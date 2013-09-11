import sys
import csv
import re
import json

# Finds the longest repeated subsequence in a sequence
# Check if each subsequence, starting at the first entry, with length
# from 1 to ceil(len/2) is repeated
# e.g.: 123456349 -> 34
# e.g.: abcdefcdgdef -> def
def longest_subsequence(seq):
    canidate = None
    longest_canidate = []

    for start_pos in range(len(seq)):
        for slice_size in range(1, int((len(seq)-start_pos)/2) + 1):
            for start_i in range(start_pos, len(seq)-slice_size, slice_size):
                canidate = seq[start_i : start_i + slice_size]
                any_contains = False
                for test_i in range(start_i + slice_size, len(seq)-start_pos+1):
                    any_contains = any_contains or (canidate == seq[test_i:test_i + slice_size])
                if not any_contains: break
                if slice_size > len(longest_canidate): longest_canidate = canidate
    return longest_canidate

            
            
# Takes a sequence, and returns non repeating hiearchies.
# In the data there are e.g.:
#   A:
#   1
#   2
#   Other A
#   B
#   C
#   D:
#   4
#   Other D
# Which I want to become
#   A:
#     1
#     2
#     Other A
#   B
#   C
#   D:
#     4
#     Other D
def build_nonrep_hierarchy(seq):
    cur_prefix = None
    ret = []
    tmp = []

    for v in seq:
        i = v['field']
        if i.find(':') > -1:
            cur_prefix = i.replace(':', '').strip()
        elif cur_prefix is not None:
            tmp.append(v)
            if i.find('Other') > -1:
                ret.append({ cur_prefix: tmp })
                cur_prefix = None
                tmp = []
        else:
            ret.append(v)

    if len(tmp) > 0:
       ret.append({ cur_prefix: tmp })
    return ret
        

# Creates hiearchies based upon repeated subsequences
# In there data there is
#   A:
#   B:
#   C
#   D
#   E:
#   B:
#   C
#   D
# Which I want to become
#   A:
#     B:
#       C
#       D
#   E:
#     B:
#       C
#       D
def create_hierarchy(seq):
    # These are fields that appear to be part of the hierarchy, but aren't
    # well, they are, but they would be root and weren't useful when I started
    # this. HOWEVER, there are some sections that have values under the totals
    # they seem to start 'Same house 1 year ago' (very exact, I know). We'll go
    # from there. It seems to happen in about 10 tables
    invalid_prefix = re.compile(r"(^\s*Total\s*:)|(^\s*Universe.*:)")

    if seq is None or not len(seq): return None
    longest_sub = longest_subsequence([i['field'] for i in seq])
    if longest_sub is None or not len(longest_sub): return build_nonrep_hierarchy(seq)
    ret = []

    sub_i = 0
    last_header = None
    for k in range(len(seq)):
        i = seq[k]['field']
        if invalid_prefix.match(i) and seq[k+1]['field'].find(':') > -1 and seq[k+1]['field'] == 'Same house 1 year ago':
            ret.append(seq[k])
        elif i == longest_sub[sub_i]:
            ret[last_header]['fields'].append(seq[k])
            sub_i = (sub_i + 1) % len(longest_sub)
        else:
            last_header = len(ret)
            ret.append(seq[k])
            ret[last_header]['fields'] = []
    
    for i in ret:
        if 'fields' in i:
            i['fields'] = create_hierarchy(i['fields'])
    return ret

filename = "Sequence_Number_and_Table_Number_Lookup.txt"


cur_table = None
stats = {}
table = []
cnt = 0
all_tables = []

with open(filename, 'r') as csvfile:
    csvfile = csv.DictReader(csvfile)
    for row in csvfile:
        cnt += 1
        # Faster if I'm just testing a specific section of the file
        #if cnt not in range(3712,3737): continue

        if row['cells'] != '':
            # Process the last table seen
            if(len(table)):
                try:
                    stats[cur_table]['fields'] = create_hierarchy(table)
                except TypeError:
                    # It pains me to do this like this:-\
                    # B07201PR specifically, and that whole section in general
                    # Is just...not standard...
                    # I was thinking there might be a way to do it by
                    # Creating as balanced a tree as possible, but maybe 
                    # In the next version
                    # Only errors on: B07201PR, B19215, B21001 so maybe it isn't so
                    # bad and can be handled by hand
                    # These tables seem to have the format
                    # A
                    # B
                    # D
                    # C
                    # E
                    # A
                    # B
                    # D
                    # C
                    # E
                    # which needs to be broken into
                    # A
                    #   B
                    #     D
                    #   C
                    #     E
                    # A
                    #   B
                    #     D
                    #   C
                    #     E
                    #
                    print("Error on table %s, placing in flat rows" % stats[cur_table]['table'], file=sys.stderr)
                    stats[cur_table]['fields'] = table


            # Initialize the new table
            cur_table = row['Long Table Title']
            stats[cur_table]  = {
                'table': row['Table ID'],
                'seq': row['seq'],
                'fields': {}
            }

            table = []
        elif row['Line Number Decimal M Lines'] != '':
            # Remove the non-essential fields
            # and give the remaining ones better names
            table.append({
                'field': row['Long Table Title'],
                'id': row['Line Number Decimal M Lines']
            
            })

# Process the last table seen
stats[cur_table]['fields'] = create_hierarchy(table)


print(json.dumps(stats))

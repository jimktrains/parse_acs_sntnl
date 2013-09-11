import sys
import csv
import re
import json

# Finds the longest repeated subsequence in a sequence
# Check if each subsequence, starting at the first entry, with length
# from 1 to ceil(len/2) is repeated
# e.g.: 123456349 -> 34
# e.g.: abcdefcdgdef -> def
# NOTE: only subsequences length 2+ are considered
def longest_subsequence(seq):
    canidate = None
    longest_canidate = []

    for start_pos in range(len(seq)):
        for slice_size in range(2, int((len(seq)-start_pos)/2) + 1):
            for start_i in range(start_pos, len(seq)-slice_size, slice_size):
                canidate = seq[start_i : start_i + slice_size]
                any_contains = False
                for test_i in range(start_i + slice_size, len(seq)-start_pos+1):
                    any_contains = any_contains or (canidate == seq[test_i:test_i + slice_size])
                if not any_contains: break
                if slice_size > len(longest_canidate): longest_canidate = canidate
    return longest_canidate

            
# These are fields that appear to be part of the hierarchy, but aren't
# well, they are, but they would be root and weren't useful when I started
# this. HOWEVER, there are some sections that have values under the totals
# they seem to start 'Same house 1 year ago' (very exact, I know). We'll go
# from there. It seems to happen in about 10 tables
invalid_prefix = re.compile(r"(^\s*Total\s*:)|(^\s*Universe.*:)")

def is_prefix(i):
    return i.find(":") > -1
            
def is_valid_prefix(seq, k, longest_sub):
    first_longest_sub = ['']
    if longest_sub is not None and len(longest_sub):
        first_longest_sub = longest_sub

    has_colon = seq[k]['field'].find(':') > -1
    invalid_match = invalid_prefix.match(seq[k]['field'])
    invalid_in_sub = (seq[k]['field'] in first_longest_sub)



    can_look_ahead = (k < (len(seq) - 1))

    invalid_unless = can_look_ahead and \
                    ( \
                        ( \
                            (seq[k+1]['field'].find(':') < 0) and \
                            seq[k+1]['field'] != 'Afghan'
                        ) or \
                        (seq[k+1]['field']  == first_longest_sub[0]) \
                    )
    if invalid_match:
        invalid_match = not invalid_unless

    invalid = invalid_match or invalid_in_sub

    #print("M", bool(invalid_match))
    #print("S", invalid_in_sub)
    #print("U", invalid_unless)
    #print("I", invalid)

    return has_colon and not invalid 

# Takes a sequence, and returns non repeating hierarchies.
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

    for k in range(len(seq)):
        v = seq[k]
        i = v['field']
        if is_prefix(i) and is_valid_prefix(seq, k, []):
            if cur_prefix is not None:
                cur_prefix['fields'] = tmp
                ret.append(cur_prefix)
            cur_prefix = v
            tmp = []
        elif cur_prefix is not None:
            tmp.append(v)
            if i.find('Other') > -1:
                cur_prefix['fields'] = tmp
                ret.append(cur_prefix)
                cur_prefix = None
                tmp = []
        else:
            ret.append(v)

    if cur_prefix is not None:
        cur_prefix['fields'] = tmp
        ret.append(cur_prefix)
    return ret
        

# Creates hierarchies based upon repeated subsequences
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

    if seq is None or not len(seq): return None
    #print("S",[i['field'] for i in seq])
    longest_sub = longest_subsequence([i['field'] for i in seq])
    #print("L",longest_sub)
    if longest_sub is None or not len(longest_sub): return build_nonrep_hierarchy(seq)
    ret = []

    sub_i = 0
    last_header = None
    for k in range(len(seq)):
        i = seq[k]['field']
        #print("++++")
        #print('k',k)
        #print('i',i)
        #print('s',sub_i)
        #print('l',longest_sub[sub_i])
        #print('h',last_header)
        #print('r',ret)
        #print(is_prefix(i))
        #print(is_valid_prefix(seq, k, longest_sub))

        if is_prefix(i):
            if is_valid_prefix(seq, k, longest_sub):
                last_header = len(ret)
                ret.append(seq[k])
                ret[last_header]['fields'] = []
            else:
                if last_header is None:
                    ret.append(seq[k])
                else:
                    ret[last_header]['fields'].append(seq[k])
                if i == longest_sub[sub_i]:
                    sub_i = (sub_i + 1) % len(longest_sub)
        else:
            if last_header is None:
                ret.append(seq[k])
            else:
                ret[last_header]['fields'].append(seq[k])
            if i == longest_sub[sub_i]:
                sub_i = (sub_i + 1) % len(longest_sub)
    
    for i in ret:
        if 'fields' in i:
            i['fields'] = create_hierarchy(i['fields'])
    return ret

filename = "Sequence_Number_and_Table_Number_Lookup.txt"


cur_table = None
cur_subj = None
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
                    # D
                    # E
                    # A
                    # B
                    # D
                    # C
                    # D
                    # E
                    # which needs to be broken into
                    # A
                    #   B
                    #     D
                    #   C
                    #     D
                    #     E
                    # A
                    #   B
                    #     D
                    #   C
                    #     D
                    #     E
                    #
                    print("Error on table %s, placing in flat rows" % stats[cur_subj][cur_table]['table'], file=sys.stderr)

                    # Removes partially processed data
                    for i in table:
                        if 'fields' in i: del i['fields']

                    stats[cur_subj][cur_table]['fields'] = table


            # Initialize the new table
            cur_table = row['Long Table Title']
            cur_subj = row['subject_area']
            if cur_subj not in stats:
                stats[cur_subj] = {}
            stats[cur_subj][cur_table]  = {
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
stats[cur_subj][cur_table]['fields'] = create_hierarchy(table)


print(json.dumps(stats))

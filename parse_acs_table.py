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
#   3
#   B
#   C
#   D:
#   4
#   5
# Which I want to become
#   A:
#     1
#     2
#     3
#   B
#   C
#   D:
#     4
#     5
def build_nonrep_hierarchy(seq):
    cur_prefix = None
    ret = []
    tmp = []

    for v in seq:
        i = v['field']
        if i.find(':') > -1:
            cur_prefix = i.replace(':', '').strip()
            tmp = []
        elif cur_prefix is not None:
            tmp.append(v)
            if i.find('Other') > -1:
                ret.append({ cur_prefix: tmp })
                cur_prefix = None
        else:
            ret.append(v)

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
    if seq is None or not len(seq): return None
    longest_sub = longest_subsequence([i['field'] for i in seq])
    if longest_sub is None or not len(longest_sub): return build_nonrep_hierarchy(seq)
    ret = []

    sub_i = 0
    last_header = None
    for k in range(len(seq)):
        i = seq[k]['field']
        if invalid_prefix.match(i):
            ret.append(seq[k])
        elif i == longest_sub[sub_i]:
            seq[last_header]['fields'].append(seq[k])
            sub_i = (sub_i + 1) % len(longest_sub)
        else:
            last_header = k
            seq[k]['fields'] = []
            ret.append(seq[k])
    
    for i in ret:
        if 'fields' in i:
            i['fields'] = create_hierarchy(i['fields'])
    return ret

filename = "Sequence_Number_and_Table_Number_Lookup.txt"

# These are fields that appear to be part of the hierarchy, but aren't
# well, they are, but they would be root and weren't useful when I started
# this
invalid_prefix = re.compile(r"(^\s*Total\s*:)|(^\s*Universe.*:)")

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
        #if cnt not in range(200): continue

        if row['cells'] != '':
            # Process the last table seen
            if(len(table)):
                stats[cur_table]['fields'] = create_hierarchy(table)

            # Initialize the new table
            cur_table = row['Long Table Title']
            stats[row['Long Table Title']]  = {
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

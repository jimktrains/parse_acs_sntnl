#!/usr/bin/env python3
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
                            seq[k+1]['field'] not in ['Afghan', 'Same house 1 year ago']
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

    def wrap_up_prefix():
        nonlocal cur_prefix
        nonlocal ret
        nonlocal tmp
        if cur_prefix is not None:
            cur_prefix['fields'] = tmp
            ret.append(cur_prefix)
        cur_prefix = None
        tmp = []
        
    for k in range(len(seq)):
        v = seq[k]
        i = v['field']
        if is_prefix(i) and is_valid_prefix(seq, k, []):
            wrap_up_prefix()
            cur_prefix = v
        elif cur_prefix is not None:
            # These come after the end of a list
            # but the end isn't signafied otherwise
            if i in ['Abroad 1 year ago']:
                wrap_up_prefix()
                ret.append(v)
            else:
                tmp.append(v)
                if i.find('Other') > -1:
                    wrap_up_prefix()
        else:
            ret.append(v)

    wrap_up_prefix()

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
    def add_row_into_appropriate_prefix(k):
        nonlocal sub_i
        if last_header is None:
            ret.append(seq[k])
        else:
            ret[last_header]['fields'].append(seq[k])
        if seq[k]['field'] == longest_sub[sub_i]:
            sub_i = (sub_i + 1) % len(longest_sub)
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
                add_row_into_appropriate_prefix(k)
        else:
            add_row_into_appropriate_prefix(k)
    
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
                    stats[cur_subj][cur_table]['fields'] = create_hierarchy(table)
                except IOError:#TypeError:
                    # Update: It doesn't error, but groups fields wrong now:-\
                    #
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
            cur_table = row['Table ID'] 
            cur_subj = row['subject_area']
            if cur_subj not in stats:
                stats[cur_subj] = {}
            stats[cur_subj][cur_table]  = {
                'name': row['Long Table Title'],
                'seq': row['seq'],
                'fields': {}
            }

            table = []
        elif row['Line Number Decimal M Lines'] != '':
            # Ignore non-data columns
            if row['Line Number Decimal M Lines'].find('.5') > -1: continue
            # Remove the non-essential fields
            # and give the remaining ones better names
            table.append({
                'field': row['Long Table Title'],
                'id': ("%s%03d" % (row['Table ID'], int(row['Line Number Decimal M Lines'])))
            })

# Process the last table seen
stats[cur_subj][cur_table]['fields'] = create_hierarchy(table)


#print(json.dumps(stats))


bad_name = re.compile(r"[^A-Za-z0-9_]+")
end_us = re.compile(r"_$")
def shorten_id(name):
    name = name.lower()
    name = name.replace('year', 'yr')
    name = name.replace('included', 'inc')
    name = name.replace('includ', 'inc')
    name = name.replace('status', 'stat')
    name = name.replace('first', '1st')
    name = name.replace('second', '2nd')
    name = name.replace('third', '3rd')
    name = name.replace('fourth', '4th')
    name = name.replace('number', 'num')
    name = name.replace('occupied', 'occ')
    name = name.replace('_the_', '_')
    name = name.replace('_in_', '_')
    name = name.replace('_for_', '_')
    name = name.replace('_of_', '_')
    name = name.replace('month', 'mon')
    name = name.replace('aggregate', 'agg')
    name = name.replace('facility', 'fac')
    name = name.replace('facilities', 'fac')
    name = name.replace('geographical', 'geo')
    name = name.replace('transportation', 'trans')
    name = name.replace('people', 'ppl')
    name = name.replace('living', 'liv')
    name = name.replace('household', 'hh')
    name = name.replace('population', 'pop')
    name = name.replace('graduate', 'grad')
    name = name.replace('professional', 'prof')
    name = name.replace('_and_over', '_n_up')
    name = name.replace('_and_under', '_n_un')
    name = name.replace('_grade_', '_gr')
    name = name.replace('poverty', 'pov')
    name = name.replace('level', 'lvl')
    name = name.replace('pov_lvl', 'povlvl')
    name = name.replace('_past_', '_p')
    name = name.replace('undergraduate', 'ugrad')
    name = name.replace('female_', 'f_')
    name = name.replace('male_', 'm_')
    name = name.replace('_by_', '_')
    name = name.replace('private', 'priv')
    name = name.replace('public', 'pub')
    name = name.replace('_or_more', '_plus')
    name = name.replace('_at_', '_')
    name = name.replace('adjusted', 'adj')
    name = name.replace('inflation', 'infl')
    name = name.replace('dollars', 'usd')
    name = name.replace('educational', 'edu')
    name = name.replace('attainment', 'att')
    name = name.replace('employment', 'empl')
    name = name.replace('enrolled', 'enroll')
    name = name.replace('detail', 'dtl')
    name = name.replace('income', 'incm')
    name = name.replace('above', 'abv')
    name = name.replace('social_security', 'ss')
    name = name.replace('_with_', '_w_')
    name = name.replace('_without_', '_wo_')
    name = name.replace('_and_or_', '_ao_')
    name = name.replace('assistance', 'asst' )
    name = name.replace('grandchildren', 'gchildren' )
    name = name.replace('responsible', 'respbl' )
    name = name.replace('naturalized', 'nat')
    name = name.replace('english', 'eng')
    name = name.replace('citizen', 'citn')
    name = name.replace('_u_s_', '_us_')
    name = name.replace('speak', 'spk')
    name = name.replace('_very_well', '_vwell')
    name = name.replace('languages', 'lang')
    name = name.replace('language', 'lang')
    name = name.replace('european', 'euro')
    name = name.replace('full_time', 'ftime')
    name = name.replace('earnings', 'earn')
    name = name.replace('worked', 'wrk')
    name = name.replace('husband', 'husb')
    name = name.replace('present', 'pres')
    name = name.replace('_less_than_', '_lt_')
    name = name.replace('_more_than_', '_mt_')
    name = name.replace('island', 'isl')
    name = name.replace('_and_', '_n_')
    name = name.replace('foreign', 'forn')
    name = name.replace('associate', 'assoc')
    name = name.replace('college', 'colg')
    name = name.replace('nativity', 'nat')
    name = name.replace('spoken', 'spkn')
    name = name.replace('ability', 'ablt')
    name = name.replace('residence', 'resdc')
    name = name.replace('united_states', 'us')
    name = name.replace('related', 'rel')
    name = name.replace('_under_18_', '_u18_')
    name = name.replace('_over_18_', '_o18_')
    name = name.replace('received', 'recv')
    name = name.replace('food_stamps', 'fdstmp')
    name = name.replace('60_yrs_or_over', 'o60yro')
    name = name.replace('hispanic', 'hisp')
    name = name.replace('white', 'wht')
    name = name.replace('black', 'blk')
    name = name.replace('percent', 'pct')
    name = name.replace('different', 'diff')
    name = name.replace('within', 'wi')
    name = name.replace('african_american', 'afam')
    name = name.replace('moved', 'mvd')
    name = name.replace('separated', 'sep')
    return name
def fix_name(name):
    name = name.replace(':', '')
    name = bad_name.sub('_', name)
    name = end_us.sub('', name)
    name = shorten_id(name)
    if re.match("^\d.+", name):
        name = "X" + name
    return name

def make_field_list(table, prefix = None):
    if 'fields' in table:
        fields = []
        if prefix is None:
            if 'field' in table:
                prefix = table['field']
        else:
            prefix = prefix  + '.'  + table['field']
        if prefix is not None:
            prefix = fix_name(prefix)

        if table['fields'] is None:
            return []

        for field in table['fields']:
            fields += make_field_list(field, prefix)
        return fields
    else:
        field = table['id']
        if prefix is None:
            prefix = table['field']
        else:
            prefix = prefix  + '.'  + table['field']
        prefix = fix_name(prefix)
        return [ ( field, prefix ) ] 


for col in stats:
    for table in stats[col]:
        schema = "acs2012_5yr"
        name = fix_name(stats[col][table]['name'])
        print("CREATE OR REPLACE VIEW %s.%s AS " % (schema, name))
        print(" SELECT stusab, logrecno, ")
        print("        state as statefp, county as countyfp, cousub as cousubfp, tract as tractce, blkgrp as blkgrpce, ")
        print("        concat(state, county) as county_geoid, ")
        print("        concat(state, county, cousub) as cousub_geoid, ")
        print("        concat(state, county, tract) as tract_geoid, ")
        print("        concat(state, county, tract, blkgrp) as blkgrp_geoid, ")
        for i in make_field_list(stats[col][table]):
            print("        %s AS %s," % i )
        print("        1 AS one ")
        print(" FROM %s.%s INNER JOIN %s.geoheader USING (geoid);" % (schema, table, schema))
        print("COMMENT ON VIEW %s.%s IS 'From %s';" % (schema, name, table))
        
        print("CREATE OR REPLACE VIEW %s.%s_moe AS " % (schema, name))
        print(" SELECT stusab, logrecno, ")
        print("        state as statefp, county as countyfp, cousub as cousubfp, tract as tractce, blkgrp as blkgrpce, ")
        print("        concat(state, county) as county_geoid, ")
        print("        concat(state, county, cousub) as cousub_geoid, ")
        print("        concat(state, county, tract) as tract_geoid, ")
        print("        concat(state, county, tract, blkgrp) as blkgrp_geoid, ")
        for i in make_field_list(stats[col][table]):
            print("        %s AS %s," % i )
            print("        %s_moe AS moe_%s," % i )
        print("        1 AS one ")
        print(" FROM %s.%s_moe INNER JOIN %s.geoheader USING (geoid);" % (schema, table,schema))
        print("COMMENT ON VIEW %s.%s_moe IS 'From %s_moe';" % (schema, name, table))

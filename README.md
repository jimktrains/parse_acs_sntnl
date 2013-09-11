parse_acs_sntnl
===============

Parses the Sequence Number and Table Number Lookup Table (ftp://ftp.census.gov/acs2010_5yr/summaryfile/Sequence_Number_and_Table_Number_Lookup.txt)

The issue with this file is that the fields are given flat (one per row, with no indication of the hierarchy), but the
fields are hierarchical. e.g.:

    "ACSSF","B05003B","0009",,"80","23 CELLS",,"SEX BY AGE BY NATIVITY AND CITIZENSHIP STATUS (BLACK OR AFRICAN AMERICAN ALONE)",              "Foreign Birth"
    "ACSSF","B05003B","0009",,,,,"Universe:  Black or African American alone",
    "ACSSF","B05003B","0009","1",,,,"Total:",
    "ACSSF","B05003B","0009","2",,,,"Male:",
    "ACSSF","B05003B","0009","3",,,,"Under 18 years:",
    "ACSSF","B05003B","0009","4",,,,"Native",
    "ACSSF","B05003B","0009","5",,,,"Foreign born:",
    "ACSSF","B05003B","0009","6",,,,"Naturalized U.S. citizen",
    "ACSSF","B05003B","0009","7",,,,"Not a U.S. citizen",
    "ACSSF","B05003B","0009","8",,,,"18 years and over:",
    "ACSSF","B05003B","0009","9",,,,"Native",
    "ACSSF","B05003B","0009","10",,,,"Foreign born:",
    "ACSSF","B05003B","0009","11",,,,"Naturalized U.S. citizen",
    "ACSSF","B05003B","0009","12",,,,"Not a U.S. citizen",
    "ACSSF","B05003B","0009","13",,,,"Female:",
    "ACSSF","B05003B","0009","14",,,,"Under 18 years:",
    "ACSSF","B05003B","0009","15",,,,"Native",
    "ACSSF","B05003B","0009","16",,,,"Foreign born:",
    "ACSSF","B05003B","0009","17",,,,"Naturalized U.S. citizen",
    "ACSSF","B05003B","0009","18",,,,"Not a U.S. citizen",
    "ACSSF","B05003B","0009","19",,,,"18 years and over:",
    "ACSSF","B05003B","0009","20",,,,"Native",
    "ACSSF","B05003B","0009","21",,,,"Foreign born:",
    "ACSSF","B05003B","0009","22",,,,"Naturalized U.S. citizen",
    "ACSSF","B05003B","0009","23",,,,"Not a U.S. citizen",

should be converted into a structure like:

    Total:
        Male:
            Under 18 years:
                Native
                Foreign born:
                    Naturalized U.S. citizen
                    Not a U.S. citizen
            18 years and over:
                Native
                Foreign born:
                    Naturalized U.S. citizen
                    Not a U.S. citizen
        Female:
            Under 18 years:
                Native
                Foreign born:
                    Naturalized U.S. citizen
                    Not a U.S. citizen
            18 years and over:
                Native
                Foreign born:
                    Naturalized U.S. citizen
                    Not a U.S. citizen

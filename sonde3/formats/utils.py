import warnings
import numpy as np

def match_param(DF,DEFINITIONS):
    """
    Method tries to match the columns of a dataframe to the definitions file sonde3/data/definitions.csv

    If the column cannot be matched a warnings.warn is passed.

    """
    fixed_columns = []
    for col in DF.columns:
        if 'Datetime_(UTC)' in col:
            fixed_columns.append(col)
            continue

        if  not isinstance(col, tuple) :
            col = col.split()
        else:
            col = list(col)

        submatch = DEFINITIONS[DEFINITIONS['parameter'].str.contains(col[0])]

        if len(col) > 2:
            #print ("col length > 2")
            #print (col, "our submatch: ", submatch)
            match = submatch[submatch['unit'].str.contains(col[2], regex=False)]
            #print ("our match: ", match)
            if not match.empty:
                col = (str(match.iloc[0]['standard']))

        elif len(col) > 1:
            #print ("col length > 1")
            #rint (col, "our submatch: ", submatch)
            if "Unnamed" not in col[1]:  #check for a null value in the units column
                match = submatch[submatch['unit'].str.contains(col[1], regex=False)]
                #print ("our match: ", match)
            else:
                col = (str(submatch.iloc[0]['standard']))

            if not match.empty:
                col = (str(match.iloc[0]['standard']))

        elif len(col) == 1:
            #print ("col length  == 1")
            #print (col, "our submatch: ", submatch)
            match = submatch[submatch['unit'].str.contains(col[0], regex=False)]
            #print ("length of col", len(col), "col: ", col, "match: ", match, "submatch: ", submatch)
            if not match.empty:
                col = (str(match.iloc[0]['standard']))
        else:

            warnings.warn("Could not match parameter <%s> to definition file" %str(col) , stacklevel=2)
            # convert list to single string to avoid errors in later handling the pandas columns
            col = ''.join(str(e)+' ' for e in col)
            # this introduces a trailing whitespace if col[1] is none

        col = ''.join(str(e)+'' for e in col)
        fixed_columns.append(col.rstrip()) # remove any trailing whitespace if exists
    DF.columns = fixed_columns
    DF.reindex(columns = fixed_columns)
    return DF

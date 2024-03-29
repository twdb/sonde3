import pandas as pd
from datetime import datetime
import pytz
import os
import io, itertools
import csv
import warnings
import six
import pytz
from .utils import match_param


def read_ysi_exo_csv(ysi_file,delim=None):
    """
    Method reads a text based YSI sonde instrument file in KOR EXO format and returns a pandas DataFrame for the table and metadata.

    Method makes many assumptions about the standard formatting of the text file.
    Method assumes the file is of YSI origin, has at least two columns.

    A separator must be passed to the function as the deliminator YSI uses
    can be different.  (Somtimes tab separated, comma, or a series of spaces)

    The function assumes that ['date','time','fractime'] are in column 0 and 1 and 2.
    """
    package_directory = os.path.dirname(os.path.abspath(__file__))
    DEFINITIONS = pd.read_csv(os.path.join(package_directory,'..',"data/definitions.csv"), encoding='cp1252')

    utc=pytz.utc

    #localtime = pytz.timezone('US/Central')

    
    ysi_file.seek(0)
    
    #grab 30 lines discover what the real header is, then trim the file
    ysi_file.seek(0)
    ysi_file = ysi_file.read().decode('ISO-8859-1')
    
    
    raw_metadata = pd.read_csv(io.StringIO(ysi_file), engine='python',na_values=['','na'],header=None, nrows=30,encoding = "ISO-8859-1" )
    header_row_index = raw_metadata.loc[raw_metadata[0].str.contains("Date")==True].index[0]
    raw_metadata = raw_metadata.drop(raw_metadata.index[(header_row_index-2):])
    #print(header_row_index, raw_metadata)
   
    
    
    #grab main file from header point, squash datetime row
    DF = pd.read_csv(io.StringIO(ysi_file), engine='python', parse_dates={'Datetime_(UTC)': [0,1]}, sep=delim,na_values=['','na'], header = header_row_index, encoding = "ISO-8859-1")
    DF = DF.drop(DF.index[:header_row_index])
    DF = DF.drop('Time (Fract. Sec)',1)
    #DF['Datetime_(UTC)'] = DF['Datetime_(UTC)'].values.astype('datetime64[s]')

    metadata = pd.DataFrame(columns=('Manufacturer', 'Instrument_Serial_Number', 'Sensor_Serial_Numbers', 'Model','Station','Deployment_Setup_Time', \
                                     'Deployment_Start_Time', 'Deployment_Stop_Time','Filename','User','Averaging','Firmware', 'Sensor_Firmware'))



    if "UTC" not in raw_metadata.iloc[9][1]:
        DF.insert(0,'Datetime_(native)' ,  DF['Datetime_(UTC)'])
        DF = DF.drop('Datetime_(UTC)', 1)

    elif ("CST" in raw_metadata.iloc[9][1]) or ("CDT" in raw_metadata.iloc[9][1]):
        localtime = pytz.timezone('US/Central')
        DF.insert(0,'Datetime_(UTC)' ,  DF['Datetime_(Native)'].map(lambda x: localtime.localize(x).astimezone(utc)))
        DF = DF.drop('Datetime_(Native)', 1)


    metadata = metadata.append([{'Model' : 'EXO'}])
    metadata.at[0, 'Manufacturer']= 'YSI'
    metadata.at[0, 'Instrument_Serial_Number']= raw_metadata.iloc[4][1].replace('Sonde ', '')
    metadata.at[0, 'Station' ]=raw_metadata.iloc[6][1]
    metadata.at[0, 'User']=raw_metadata.iloc[5][1]
    metadata.at[0, 'Averaging']=raw_metadata.iloc[8][1]
    metadata.at[0, 'Firmware' ]=raw_metadata.iloc[16][2]
    #head, tail = ntpath.split(ysi_file)
    #metadata = metadata.iat([0], 'Filename' , tail)
    metadata['Deployment_Start_Time'] = DF['Datetime_(UTC)'].iloc[0]
    metadata['Deployment_Stop_Time'] = DF['Datetime_(UTC)'].iloc[-1]
    sensors = raw_metadata.iloc[15:, 0:3]
    metadata.at[0, 'Sensor_Serial_Numbers']=sensors[1].str.cat(sep=';')
    metadata.at[0, 'Sensor_Firmware']=  sensors[2].str.cat(sep=';')

    DF = DF.drop(['Site Name'], axis=1)

    new_cols = []
    
    for col in DF.columns:
        new_cols.append( ''.join(i for i in col if ord(i)<128))

    DF.columns = new_cols
    
    DF = match_param(DF,DEFINITIONS)


    #now convert all data rows to floats...
    #move this to separate function if I have to do this more than for hydrotechs
    floater = lambda x: float(x)

    #split set
    dt_column = DF.iloc[:,0]
    data = DF.iloc[:,1:]
    data = data.applymap(floater)


    DF = pd.concat([dt_column,data], axis=1)

    return metadata, DF



def read_ysi_exo_backup(ysi_file,delim=None,tzinfo=None):
    """
    Method reads a text based YSI sonde instrument file in KOR EXO Backup format and returns a pandas DataFrame for the table and metadata.

    Method makes many assumptions about the standard formatting of the text file.
    Method assumes the file is of YSI origin, and only has a single column header

    A separator must be passed to the function as the deliminator YSI uses
    can be different.  (Somtimes tab separated, comma, or a series of spaces)

    The function assumes that ['date','time'] are in column 0 and 1.
    """
    package_directory = os.path.dirname(os.path.abspath(__file__))
    DEFINITIONS = pd.read_csv(os.path.join(package_directory,'..',"data/definitions.csv"), encoding='cp1252')
    utc=pytz.utc

    
    ysi_file.seek(0)

    #ysi_file = ysi_file.read().decode('utf-8')

    #for line in ysi_file:
    #    line.replace('\0','')

    #grab main file from header point, squash datetime row
    DF = pd.read_csv(ysi_file, parse_dates={'Datetime_(Native)': [0,1]}, sep=',',na_values=['','na'], header = [0], encoding='unicode_escape')
    #DF = DF.drop(DF.index[:header_row_index])
    #DF = DF.drop('Time (Fract. Sec)',1)
        #DF['Datetime_(UTC)'] = DF['Datetime_(UTC)'].values.astype('datetime64[s]')

    metadata = pd.DataFrame(columns=('Manufacturer', 'Instrument_Serial_Number', 'Sensor_Serial_Numbers', 'Model','Station','Deployment_Setup_Time', \
                                     'Deployment_Start_Time', 'Deployment_Stop_Time','Filename','User','Averaging','Firmware', 'Sensor_Firmware'))
    metadata = metadata.append([{'Model' : 'EXO'}])
    
    utc=pytz.utc
    if tzinfo:
        localtime = tzinfo
    else:
        localtime = pytz.timezone('US/Central')

        #warnings.warn("Info: No time zone was set for file, assuming records are recorded in CST" , stacklevel=2)
    DF.insert(0,'Datetime_(UTC)' ,  DF['Datetime_(Native)'].map(lambda x: localtime.localize(x).astimezone(utc)))
    DF = DF.drop('Datetime_(Native)', 1)

    # stripping out all of the funky non-ascii characters out of the file so we can match properly
    # otherwise EXO degree mark will break the match algorithm
    new_cols = []
    for col in DF.columns:
        new_cols.append( ''.join(i for i in col if ord(i)<128))

    DF.columns = new_cols

    if 'Site' in DF:
        DF = DF.drop(columns=['Site'])
    if 'User ID' in DF:
        DF = DF.drop(columns=['User ID'])
    if 'Unit ID' in DF:
        DF = DF.drop(columns=['Unit ID'])

    DF = match_param(DF,DEFINITIONS)



    #now convert all data rows to floats...
    #move this to separate function if I have to do this more than for hydrotechs
    floater = lambda x: float(x)

    #split set
    dt_column = DF.iloc[:,0]
    data = DF.iloc[:,1:]
    data = data.applymap(floater)


    DF = pd.concat([dt_column,data], axis=1)


    return metadata, DF

import pandas as pd
import subprocess as sub

def find_files(search_directory, pattern):
    #construct the find command
    command = ['find', f'{search_directory}', '-type', 'f', '-name', f'{pattern}']
    #run the subprocess and capture the output as text instead of bytes
    result = sub.run(command, capture_output=True, text=True)
    #split the standard output by newline to create a list of filepaths to return
    paths = result.stdout.splitlines()
    return paths

#read in dataframe
def read_dataframe(dataframe_filepath):
    '''this fuction reads in a dataframe'''
    df = pd.read_csv(dataframe_filepath, sep = '\t')
    return df

def filter_df(df, column_name, keep_values):
    ''' this function filters a dataframe and keeps rows which match specified values in the specified column '''
    return df[df[column_name].astype(str).isin(keep_values)]

#write dataframe of variants to investigate out
def write_dataframe_to_tsv(dataframe_to_write, write_to):
    '''this function takes an input dataframe and writes it to a tsv file with the specified name'''
    dataframe_to_write.to_csv(write_to, index = False, sep = '\t')

working_directory = '/path/to/project_results'


#find all dataframes that end in '_checked_dataframe.tsv'
list_of_files = find_files(search_directory = working_directory, pattern = '*_checked_dataframe.tsv')
#create a list for all dfs
all_dfs = []
#for every file in the list
for i in list_of_files:
    #split the file path on '/'
    filename = str.split(i,'/')[-1]
    #get the caller name from the file name
    caller = str.split(filename,'_')[0]
    #read in dataframe
    df = read_dataframe(i)
    #make a copy of the dataframe to make edits to
    df_copy = df.copy()
    #filter dataframe to include only rows which have 'not_in_giab' or 'investigate' in the status column
    filtered_df = filter_df(df = df_copy, column_name='status', keep_values=['not_in_giab', 'investigate'])
    #add the callername to the dataframe in the first column
    filtered_df.insert(0, 'caller', caller)
    #add the caller_df to the list of all dataframes
    all_dfs.append(filtered_df)

#combine all dataframes to form 1 big dataframe of things to investigate
combined_df = pd.concat(all_dfs, ignore_index=True)


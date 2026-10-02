import pandas as pd
import subprocess as sub

def find_input_files(search_directory, pattern):
    #construct the find command
    command = ['find', f'{search_directory}', '-type', 'f', '-name', f'{pattern}']
    #run the subprocess and capture the output as text instead of bytes
    result = sub.run(command, capture_output=True, text=True)
    #split the standard output by newline to create a list of filepaths to return
    paths = result.stdout.splitlines()
    return paths

def get_caller_name_from_filepath(filepath):
    '''this function will work to get the variant caller name from a filepath if formatted /path/to/directory/callername_extension'''
    #split the entire filepath on the '/'
    split_filepath = filepath.split('/')
    #split the final element on the '_' and get the first element
    caller_name = (split_filepath[-1].split('_')[0])
    return caller_name

def csv_to_pd(input_csv):
    #read in csv to pandas dataframe
    dataframe = pd.read_csv(input_csv)
    return (dataframe)

search_directory = '/path/to/directory/with/happy/results'
pattern = '*.output.summary.csv'

#create an empty list of csvs
list_of_csvs = find_input_files(search_directory, pattern)

#create a list of dictionaries of variant callers and file_paths 
callers= []
for i in list_of_csvs:
    #get the variant caller name from the filepath
    caller_name = get_caller_name_from_filepath(filepath=i)
    #create a dictionary to store variant callers and filepaths to happy results
    caller_dict = {'caller_name': caller_name, 'happy_results_filepath': i}
    #append the dictionary to the callers list
    callers.append(caller_dict)

#iterate through list of dictionaries
for item in callers:
    #get the caller
    caller = item['caller_name']
    #get the caller's happy results filepath
    input_csv = item['happy_results_filepath']
    #read csv into a dataframe
    results_dataframe = csv_to_pd(input_csv)
    #add a column to the dataframe to add the caller name 
    results_dataframe['caller'] = caller
    #transpose dataframe so that metrics become columns 
    transposed_resuts_dataframe = results_dataframe.T
    #add the dataframe to the caller's dictionary
    item['dataframe'] = transposed_resuts_dataframe

#combine all dataframes 
#create a list to put dataframes in
dataframes = []
#iterate through the list of dictionaries
for dictionary in callers:
    #get the dataframes from each dictionary
    df = dictionary['dataframe']
    #add to the list of dataframes 
    dataframes.append(df)

#combine the dataframes. Combine by columns
combined_dataframe = pd.concat(dataframes,axis=1)

#reorder to move 0s next to eachother, 1s next to eachother, 2s next to eachother
reordered_df = combined_dataframe.sort_index(axis=1)

#move the caller row so that it is the top row
#get the caller row
top = reordered_df.loc[["caller"]]
#get the rest of the rows without caller
rest = reordered_df.drop("caller")
#put the dataframe back together in the right order
final_df = pd.concat([top, rest])

final_df.to_csv(f'{search_directory}/reordered_happy_results.csv', index = True)





    




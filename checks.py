import pandas as pd
import numpy as np
import subprocess 

def read_in_dataframe(filepath, separator):
    df = pd.read_csv(filepath, sep = separator)
    return df

def read_vcf_into_dataframe(filepath):
    '''this function takes an input vcf and reads it in as a dataframe. The vcf header is removed'''
    #read in vcf file ignoring any header lines
    separator = '\t' 
    #count the number of lines that do not start with '##' (header)
    number_to_skip = subprocess.run(f"grep '^##' {filepath} | wc -l ", capture_output=True, text=True, shell=True).stdout.strip()
    number = int(number_to_skip)
    #read the file into a pandas dataframe remover the number of lines that are the header
    df = pd.read_csv(filepath, sep = separator, skiprows=number)
    return df

def create_data_dictionary(dataframe_of_files):
    #transpose dataframe so that the indexes become my keys
    transposed_df = dataframe_of_files.transpose()
    #convert dataframe to a nested dictionary
    dictionary = transposed_df.to_dict()
    #loop through each File in the inner dictionary
    for key, value in dictionary.items():  
        path = value['File']
        #if the file path ends with .vcf 
        if path.endswith('.vcf'):
            #call the read_vcf_into_dataframe function to read it into a dataframe
            df = read_vcf_into_dataframe(filepath = path)
            #add the Dataframe to the inner dictionary
            dictionary[key]['Dataframe'] = df
        #if path ends with .tsv
        elif path.endswith('.tsv'):
        #use the read_in_dataframe function to read it into a dataframe
            df = read_in_dataframe(filepath = path, separator = '\t')
            dictionary[key]['Dataframe'] = df
        else:
            print('something went wrong')
    return dictionary
        
def total_count (input_dataframe):
    number_of_rows = len(input_dataframe)
    return number_of_rows

def create_count_dictionary (dictionary):
    #create an empty dictionary to store the counts in 
    count_dict = {}
    #iterate through each key and value in the dictionary
    for key, value in dictionary.items():
            #get the dataframe using the dataframe key
            df = value['Dataframe']
            #apply the total count to get the number of rows
            number_of_rows = total_count(input_dataframe = df)
            #store the counts in an inner dictionary for total counts, within an outer dictionary that has the same keys as the data dictionary
            count_dict[key] = {'total_variants': number_of_rows}
    return count_dict

#NEED TO CHANGE THIS
def compare_column_values(df1, df2, in_or_not_in, column_to_compare):
    #get the specific column from the df1 and turn that into an array. Make sure that each array is string type
    array1 = np.array(df1[f'{column_to_compare}']).astype(str)
    #get the same column from df2 and turn that into an array. Make sure that each array is string type
    array2 = np.array(df2[f'{column_to_compare}']).astype(str)
    #if checking whether array1 values are not in array2
    if in_or_not_in == 'not_in':
        #see whether array1 values are not in array2. Return True for those not in array2
        not_in_array2 = np.isin(array1, array2, invert = True)
        #return the indices where the condition is True. True means not in array2
        indices = np.where(not_in_array2)[0]
        #get a list of the actual values in array1 that that aren't in array2
        values = array1[indices].tolist()
    #if checking whether array1 values are in array2
    elif in_or_not_in == 'in':
        #see whether array1 values are in array2. Return True for those in array2.
        in_array2 = np.isin(array1, array2)
        #return the indices where the condition is True. True means in array2
        indices = np.where(in_array2)[0]
        #get the actual values in df1 that that are in array2
        values = array1[indices].tolist()
    else:
        values = print('something went wrong')
    return values


#read in the csv file list of the files to create a dictionary out of
files_df = read_in_dataframe(filepath = '/data/home/marym/research_project/deep_variant/deepvariant_files.csv', separator = ',')
#rename the indexes in the dataframe. These will be the keys in my dictionary with each key relating to each file. MUST BE IN THE SAME ORDER AS THE FILES
files_df.index = [
    "caller_vcf",
    "vcf_with_ids",
    "results_df", #pass only
    "happy_vcf",
    "happy_exploded_df",
    "merged_df",
]
#create the data dictionary containing filepath, description of file and file read into a dataframe
data_dictionary = create_data_dictionary(dataframe_of_files = files_df)
#create the count dictionary
count_dictionary = create_count_dictionary(dictionary = data_dictionary) 

#######NEED TO CHANGE THIS TO GET THINGS FROM THE DICTIONARY       
#df2 = read_in_dataframe(filepath ='/data/home/marym/research_project/info_dataframes/deepvariant_exploded_happy_dataframe.tsv')
#check what IDs in the results dataframe are not in the happy_exploded_dataframe. Returns values not in the happy exploded dataframe.
# result = compare_column_values(
#     df1 = pass_only,
#     df2 = df2,
#     in_or_not_in = 'not_in', #must be set to 'in' or 'not_in'
#     column_to_compare = 'my_id')



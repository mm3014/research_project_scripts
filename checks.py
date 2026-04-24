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
        path = value.get('File', None)
        #if the file path ends with .vcf 
        if path.endswith('.vcf'):
            #call the read_vcf_into_dataframe function to read it into a dataframe
            df = read_vcf_into_dataframe(filepath = path)
            #make the key if it doesn't exist and add the Dataframe to the inner dictionary
            dictionary.setdefault(key, {}).update({'Dataframe': df})
        #if path ends with .tsv
        elif path.endswith('.tsv'):
        #use the read_in_dataframe function to read it into a dataframe
            df = read_in_dataframe(filepath = path, separator = '\t')
            dictionary.setdefault(key, {}).update({'Dataframe': df})
        else:
            print('something went wrong')
    return dictionary

def fetch_relevant_dataframe(dictionary, key):
    #get the dataframe from the dictionary using the specified key
    df = dictionary.get(key, {}).get('Dataframe', None)
    return df

def get_df_column(dictionary, key, column_name):
    #get the relevant dataframe from the dicitonary
    df_to_search = fetch_relevant_dataframe(dictionary, key)
    #get the relevant column from the dataframe
    column = df_to_search.loc[:, column_name]
    return column

#NEED TO CHANGE THIS
def compare_column_values(dictionary, key1, key2, column1, column2, in_or_not_in): 
    #get column1 from the dataframe
    series1 = get_df_column(dictionary, key=key1, column_name=column1).astype(str)
    #get column2 from the dataframe
    series2 = get_df_column(dictionary, key=key2, column_name=column2).astype(str)
    #if in_or_not_in is set to 'not_in'
    if in_or_not_in == 'not_in':
        #get a boolean mask. True means the value in series 1 is not in series 2
        mask = ~series1.isin(series2)
    #if in_or_not_in is set to 'in'    
    elif in_or_not_in == 'in':
        #get a boolean mask. True means the value is series 1 is in series 2
        mask = series1.isin(series2)
    else:
        raise ValueError("in_or_not_in must be 'in' or 'not_in'")
    values = series1[mask]
    return values

def count_rows (input_dataframe, to_count):
    #count the length of the dataframe
    number_of_rows = len(input_dataframe)
    return number_of_rows

def create_count_dictionary (dictionary):
    #create an empty dictionary to store the counts in 
    count_dict = {}
    #iterate through each key and value in the dictionary
    for key, value in dictionary.items():
            #get the dataframe using the dataframe key
            df = value.get('Dataframe', None)
            #apply the total count to get the number of rows
            number_of_rows = number_of_rows = len(df)
            #store the counts in an inner dictionary for total counts, within an outer dictionary that has the same keys as the data dictionary. Key is created if it doesn't exist.
            count_dict.setdefault(key, {}).update({'total_variants': number_of_rows})
    return count_dict

#read in the csv file list of the files to create a dictionary out of
files_df = read_in_dataframe(filepath = '/pathto/deepvariant_files.csv', separator = ',')
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

#CHECK FOR IDS THAT ARE IN THE RESULTS THAT ARE NOT IN HAPPY
#get my_id values in results_df not in happy_exploded_df. in_or_not_in must be 'in' or 'not_in'. We want this to be 0 to show that all variants in my vcf have been accounted for.
myid_not_in_happy = compare_column_values(dictionary = data_dictionary, key1 = 'results_df' , key2 = 'happy_exploded_df', column1 = 'my_id', column2 = 'my_id', in_or_not_in = 'not_in')
#get the results dataframe 
results_df = fetch_relevant_dataframe(dictionary = data_dictionary, key = 'results_df')
#get records from the results dataframe that were not in happy
filtered_df_res = results_df.loc[myid_not_in_happy.index]

#CHECK FOR IDS THAT ARE IN HAPPY AND NOT IN THE RESULTS
#get my_ids in happy that are not in res
not_in_res = compare_column_values(dictionary = data_dictionary, key1 = 'happy_exploded_df' , key2 = 'results_df', column1 = 'my_id', column2 = 'my_id', in_or_not_in = 'not_in')
#get happy dataframe
happy_df = fetch_relevant_dataframe(dictionary = data_dictionary, key = 'happy_exploded_df')
#get records from happy dataframe not in results
filtered_df_hap = happy_df.loc[not_in_res.index]
#check the unique values in this dataframe's TRUTH_BD column
unique_values = filtered_df_hap['TRUTH_BD'].value_counts()
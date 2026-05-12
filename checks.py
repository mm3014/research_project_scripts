import pandas as pd
import numpy as np
import subprocess
import argparse
import csv

#CREATE ARGUMENT PARSER
parser = argparse.ArgumentParser(
    prog='DataframeChecks')

def name_path_pair(arg):
    '''Convert caller name:path from '--input' argument into ('name', 'path'). This is needed to make sure the input is in the correct format'''
    if ':' not in arg:
        raise argparse.ArgumentTypeError("Input must be in name:path format")
    name = arg.split(':', 1)[0]
    path = arg.split(':', 1)[1]
    return name, path

parser.add_argument('--files_list',type=name_path_pair, action='append', help='input the variant caller name and the filepath to file list (csv) in name:path format')
parser.add_argument('--working_dir', default='./',type=str, help= 'directory to output dataframe files to')
args = parser.parse_args()

def read_in_dataframe(filepath, separator, header):
    df = pd.read_csv(filepath, sep = separator, header = header)
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
            df = read_in_dataframe(filepath = path, separator = '\t', header = 0)
            dictionary.setdefault(key, {}).update({'Dataframe': df})
        #if path ends with .bed
        elif path.endswith('.bed'):
        #use the read_in_dataframe function to read it into a dataframe
            df = read_in_dataframe(filepath = path, separator = '\t', header = None)
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

#NOT CURRENTLY BEING USED
#def compare_column_values(dictionary, key1, key2, column1, column2, in_or_not_in): 
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

def write_dataframe_to_tsv(dataframe_to_write, write_to, header):
    '''this function takes an input dataframe and writes it to a tsv file with the specified name'''
    dataframe_to_write.to_csv(write_to, index = False, header = header, sep = '\t')

def make_bed (dataframe, output_directory):
    #get the records only in happy 
    filtered_left = dataframe.loc[dataframe['_merge'] == 'left_only']
    #make a copy of the dataframe with the chromosome and position column
    bed_subset = filtered_left[['#CHROM_res', 'POS_res']].copy()
    #convert to integer to drop the .0 decimal 
    bed_subset['POS_res'] = (bed_subset['POS_res'].round(0).astype(int))
    #make a copy of the POS_res column to act as the end position column needed for a bed file
    bed_subset['POS_res_copy'] = bed_subset['POS_res'].copy()
    #make a column at the end of the dataframe to store the index. This will be needed to update the merged dataframe with the bedtools intersect results later on
    bed_subset["index_number"] = bed_subset.index
    #construct the output filepath
    output_file_path = f'{output_directory}/not_in_happy.bed'
    print(f'writing bed to {output_file_path}')
    #write out the bed file
    write_dataframe_to_tsv(dataframe_to_write = bed_subset, write_to = output_file_path, header = 0)
    return output_file_path

def run_intersect(filepath_sample, filepath_bed, output_directory, bedtools_flag):
    #onstuct the output filepath
    output_filepath = f'{output_directory}/intersect_result.bed'
    #construct the command
    command = [
        #call tool
        'bedtools',
        'intersect', 
        #provide sample to check
        '-a',
        f'{filepath_sample}',
        #provide bed file to check against
        '-b',
        f'{filepath_bed}',
        #add any other tools
        f'{bedtools_flag}']
    #run command write file
    with open(output_filepath, "w") as out:
        result = subprocess.run(command,stdout=out,check=True)
    #check whether the subprocess ran and print message accordingly
    if result.returncode == 0:
        message = f'Writing intersect output to {output_filepath}'
    else:
        message = 'bedtools intersect failed'
    return message, output_filepath

################ MAIN ########################

#get the filepath and the caller name
for element in args.files_list:
    caller_name = element[0]
    path_to_files = element[1]

working_directory = args.working_dir

#read in the csv file list of the files to create a dictionary out of
files_df = read_in_dataframe(filepath = f'{path_to_files}', separator = ',', header = 0)
#rename the indexes in the dataframe. These will be the keys in my dictionary with each key relating to each file. MUST BE IN THE SAME ORDER AS THE FILES
files_df.index = [
    "caller_output",
    "vcf_with_ids",
    "results_df", #pass only
    "happy_vcf",
    "happy_exploded_df",
    "merged_df",
    "GIAB_bed"
]
 
#create the data dictionary containing filepath, description of file and file read into a dataframe
data_dictionary = create_data_dictionary(dataframe_of_files = files_df)
#create the count dictionary
count_dictionary = create_count_dictionary(dictionary = data_dictionary)

#get the merged dataframe
merged_df = fetch_relevant_dataframe(dictionary = data_dictionary, key = 'merged_df')
#make a bed file of the variants that are in the results dataframe but not in the happy output dataframe
not_in_happy_bed = make_bed(dataframe = merged_df, output_directory = working_directory)
#run bedtools intersect on the variants not in the happy output dataframe to see whether they intersect with the GIAB bed used by happy
#if they are included in the bed file they should be in the happy output
#get the giab_bed from the data dictionary
giab_bed = data_dictionary.get('GIAB_bed', {}).get('File', None)
#run bed tools intersect and get a message to say whether it was successful
intersect_message = run_intersect(filepath_sample = not_in_happy_bed, filepath_bed = giab_bed, output_directory = working_directory, bedtools_flag = '-wa')[0]
#if the message starts with 'writing intersect output to' (this means it was successful)
#first make row_ids an empty list. Needed for later on if statement to update merged_df
row_ids = []
if intersect_message.startswith('Writing intersect output to'):
    #get the path for the intersect results to read back in
    intersect_result_filepath = run_intersect(filepath_sample = not_in_happy_bed, filepath_bed = giab_bed, output_directory = working_directory, bedtools_flag = '-wa')[1]
    #check if the filepath has anything in it
    with open(intersect_result_filepath, "r") as f:
        if f.read(1):  #tries to read first character and if it can
            #read in the intersect result into a df
            intersect_df = read_in_dataframe(filepath = f'{intersect_result_filepath}' , separator = '\t', header = None)
            #get the indices from the last column which link these results to the merged dataframe
            row_ids = intersect_df.iloc[:, -1]
            #and update the merged dataframe at those potitions with 'investigate'
            merged_df.loc[row_ids, 'status'] = 'investigate'
        else:
            print("Intersect_result.bed is empty. There aren't any variants not included in the happy dataframe which intersect with the GIAB bed")
else:
    print(intersect_message)

#UPDATE MERGED DATAFRAME WITH CHECK RESULT
#add a column to put review status as checked for any variant where '_merge' column says 'both'
merged_df.loc[merged_df['_merge'] == 'both', 'status'] = 'checked'
#update status column to 'new' for rows where '_merge'columns says right_only 
merged_df.loc[merged_df['_merge'] == 'right_only', 'status'] = 'new'

#update status column to 'not_in_giab' for rows that didn't overlap with giab bed
#first get all indexes of rows not in happy 
filtered_left = merged_df.loc[merged_df['_merge'] == 'left_only'].index
#from this list of indexes get the indexes that aren't the row-ids that do overlap with happy
not_overlap_indexes = filtered_left.difference(row_ids)
#update df
merged_df.loc[not_overlap_indexes, 'status'] = 'not_in_giab'

#update status column to 'not_in_giab' for rows that didn't overlap with giab bed
#first get all indexes of rows not in happy 
filtered_left = merged_df.loc[merged_df['_merge'] == 'left_only'].index
not_overlap_indexes = filtered_left.difference(row_ids)
merged_df.loc[not_overlap_indexes, 'status'] = 'not_in_giab'

#write out checked dataframe 
write_dataframe_to_tsv(dataframe_to_write = merged_df, write_to = f'{working_directory}/{caller_name}_checked_dataframe.tsv', header = 0)

#write out count dictionary
with open(f'{working_directory}/counts.csv', "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["file", "total_variants"])
    
    for key, value in count_dictionary.items():
        writer.writerow([key, value["total_variants"]])

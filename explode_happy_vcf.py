import pandas as pd
import argparse
import subprocess
import numpy as np

#CREATE ARGUMENT PARSER
parser = argparse.ArgumentParser(
    prog='Explode_Happy_VCF', 
    description = 'Takes an input happy output vcf and explodes all of the format values so that they are in separate columns '
)

def name_path_pair(arg):
    '''Convert variant caller name:path from '--vcf_file' argument into ('name', 'path'). This is needed to make sure that the vcfs are input in the correct format'''
    if ':' not in arg:
        raise argparse.ArgumentTypeError("Input must be in name:path format")
    name = arg.split(':', 1)[0]
    path = arg.split(':', 1)[1]
    return name, path

parser.add_argument('--vcf_file',type=name_path_pair, action='append', help='input the variant caller name and the filepath to the results vcf in name:path format')
parser.add_argument('--output_dir', default='./',type=str, help= 'directory to output dataframe files to')
args = parser.parse_args()

#DEFINE FUNCTIONS

#read in vcf to a dataframe
def read_vcf_into_dataframe(filepath):
    '''this function takes an input vcf and reads it in as a dataframe. The vcf header is removed'''
    #count the number of lines that do not start with '##' (header)
    number_to_skip = subprocess.run(f"zgrep '^##' {filepath} | wc -l ", capture_output=True, text=True, shell=True).stdout.strip()
    number = int(number_to_skip)
    separator = '\t'
    #read the file into a pandas dataframe remover the number of lines that are the header
    df = pd.read_csv(filepath, sep = separator, skiprows=number)
    return df

def get_field(input_list, specific_string):
    '''This function takes an input list and returns a value which starts with a specific string'''
    #turn the list of split strings into an array
    list_to_array = np.array(input_list)
    #get an array of indexes of elements in the series which start with a specific string
    array_of_indexes = np.where(np.char.startswith(list_to_array, f'{specific_string}'))[0]
    #if the array is not empty
    if array_of_indexes.size > 0:
        #get the index as an integer
        index_int = array_of_indexes[0]
        #get the value at that index
        value = input_list[index_int]
    else:
    #set value to None
        value = None
    return value

def extract_my_id(input_dataframe, column_to_extract, new_column):
    '''This function takes an input dataframe, extracts a specific string from a string within a column and puts the extracted string in its own column'''
    #make a new dataframe column
    input_dataframe[f'{new_column}'] = (input_dataframe[f'{column_to_extract}'].str.split(';')
        #containing a specific string extracted from the current string value                         
        .apply(lambda lst: get_field(input_list=lst, specific_string=new_column)))
    return input_dataframe
          
def make_exploded_dataframe(dataframe, val):
    ''' This function takes an input happy vcf dataframe and explodes the format column with metrics from another specified column'''
    #set a name for the new column to be added to the dataframe
    new_col_name = f'{val}_val'
    #create a new dataframe with an added column
    exploded_dataframe = (dataframe.assign(
            # containing each split value in the FORMAT string
            FORMAT_val = dataframe["FORMAT"].str.split(":")
            #with the value name appended to its name
            .apply(lambda vals: [f'{val}_{x}' for x in vals]),
            # containing each split value in the specified VCF column (dynamic name)
            **{new_col_name: dataframe[f'{val}'].str.split(":")})
        #mapped to each other
        .explode(["FORMAT_val", new_col_name]))
    return exploded_dataframe

def pivot_dataframe (input_dataframe, metric_column, value_column):
    '''this function pivots the dataframe to put specified metrics in columns instead of rows'''
    #subset columns to pivot on in a copied dataframe
    pivot_df = input_dataframe[[f"{metric_column}", f"{value_column}"]].copy()
    #create and add column with the index in, this will be used to pivot on.
    pivot_df["variant_index"] = input_dataframe.index
    #pivot the dataframe to make the metrics columns
    wide_df = (pivot_df.pivot(index="variant_index", columns = metric_column, values = value_column))
    #get all of the other columns from the original dataframe, wihtout duplicate rows for each metric
    original_cols = input_dataframe.drop(columns=[metric_column, value_column]).drop_duplicates()
    #merge the original columns with the pivoted dataframe to get a complete dataframe
    final_df = original_cols.merge(wide_df,left_index = True,right_index = True,how = "left")
    return final_df

def write_dataframe_to_tsv(dataframe_to_write, write_to):
    '''this function takes an input dataframe and writes it to a tsv file with the specified name'''
    dataframe_to_write.to_csv(write_to, index = False, sep = '\t')

def happy_vcf_to_tsv(filepath, output_file):
    #read happy results vcf into a dataframe
    read_in_vcf = read_vcf_into_dataframe(filepath)
    #extract the my_id from the info column and add it to its own column in the dataframe
    dataframe_with_id = extract_my_id(input_dataframe = read_in_vcf, column_to_extract = 'INFO', new_column = 'my_id')
    #explode the TRUTH and FORMAT columns in the happy results dataframe
    exploded_dataframe = make_exploded_dataframe(dataframe = dataframe_with_id, val = 'TRUTH')
    #pivot dataframe to include the TRUTH metrics in columns
    pivoted_dataframe = pivot_dataframe(input_dataframe = exploded_dataframe, metric_column = 'FORMAT_val', value_column = 'TRUTH_val')
    #explode QUERY and FORMAT columns in the pivoted dataframe
    exploded_pivoted_dataframe = make_exploded_dataframe(dataframe = pivoted_dataframe, val = 'QUERY')
    #pivot dataframe to include the TRUTH metrics in columns
    final_pivoted_dataframe = pivot_dataframe(input_dataframe = exploded_pivoted_dataframe, metric_column = 'FORMAT_val', value_column = 'QUERY_val')
    #write to dataframe file
    write_dataframe_to_tsv(dataframe_to_write = final_pivoted_dataframe, write_to = output_file)

#MAIN
OUTPUT_DIRECTORY = args.output_dir

#get the caller name and input vcf filepath for each caller from the arg input
for element in args.vcf_file:
    caller_name = element[0]
    happy_vcf_filepath = element[1]
    #create a name for the output dataframe files
    output_file_path= f'{OUTPUT_DIRECTORY}/{caller_name}_exploded_happy_dataframe.tsv'
    #write to dataframe
    print(f'writing happy results as an exploded dataframe to {output_file_path}')
    happy_vcf_to_tsv(filepath = happy_vcf_filepath, output_file = output_file_path)
import pandas as pd
import subprocess
import numpy as np
import argparse

#CREATE ARGUMENT PARSER
parser = argparse.ArgumentParser(
    prog='Populate IDs', 
    description = 'Takes an input vcf, filters for PASS only, adds a random ID to the INFO column and outputs an updated vcf'
)

def name_path_pair(arg):
    '''Convert variant caller name:path from '--vcf_file' argument into ('name', 'path'). This is needed to make sure that the vcfs are input in the correct format'''
    if ':' not in arg:
        raise argparse.ArgumentTypeError("Input must be in name:path format")
    name = arg.split(':', 1)[0]
    path = arg.split(':', 1)[1]
    return name, path

parser.add_argument('--vcf_file',type=name_path_pair, action='append', help='input the variant caller name and the filepath in name:path format')
parser.add_argument('--output', default='./',type=str, help= 'filepath to output dataframe files to')
args = parser.parse_args()

#read in vcf header
def read_in_header (filepath):
    header_lines = []
    with open(filepath) as f:
        for line in f:
            if line.startswith('#'):
                header_lines.append(line)
            else:
                break
    return header_lines

#read in vcf to dataframe not including header
def read_vcf_into_dataframe(filepath):
    '''this function takes an input vcf and reads it in as a dataframe. The vcf header is removed'''
    #read in vcf file ignoring any header lines
    separator = '\t' 
    #count the number of lines that start with '##' (header)
    number_to_skip = subprocess.run(f"grep '^##' {filepath} | wc -l ", capture_output=True, text=True, shell=True).stdout.strip()
    number = int(number_to_skip)
    #read the file into a pandas dataframe removing the number of lines that are the header
    df = pd.read_csv(filepath, sep = separator, skiprows=number)
    return df

def pass_only(df, column_name, keep_value):
    '''this function takes an input dataframe and filters by a specific column value'''
    filtered_df = df[df[column_name] == keep_value]
    return filtered_df

def populate_id(input_dataframe, column_name, string):
    changed_dataframe = input_dataframe
    #create an empty list for row indexes
    row_indexes = []
    for index in range(len(changed_dataframe)):
        row_indexes.append(index)
    #create an empty list for ID numbers
    id_numbers = []
    #list numbers from 1 to the length of the dataframe + 1. These will be the numbers assigned to each id.
    for i in range(1,len(changed_dataframe)+1):
        id_numbers.append(i)
    #create an array of the list of id numbers 
    id_array = np.array(id_numbers)
    #create an array of the list of row indexes
    row_index_array = np.array(row_indexes)
    #create an array of the values at each row index of a specified column
    column_values = changed_dataframe[column_name].iloc[row_index_array].values
    #create an array of updated column values
    updated_column_values = np.where(
        #any column values that are True for '.' or True for ''
        (column_values == '.') | (column_values == ''),
        #are updated with the string and id using this format
        f'{string}' + id_array.astype(str),
        #otherwise any columns values that are false for '.' or  '' are updated with the string and id using this format
        column_values + f';{string}' + id_array.astype(str))
    #update the changed dataframe column with the updated values
    changed_dataframe[column_name] = updated_column_values
    return changed_dataframe

#export as vcf again with the header
def export_as_vcf(input_dataframe, header_only, output_filepath):
    with open(output_filepath, "w") as out:
         # write the header exactly as stored
        out.writelines(line if line.endswith("\n") else line + "\n" for line in header_only)
        #write the dataframe without the header
        input_dataframe.to_csv(out, sep="\t", index=False, header=False)

for element in args.vcf_file:
    caller_name = element[0]
    filepath = element[1]

output_directory = args.output

#read in the header
header_only = read_in_header(filepath)
#read in the rest of the vcf to the dataframe
vcf_dataframe = read_vcf_into_dataframe(filepath)
#filter the filter column to keep only 'PASS'
pass_only_df = pass_only(df = vcf_dataframe, column_name = 'FILTER', keep_value = 'PASS')
#populate each value in the INFO column with 'my_id={number from 1 to total number of rows}'
populated_dataframe = populate_id(input_dataframe = pass_only_df, column_name = 'INFO', string = 'my_id=')
#split the filepath by / and get the last element of the list to use as the new filename
current_filename = filepath.split('/')[-1]
#construct a new filepath
new_filename = f'{output_directory}/info_passonly_{current_filename}'
#export the populated vcf with its header to the original path
print(f'writing {caller_name} updated vcf to {new_filename}')
export_as_vcf(input_dataframe = populated_dataframe, header_only = header_only , output_filepath = new_filename)
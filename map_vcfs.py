import pandas as pd
import subprocess
import argparse
import numpy as np

#CREATE ARGUMENT PARSER
parser = argparse.ArgumentParser(
    prog='VcftoDataframe', 
    description = 'Takes an input vcf, separates metrics and values in the info column into seperate fields and outputs the dataframe as a tsv file'
)

def name_path_pair(arg):
    '''Convert variant caller name:path from '--vcf_file' argument into ('name', 'path'). This is needed to make sure that the vcfs are input in the correct format'''
    if ':' not in arg:
        raise argparse.ArgumentTypeError("Input must be in name:path format")
    name = arg.split(':', 1)[0]
    path = arg.split(':', 1)[1]
    return name, path

parser.add_argument('--vcf_file',type=name_path_pair, action='append', help='input the variant caller name and the filepath to the results vcf in name:path format')
parser.add_argument('--output', default='./',type=str, help= 'filepath to output dataframe files to')
args = parser.parse_args()
#DEFINE FUNCTIONS

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

def make_exploded_dataframe(dataframe):
    #get format column name
    format_col_name = dataframe.columns[-2]
    #get end column name
    end_col_name = dataframe.columns[-1]
    #get info
    #create a new dataframe with an added columns
    exploded_dataframe = (dataframe.assign(
                            #containing each split value in the format string
                            format_val = dataframe[f"{format_col_name}"].str.split(":"),
                            #containing each split value in the end vcf column
                            end_val = dataframe[f"{end_col_name}"].str.split(":"))
                            #mapped to eachother
                            .explode(["format_val", "end_val"]))
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


def vcf_to_dataframe(input_vcf, output_file):
    '''this function takes an input vcf file, reads it into a dataframe, separates the metrics and values in the info column into seperate fields and outputs the dataframe as a csv file'''
    #read in vcf file ignoring any header lines
    df = read_vcf_into_dataframe(filepath = input_vcf)
    #make exploded dataframe with format metrics and corresponding values
    exploded_df = make_exploded_dataframe(dataframe = df)
    #aggregate to collapse rows again 
    pivoted_df = pivot_dataframe(input_dataframe = exploded_df, metric_column = 'format_val', value_column = 'end_val')
    #extract the my_id value from the the INFO column and put it in its own column.
    id_dataframe = extract_my_id(input_dataframe = pivoted_df , column_to_extract = 'INFO', new_column = 'my_id')
    #write the final dataframe to a csv file
    write_dataframe_to_tsv(dataframe_to_write = id_dataframe, write_to = output_file)


#MAIN

#from the output file path argument get the filepath to output dataframe files to
OUTPUT_FILE_PATH_ARG = args.output

#get the caller name and input vcf filepath for each caller from the arg input
for element in args.vcf_file:
    caller_name = element[0]
    input_vcf = element[1]
    #create a name for the output dataframe files
    output_file_path= f'{OUTPUT_FILE_PATH_ARG}/{caller_name}_dataframe.tsv'
    print(f'writing mapped results vcf to {output_file_path}')
    #write to dataframe
    vcf_to_dataframe(input_vcf= input_vcf, output_file = output_file_path)

#STILL NEED TO DO
#CREATE A RANDOM NUMBER TO ADD TO THE FILE IF THE VARIANT CALLER IS THE SAME.
#WITHIN MY LOOP, MAKE A DICTIONARY RECORDING THE INPUT FILE AND THE OUTPUT FILE NAME, THEN WRITE THIS TO A LOG FILE AT THE END OF THE SCRIPT.
#THE LOG FILE WILL BE OUTSIDE OF THE LOOP
import pandas as pd
import argparse
import subprocess 

#CREATE ARGUMENT PARSER
parser = argparse.ArgumentParser(
    prog='Add_Happy_Status', 
    description = 'Takes an input happy output vcf and adds a column to the input dataframe with the happy output for each variant'
)

def separate_input_pair(arg):
    '''Convert input:input from argument into ('input', 'input', 'input')'''
    if arg.count(':') != 2:
        raise argparse.ArgumentTypeError("Input must be in input:input:input format")
    input1 = arg.split(':')[0]
    input2 = arg.split(':')[1]
    input3 = arg.split(':')[2]
    return input1, input2, input3

parser.add_argument('--input',type=separate_input_pair, action='append', help='input the variant caller, filepath to the metrics dataframe and the filepath to the happy results vcf dataframe in caller_name:path/to/dataframe:filepath/to/happy_results_dataframe format')
parser.add_argument('--output', default='./',type=str, help= 'filepath to output dataframe files to')
args = parser.parse_args()

#read in dataframe
def read_dataframe(dataframe_filepath):
    '''this fuction reads in a dataframe'''
    df = pd.read_csv(dataframe_filepath, sep = '\t')
    return df

def create_unique_column(input_dataframe, list_of_columns):
    ''' this function merges the data in specified columns and puts it in a new column. This new column acts as a unique identifier for the row'''
    #add a new column to the dataframe
    input_dataframe['unique_column'] = (
        #where the column value is a string of all values taken from columns specified in [list_of_columns]
        input_dataframe[list_of_columns].astype(str)
            #aggregated across the rows and joined with a '-' separator
            .agg('_'.join, axis = 1)
            )
    return input_dataframe

def merge_on_unique(df1, df2):
    result = pd.merge(df1, df2, how  = 'outer', on = 'unique_column', suffixes = ('_res', '_hap'))
    return result

def write_dataframe_to_tsv(dataframe_to_write, write_to):
    '''this function takes an input dataframe and writes it to a tsv file with the specified name'''
    dataframe_to_write.to_csv(write_to, index = False, sep = '\t')


#MAIN
OUTPUT_FILE_PATH_ARG = args.output 

#iterate through the input argument paris
for element in args.input:
    #assign the caller name to caller name
    caller_name = element[0]
    #assign the results dataframe filepath to input_results_dataframe
    input_results_dataframe = element[1]
    #assign the happy vcf dataframe filepath to happy_results_dataframe
    happy_results_dataframe = element[2]
    #read in results dataframe
    results_dataframe = read_dataframe(dataframe_filepath = input_results_dataframe)
    #add a new column in results dataframe with merged data from #CHROM, POS, REF and ALT columns
    unique_col_dataframe = create_unique_column(input_dataframe = results_dataframe, list_of_columns = ['#CHROM', 'POS', 'REF', 'ALT'])
    #read in happy vcf dataframe
    happy_vcf_dataframe = read_dataframe(dataframe_filepath = happy_results_dataframe)
    #add a new column in happy vcf dataframe with merged data from #CHROM, POS, REF and ALT columns
    unique_col_happy_vcf_dataframe = create_unique_column(input_dataframe = happy_vcf_dataframe, list_of_columns = ['#CHROM', 'POS', 'REF', 'ALT'])
    #merge the results dataframe and happy vcf dataframe on the unique columns just made
    merged_df = merge_on_unique(df1 = unique_col_dataframe, df2 = unique_col_happy_vcf_dataframe)
    #create file path to write dataframe to
    output_file_path= f'{OUTPUT_FILE_PATH_ARG}/{caller_name}_merged_happy_dataframe.tsv'
    #printing message
    print(f'writing CALLERNAME {caller_name}')
    #write dataframe to file
    write_dataframe_to_tsv(dataframe_to_write = merged_df, write_to = output_file_path)
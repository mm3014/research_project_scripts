import pandas as pd
import subprocess

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

#populate a variant count into the id column
def populate_id(input_dataframe):
    #get the dataframe ID column
    input_dataframe['ID'] = range(1,len(input_dataframe) + 1)
    return input_dataframe

#export as vcf again with the header
def export_as_vcf(input_dataframe, header_only, output_filepath):
    with open(output_filepath, "w") as out:
         # write the header exactly as stored
        out.writelines(line if line.endswith("\n") else line + "\n" for line in header_only)
        #write the dataframe without the header
        input_dataframe.to_csv(out, sep="\t", index=False, header=False)


filepath = 'path/to/file'

#read in the header
header_only = read_in_header(filepath)
#read in the rest of the vcf to the dataframe
vcf_dataframe = read_vcf_into_dataframe(filepath)
#populate the ID column with a number
populated_dataframe = populate_id(input_dataframe = vcf_dataframe)
#split the filepath by / and get the last element of the list to use as the new filename
current_filename = filepath.split('/')[-1]
#get the rest of the filepath 
rest_of_filename = "/".join(filepath.split("/")[:-1])
#get the file_extension 
extension = current_filename.split('.')[-1]
#construct a new filepath
new_filename = f'{rest_of_filename}/{current_filename}_id.{extension}'
#export the populated vcf with its header to the original path
export_as_vcf(input_dataframe = populated_dataframe, header_only = header_only , output_filepath = new_filename)
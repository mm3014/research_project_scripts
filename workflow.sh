### TO RUN SCRIPT FROM COMMAND LINE
### 1. COPY THE CALLER  VCF OVER TO THE CALLER_OUPUT file
### 2. RUN ON THE COMMAND LINE WITH COMMAND
###    path_to/workflow.sh path_to/project_workflow 'variant_caller_name'

!/usr/bin/env bash

#this is the filepath to the project workflow folder that was input via the command line when calling the workflow script
PROJECT_WORKFLOW_FOLDER=$1
#this is the name of the variant caller that was input via the command line when calling the workflow script
CALLER_INPUT=$2
### SET UP THE WORKFLOW DIRECTORIES ###

echo "starting"
echo "working in directory: ${PROJECT_WORKFLOW_FOLDER}"
echo "analysing caller: ${CALLER_INPUT}"

WORKING_DIR=$PROJECT_WORKFLOW_FOLDER
ALL_RESULTS="${WORKING_DIR}/project_results"
CALLER_OUTPUT="${WORKING_DIR}/caller_output"
REF_DIRECTORY="${WORKING_DIR}/ref_files"
SCRIPTS="${WORKING_DIR}/research_project_scripts/scripts"
CALLER=$CALLER_INPUT

#make folder for my analysis results for the specific caller
ANALYSIS_RESULTS="${ALL_RESULTS}/${CALLER}"
mkdir -p "${ANALYSIS_RESULTS}"

#make folder for the output dataframes
DATAFRAMES_DIR="${ANALYSIS_RESULTS}/dataframes"
mkdir -p "${DATAFRAMES_DIR}"

#make the file log in the caller's analysis results folder
FILE_LOG="${ANALYSIS_RESULTS}/${CALLER}_files.csv"
touch "${FILE_LOG}"
echo "Description,File" >> "${FILE_LOG}"

#make the error log 
ERROR_LOG="${ANALYSIS_RESULTS}/error_log.txt"
touch "${ERROR_LOG}"

### DEFINE REF FILES NEEDED ###
GIAB_VCF="${REF_DIRECTORY}/HG001_GRCh38_v3.3.2_benchmark.vcf.gz"
REF="${REF_DIRECTORY}/GRCh38_no_alt_analysis_set.fa"
GIAB_BED="${REF_DIRECTORY}/HG001_GRCh38_v3.3.2_benchmark.bed"
SAMPLE_BED="${REF_DIRECTORY}/Twist_Comprehensive_Exome_Covered_Targets_hg38.bed"

### CREATE FUNCTIONS FOR ERROR LOG, FILE LOG AND FILE EXISTENCE CHECKS

#check if the input to the step exists and the expected ouput doesn't exist
check_before_step() {
  #local means a variable only for this function
  local step_input="$1"
  local step_expected_output="$2"

  #if the input exists and the output doesn't
  if [[ -e "$step_input" && ! -e "$step_expected_output" ]]; then
    #run step
    return 0
  else
  #skip step
    return 1 
  fi
}

#Function to write that the stp is running to the ERROR_LOG
log_step_running() {
  local script="$1"
  local step_input="$2"
  local step_key="$3"
  {
    echo "[INFO] Running script: ${script}"
    echo "[INFO] Script input: ${step_input}"
    echo "[INFO] Generating ${step_key}"
  }>> "$ERROR_LOG"
}

#Function to write that a step was skipped to the ERROR_LOG
log_step_skipped() {
  local script="$1"
  local step_input="$2"
  local step_key="$3"
  {
    echo "[ERROR] Skipped script: ${script}"
    echo "[ERROR] Input attempted: ${step_input}"
    echo "[ERROR] Did not generate ${step_key}"
  }>> "$ERROR_LOG"
}

add_file_to_list() {
    local key="$1"
    local filepath="$2"
{
    echo "$key,${filepath}"
}>> "$FILE_LOG"
}

### LOCATE INPUT VCF STEP ###

#get the filepath of the caller's output vcf and assign to the INPUT variable
INPUT=$(ls "${CALLER_OUTPUT}"/*"${CALLER}"*.vcf)
#add the input file to the file log with the step key
STEP_KEY='caller_output'
add_file_to_list "$STEP_KEY" "$INPUT"

### POPULATE IDS STEP ###

#define the file path for the results vcf
RESULTS_VCF="${ANALYSIS_RESULTS}/populated_my_id_passonly.vcf" 
#define the EXPECTED_OUTPUT
EXPECTED_OUTPUT="$RESULTS_VCF"
#define the filepath to the script to run
SCRIPT_TO_RUN="${SCRIPTS}/populate_id.py"
#define the step for the error log
STEP_KEY="vcf_with_ids"

#if input exists and output doesn't exist
if check_before_step "$INPUT" "$EXPECTED_OUTPUT"; then
#log in the error log that the step is running
    log_step_running "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
    #call the python script
    python "${SCRIPT_TO_RUN}" \
    --vcf_file "${CALLER}:${INPUT}" \
    --output_dir "${ANALYSIS_RESULTS}"
    #add files created to file list. This file list is used for the checks step
    add_file_to_list "$STEP_KEY" "$EXPECTED_OUTPUT" 
else
    log_step_skipped "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
fi

### MAP VCFS STEP ###

#get the input (the output from populate ids step)
INPUT="$RESULTS_VCF"
#define the results dataframe filepath
RESULTS_DF="${DATAFRAMES_DIR}/${CALLER}_dataframe.tsv"
#define the filepath for the expected output
EXPECTED_OUTPUT="$RESULTS_DF"
#define the filepath to the script to run
SCRIPT_TO_RUN="${SCRIPTS}/map_vcfs.py"
#define the step for the error log
STEP_KEY="results_df"

#if input exists and output doesn't exist
if check_before_step "$INPUT" "$EXPECTED_OUTPUT"; then
#log in the error log that the step is running
    log_step_running "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
    #call the python script
    python "${SCRIPT_TO_RUN}" \
    --vcf_file "${CALLER}:${INPUT}" \
    --output_dir "${DATAFRAMES_DIR}"
    #add files created to file list. This file list is used for the checks step
    add_file_to_list "$STEP_KEY" "$EXPECTED_OUTPUT" 
else
    log_step_skipped "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
fi

### RUN HAPPY STEP ###

#keep input the same (the output from populate ids step)
INPUT="$RESULTS_VCF"
#define the filepath for the expected output directory
EXPECTED_OUTPUT="${ANALYSIS_RESULTS}/happy"
#define the happy output file needed for the downstream analysis. This needs to be loggged
HAPPY_VCF="${EXPECTED_OUTPUT}/${CALLER}.vcf"
#define the filepath to the script to run
SCRIPT_TO_RUN="${SCRIPTS}/run_happy.sh"
#define the step for the error log
STEP_KEY="happy_vcf"

#if input exists and happy output directory doesn't exist
if check_before_step "$INPUT" "$EXPECTED_OUTPUT"; then
#log in the error log that the step is running
    log_step_running "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
    #make output directory for happy results
    mkdir -p "${EXPECTED_OUTPUT}"
    #run the script to run happy
    ${SCRIPT_TO_RUN} "$GIAB_VCF" "$INPUT" "$REF" "$GIAB_BED" "$SAMPLE_BED" "$EXPECTED_OUTPUT" "$CALLER"
    #if the HAPPY_VCF file exists add file to file list. This file list is used for the checks step
    if [[ -f "$HAPPY_VCF" ]]; then
    add_file_to_list "$STEP_KEY" "$HAPPY_VCF"
    else
    log_step_skipped "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
    fi
else
    log_step_skipped "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
fi

### EXPLODE HAPPY OUTPUT STEP ###

#get the happy output_vcf file
INPUT=$HAPPY_VCF
#define HAPPY_DF
HAPPY_DF="${DATAFRAMES_DIR}/${CALLER}_exploded_happy_dataframe.tsv"
#define the filepath for the expected output directory
EXPECTED_OUTPUT="$HAPPY_DF"
#define the filepath to the script to run
SCRIPT_TO_RUN="${SCRIPTS}/explode_happy_vcf.py"
#define the step for the error log
STEP_KEY="happy_exploded_df"

#if input exists and output doesn't exist
if check_before_step "$INPUT" "$EXPECTED_OUTPUT"; then
#log in the error log that the step is running
    log_step_running "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
    #call the python script
    python "${SCRIPT_TO_RUN}" \
    --vcf_file "${CALLER}:${INPUT}" \
    --output_dir "${DATAFRAMES_DIR}"
    #add files created to file list. This file list is used for the checks step
    add_file_to_list "$STEP_KEY" "$EXPECTED_OUTPUT" 
else
    log_step_skipped "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
fi

### MERGE DATAFRAMES STEP ###

#define results dataframe as INPUT1
INPUT1=$RESULTS_DF
#define happy exploded dataframe as INPUT2
INPUT2=$HAPPY_DF
#define filepath for merged dataframe 
MERGED_DF="${DATAFRAMES_DIR}/${CALLER}_merged_happy_dataframe.tsv"
#define the filepath for the expected output directory
EXPECTED_OUTPUT=$MERGED_DF
#define the filepath to the script to run
SCRIPT_TO_RUN="${SCRIPTS}/add_happy_status.py"
#define the step for the error log
STEP_KEY="merged_df"

#if input exists and output doesn't exist
if check_before_step "$INPUT1" "$EXPECTED_OUTPUT" \
  && check_before_step "$INPUT2" "$EXPECTED_OUTPUT"; then
  #define the input
    INPUT="${CALLER}:${INPUT1}:${INPUT2}"
#log in the error log that the step is running
    log_step_running "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
    #call the python script
    python "${SCRIPT_TO_RUN}" \
    --input "${INPUT}" \
    --output_dir "${DATAFRAMES_DIR}"
    #add files created to file list. This file list is used for the checks step
    add_file_to_list "$STEP_KEY" "$EXPECTED_OUTPUT" 
else
    log_step_skipped "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
fi

### RUN CHECKS STEP ###

#add GIAB bed to file list
STEP_KEY='GIAB_bed'
add_file_to_list "$STEP_KEY" "$GIAB_BED"

#define input
INPUT=$FILE_LOG
#define filepath for checked dataframe 
CHECKED_DF="${DATAFRAMES_DIR}/${CALLER}_checked_happy_dataframe.tsv"
#define the filepath for the expected output directory
EXPECTED_OUTPUT=$CHECKED_DF
#define script to run 
SCRIPT_TO_RUN="${SCRIPTS}/checks.py"
#defien step key
STEP_KEY='checks'

#if input exists and output doesn't exist
if check_before_step "$INPUT" "$EXPECTED_OUTPUT"; then
#log in the error log that the step is running
    log_step_running "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
    #call the python script
    python "${SCRIPT_TO_RUN}" \
    --files_list "${CALLER}:${INPUT}" \
    --working_dir "${DATAFRAMES_DIR}"
else
    log_step_skipped "$SCRIPT_TO_RUN" "$INPUT" "$STEP_KEY"
fi


##### NEED TO MAKE THE PARENT DIR
####COPY THE CALLER  VCF OVER TO THE CALLER_OUPUT file

!/usr/bin/env bash

### SET UP THE WORKFLOW DIRECTORIES ###

WORKING_DIR=/pathto/project_workflow
ALL_RESULTS="${WORKING_DIR}/project_results"
CALLER_OUTPUT="${WORKING_DIR}/caller_output"
SCRIPTS="${WORKING_DIR}/scripts"
CALLER="deepvariant"

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

#define the file path for the output
EXPECTED_OUTPUT="${ANALYSIS_RESULTS}/info_passonly.vcf"
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

### run happy "happy_vcf" 
### CAN JUST COPY THE COMMAND INTO HERE



### map vcfs "results_df"

#define the file path for the output dataframes
EXPECTED_OUTPUT="${DATAFRAMES_DIR}/${CALLER}_dataframe.tsv"

### explode happy output  "happy_exploded_df"

### add happy status "merged_df"

###checks "GIAB_bed"



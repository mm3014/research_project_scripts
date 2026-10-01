#!/bin/bash

GIAB_VCF="$1"
INPUT="$2"
REF="$3"
GIAB_BED="$4"
SAMPLE_BED="$5"
EXPECTED_OUTPUT="$6"
CALLER="$7"

#set output prefix
PREFIX="${EXPECTED_OUTPUT}/${CALLER}"

#run happy using docker 
docker run -it -v /data/:/data happy /opt/hap.py/bin/hap.py \
"$GIAB_VCF" \
"$INPUT" \
-r "$REF" \
--gender female --decompose --leftshift --adjust-conf-regions --preserve-info --ci-alpha 0.05 \
-f "$GIAB_BED" \
-T "$SAMPLE_BED" \
-o "$PREFIX"

#unzip the happy results vcf so that is can be read in to further analysis steps
HAPPY_RESULTS_FILE="${PREFIX}.vcf.gz"
gunzip $HAPPY_RESULTS_FILE
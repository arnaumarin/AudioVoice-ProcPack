#!/bin/bash

# Be sure that this file has execution permissions:
# Use the nautilus explorer or chmod +x run_vad.sh

# Write here the name and path of your program and database
DB=$HOME/PAV/P2/db.v4
CMD=bin/vad
rm -f out_alpha.txt                     #delete previous file (this script concatenates existing data)
lower_index_bound=0                     #lower bound of the for loop
upper_index_bound=100                   #upper bound of the for loop
offset=0                                #offset of the variable we want to iterate
div=1                                   #controls the step size of the variable when we iterate it (=2 -> /2)
for index in $(seq $lower_index_bound $upper_index_bound); do #vary $index from (lower_index_bound) to (upper_index_bound)
    echo "i = $index"
    k0=$(bc <<<"scale=2; $offset+$index/$div")    #stores offset+$index/div in k0 (uses basic calculator (bc) since shell doesn't seem to support floating point by default)
    echo "k0 = $k0"                     #display k0 value 
    echo -n "$k0 ">> out_alpha.txt      #print k0 value in out_alpha.txt

    for filewav in $DB/*/*wav; do

        if [[ ! -f $filewav ]]; then
            echo "Wav file not found: $filewav" >&2
            exit 1
        fi

        filevad=${filewav/.wav/.vad}
        
        $CMD -i $filewav -o $filevad -t $k0 || exit 1

        # Alternatively, uncomment to create output wave files
        #    filewavOut=${filewav/.wav/.vad.wav}
        #    $CMD $filewav $filevad $filewavOut || exit 1

    done
    #vad_evaulation_printless.pl is almost like vad_evaluation.pl, except that most prints on display have been delated to view the TOTAL results properly
    #this .pl is also in charge of printing the "TOTAL" results into out.alpha.txt, since parsing it from the screen through the shell script seemed way too complex
    scripts/vad_evaluation_printless.pl $DB/*/*lab 
    echo ""
done

exit 0

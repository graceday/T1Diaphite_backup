#!/bin/bash
SCALEFACTORS=$(cat scalefactors.txt)
for i in {1..17}; do
	g=$(awk -v i="$i" 'FNR == i {print $1}' sequences.txt)
	d=$(awk -v i="$i" 'FNR == i {print $2}' sequences.txt)
	mkdir -p g_"$g"_d_"$d"
	cd g_"$g"_d_"$d"
	for SFa in ${SCALEFACTORS[@]}; do
		for SFb in ${SCALEFACTORS[@]}; do
			for SFc in ${SCALEFACTORS[@]}; do
				DIRNAME=dpt1_scaled_"$SFa"_"$SFb"_"$SFc"_"$1"
				mkdir -p "$DIRNAME"
				cp ../SUBMISSIONSCRIPT.sh ./"$DIRNAME"/"$DIRNAME".sh
				cp ../"$1".inpt ./"$DIRNAME"/"$1".inpt
				python ../t1_diaphite_creator_scaled.py --out_file ./"$DIRNAME"/"positions.data" --g "$g" --d "$d" --nx 4 --ny 4 --nz 3 --sfa "$SFa" --sfb "$SFb" --sfc "$SFc"
				cd "$DIRNAME"
				qsub "$DIRNAME".sh
				cd ../
			done
		done
	done
	cd ../
done

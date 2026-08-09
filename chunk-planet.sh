#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <osm.pbf>"
    exit 1
fi

PBFFILE=$1
latchunk=180
lonchunk=15

if [ ! -d planet ]; then
    mkdir planet
fi

for latitude in $(seq -90 ${latchunk} 89)
do
    for longitude in $(seq -180 ${lonchunk} 179)                   
    do
        key=$(printf "%04d,%04d,%04d,%04d\n" ${longitude} ${latitude} $((longitude + lonchunk)) $((latitude + latchunk)))
        outkey=$(printf "%04d%04d%04d%04d\n" ${longitude} ${latitude} $((longitude + lonchunk)) $((latitude + latchunk)))
        echo ${key}        
        if [ ! -s planet/planet-${outkey}.osm.pbf ]; then           
            osmconvert ${PBFFILE} -b=${key} -o=planet/planet-${outkey}.osm.pbf &
            while :
            do
                N=$(ps -A -ww | fgrep osmconvert | wc -l)
                echo ${N} ${outkey}
                sleep 5
                if [[ ${N} -le 24 ]] ; then
                    break
                fi
                sleep 55
            done
        fi
    done
done

while :
    do
        N=$(ps -A -ww | fgrep osmconvert | wc -l)
        if [[ ${N} -eq 0 ]] ; then
            break
        fi
        echo ${N} running
        sleep 60
done

echo finish

#!/usr/bin/env bash

for i in archive data output
do
    if [ ! -d ${i} ]; then
        mkdir -p ${i}
    fi
done


if [ ! -d venv ]; then
    echo Set up python3 virtual environment
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

if [ $(ls data/*.pbf 2> /dev/null | wc -l) -gt 1 ]; then
    echo ERROR: more than one osm.pbf file in data directory
    echo data/*.pbf
    exit 1
elif [ ! $(ls data/*.pbf 2> /dev/null | wc -l) -eq 1 ]; then
    echo ERROR: download INE osm.pbf file in data directory
    echo e.g. https://download.geofabrik.de/europe/britain-and-ireland.html
    exit 2
fi

for FILENAME in output/*.gpkg
do
    if [ ! -s ${FILENAME} ]; then
        mv ${FILENAME} archive
    fi
done

./quackosmget.py

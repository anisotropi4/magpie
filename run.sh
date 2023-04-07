#!/usr/bin/env bash

set -x

for i in archive cache
do
    if [ ! -d ${i} ]; then
        mkdir -p ${i}
    fi
done

if [ ! -d venv ]; then
    echo Set up python3 virtual environment
    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

for FILENAME in great-britain-rail.geojson great-britain-rail.gpkg
do
    if [ ! -s ${FILENAME} ]; then
        mv ${FILENAME} archive
    fi
done

./osmnxget.py

ln great-britain-rail.geojson output-all.json

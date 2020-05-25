#!/bin/sh

if [ ! -d output/archive ]; then
    mkdir -p output/archive
fi

CONTINENT=europe
REGION=great-britain

URL=http://download.geofabrik.de/${CONTINENT}
FILENAME=${REGION}-latest.osm.pbf
if [ ! -s  output/${FILENAME} ]; then
    curl -L -o output/${FILENAME} ${URL}/${FILENAME}
fi


if [ ! -f ${REGION}.poly ]; then
    echo missing ${REGION}.poly polygon file
    exit 1
fi

if [ x"$(find output/${REGION}-latest.osm.pbf -mmin -15)" = x ]; then
    osmupdate output/${FILENAME} ${REGION}-update.osm.pbf -B=${REGION}.poly --verbose --keep-tempfiles
    mv output/${FILENAME} output/archive
    mv ${REGION}-update.osm.pbf output/${FILENAME}
else
    echo "${FILENAME} is less than 15 minutes old"
fi

KEYWORD=rail
for element in points lines multilinestrings multipolygons other_relations
do
    if [ ! -s ${REGION}-${KEYWORD}-${element}.json ]; then
        ogr2ogr --config OGR_INTERLEAVED_READING YES --config OSM_CONFIG_FILE osmconf-all.ini \
                -where "(railway IS NOT NULL) OR (train IS NOT NULL) or (rail IS NOT NULL) or (ref_tiploc IS NOT NULL)" \
		            -f GeoJSON ${REGION}-${KEYWORD}-${element}.json \
		            output/${REGION}-latest.osm.pbf ${element}
    fi
done

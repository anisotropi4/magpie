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

if [ ! -f data/${REGION}.poly ]; then
    echo missing data/${REGION}.poly polygon file
    exit 1
fi

if [ x"$(find output/${REGION}-latest.osm.pbf -mmin -15)" = x ]; then
    osmupdate output/${FILENAME} ${REGION}-update.osm.pbf -B=data/${REGION}.poly --verbose --keep-tempfiles
    mv output/${FILENAME} output/archive
    mv ${REGION}-update.osm.pbf output/${FILENAME}
else
    echo "${FILENAME} is less than 15 minutes old"
fi

for element in points lines multilinestrings multipolygons other_relations
do
    KEYWORD=all
    if [ ! -s ${REGION}-${KEYWORD}-${element}.json ]; then
        ogr2ogr --config OGR_INTERLEAVED_READING YES --config OSM_CONFIG_FILE osmconf-${KEYWORD}.ini \
                -where "(railway IS NOT NULL) OR (train IS NOT NULL) or (rail IS NOT NULL)" \
		            -f GeoJSON ${REGION}-${KEYWORD}-${element}.json \
		            output/${REGION}-latest.osm.pbf ${element}
    fi
done

if [ ! -s extract-keys.txt ]; then
    jq '.features[].properties.all_tags' great-britain-all-*.json | sed 's/=>/:/g; s/^"//; s/"$//; s/\\//g; s/","/"\n"/g' | sed 's/":.*$/"/' | sort -u > extract-keys.txt
fi


for element in points lines multilinestrings multipolygons other_relations
do
    KEYWORD=rail
    if [ ! -s ${REGION}-${KEYWORD}-${element}.json ]; then
            ogr2ogr --config OGR_INTERLEAVED_READING YES --config OSM_CONFIG_FILE osmconf-${KEYWORD}.ini \
                -where "(railway IS NOT NULL) OR (train IS NOT NULL) or (rail IS NOT NULL)" \
		            -f GeoJSON ${REGION}-${KEYWORD}-${element}.json \
		            output/${REGION}-latest.osm.pbf ${element}
    fi
    KEYWORD=voltage
    if [ ! -s ${REGION}-${KEYWORD}-${element}.json ]; then
            ogr2ogr --config OGR_INTERLEAVED_READING YES --config OSM_CONFIG_FILE osmconf-${KEYWORD}.ini \
                -where "((railway IS NOT NULL) OR (train IS NOT NULL) or (rail IS NOT NULL)) AND (voltage IS NOT NULL)" \
		            -f GeoJSON ${REGION}-${KEYWORD}-${element}.json \
		            output/${REGION}-latest.osm.pbf ${element}
    fi
done


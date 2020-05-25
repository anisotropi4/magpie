# GB Rail data

Open Street Map contains lots of data about the railway in mainland Britain. These scripts extract the full Open Street Map dataset and then filter for point associated with rail.

## Creating the datafiles and associate geojson format report

Once the dependencies to create the report are met run the script:

    $ ./run.sh

This will download, update to a point in time and create a set of geometric point, lines, multilinestrings, multipolygons and other_relations geojson objects filtered to contain rail related data.

## Dependencies

These are environment and project dependencies.

### Environment dependencies

Install the required OSM update and GDAL dependencies for the ogr2ogr tool

    $ sudo apt install osmctools gdal-bin

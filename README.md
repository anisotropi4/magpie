# GB Rail data

Open Street Map contains lots of data about the railway in mainland Britain. These scripts extract the full Open Street Map dataset and then filter for point associated with rail.

## Creating the datafiles and associate geojson format report

Once the dependencies to create the report are met run the script:

    $ ./run.sh

This will download, update to a point in time and create a set of geometric point, and line GeoPKG and geojson objects filtered to contain rail related data.

## Dependencies

These are environment and project dependencies.

### Environment dependencies

The required OSM dependencies for the `osmnx` and `geopandas` `python3` modules are installed by the `run.sh` script.


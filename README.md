# GB Rail data

[OpenStreetMap](https://www.openstreetmap.org) contains lots of data about the railway in mainland Britain and Ireland. The scripts in this project extract and filter data associated with rail from the full OpenStreetMap dataset.

## Creating the GeoPKG railway datafile

* Download an appropriate `osm.pbf` format file and copy into the `data` directory. The Britain and Ireland file from: [geofabrik](https://download.geofabrik.de/europe/britain-and-ireland.html) . 

* Run the script:

    $ ./run.sh

* This extracts associated geographic geometry in the GeoPKG `output/ine-rail.gpkg` file.

* Relevant rail related data and railway features, line speed and electrification scheme are derived based on metadata.

## Dependencies

These are environment and project dependencies.

### Environment dependencies

The required dependencies for the [`polars`](https://pola.rs), [`quackosm`](https://kraina-ai.github.io/quackosm) and [`GeoPandas`](https://geopandas.org) [`python3`](https://www.python.org) modules are installed by the `run.sh` script.

## License

The code and scripts ared under an [Apache 2.0 license](https://opensource.org/license/Apache-2.0). 

Any data derived from [OpenStreetMap](https://www.openstreetmap.org) is published under the [Open Data Commons Open Database License (ODbL)](https://www.openstreetmap.org/copyright), or where not applicable [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.en).

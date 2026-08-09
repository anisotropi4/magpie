# GB and Planet OSM Rail data

[OpenStreetMap (OSM)](https://www.openstreetmap.org) contains lots of data about the railway both for mainland Britain and Ireland but also the planet. The scripts in this project extract and filter data associated with rail from the full OSM dataset.

## Creating the GeoPKG railway datafile

* Download an appropriate `osm.pbf` format file and copy into the `data` directory. The Britain and Ireland file from: [Geofabrik](https://download.geofabrik.de/europe/britain-and-ireland.html). 

* Run the script to extracts associated geographic geometry into a GeoPKG file:

```
    $ ./run.sh
```

* This is `output/ine-rail.gpkg` and/or `output/planet-rail.gpkg`.
* Where relevant rail related data and railway features, line speed and electrification scheme are derived based on metadata.


### Notes on the Planet

* As [OSM](https://wiki.openstreetmap.org/wiki/Planet.osm) say: "Do not attempt to download the planet in a web browser." 

* There are altenative options documented in the [link](https://wiki.openstreetmap.org/wiki/Planet.osm) including cURL or bit torrent.

* The planet file is huge and processing the file is slow (over 90 minutes), and requires 200GB storage. 


## Dependencies

These are environment and project dependencies.

### Environment dependencies

The required dependencies for the [`polars`](https://pola.rs), [`quackosm`](https://kraina-ai.github.io/quackosm) and [`GeoPandas`](https://geopandas.org) [`python3`](https://www.python.org) modules are installed by the `run.sh` script.

The planet file also requires `osmconvert` tool to split the planet file into 24 segments.

### Planet dependencies
* These scripts were tested against `osmconvert` 0.8.1 from [`osmctools`](https://gitlab.com/osm-c-tools/osmctools). 

* Where the associated Debian apt package is installed as:

```
   $ sudo apt install osmctools
```


## License

The code and scripts ared under an [Apache 2.0 license](https://opensource.org/license/Apache-2.0). 

Any data derived from [OpenStreetMap](https://www.openstreetmap.org) is published under the [Open Data Commons Open Database License (ODbL)](https://www.openstreetmap.org/copyright), or where not applicable [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.en).

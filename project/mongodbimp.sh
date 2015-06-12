#!/bin/sh
python tojson.py
mongoimport --collection openstreet --file los-angeles_california.osm.json

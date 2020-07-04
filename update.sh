#!/bin/bash

CWD=$(pwd)
DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)

# migrate database
echo "Migration database ..."
rm -R $DIR/hotspot/migrations/*
python3 $DIR/manage.py makemigrations hotspot
python3 $DIR/manage.py migrate

# update static files
echo "Updating bower packages ..."
cd $DIR/hotspot/static
bower install

cd $CWD

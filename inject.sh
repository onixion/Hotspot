#!/bin/bash

CWD=$(pwd)
DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)

python3 $DIR/manage.py shell < $DIR/scripts/inject.py

cd $CMD

#!/bin/bash

CWD=$(pwd)
DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)

echo "Clearing database ..."

python3 $DIR/manage.py shell < $DIR/scripts/database_clear.py

cd $CMD

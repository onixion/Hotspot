#!/bin/bash

CWD=$(pwd)
DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)

export start_workers=True
python3 $DIR/manage.py runserver 8000

cd $DIR

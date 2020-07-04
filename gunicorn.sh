#!/bin/bash

NAME="hotspot"
DJANGODIR=/srv/http/hotspot
SOCKFILE=/srv/http/hotspot/gunicorn.sock
USER=gunicorn
GROUP=gunicorn
NUM_WORKERS=16
DJANGO_SETTINGS_MODULE=hotspot.settings
DJANGO_WSGI_MODULE=hotspot.wsgi

cd $DJANGODIR
source /srv/http/hotspot_env/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

exec /srv/http/hotspot_env/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user $USER \
  --bind=unix:$SOCKFILE

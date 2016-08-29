#!/usr/bin/env bash

VIRTUAL_ENV="/home/pi/flasktest/flask"
PATH="$VIRTUAL_ENV/bin:$PATH"
export PATH
export FLASK_APP=run.py
export FLASK_DEBUG=1

flask run --host=0.0.0.0

#!/bin/sh

if [ -f env_vars.sh ]; then
    . ./env_vars.sh
fi
python3 run.py

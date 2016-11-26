#!/bin/bash -x
virtualenv env
sed -i -e '1 s,^.*$,#!/usr/bin/env python,g' env/bin/pip
source env/bin/activate
pip install --target="$PWD" -r requirements.txt
deactivate
rm -rf env

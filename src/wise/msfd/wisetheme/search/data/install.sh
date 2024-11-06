#!/bin/sh
virtualenv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python importer.py

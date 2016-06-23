#!/bin/bash
echo "" > OpenstackOrchestrator.log
python3 gunicorn.py "$@"

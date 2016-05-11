#!/bin/bash
echo "" > FrogOrchestrator.log
python3 gunicorn.py

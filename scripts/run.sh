#!/bin/bash

echo "Iniciando aplicação..."

source venv/bin/activate

python -m gunicorn main:app --bind 0.0.0.0:8000
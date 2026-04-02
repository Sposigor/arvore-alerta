#!/bin/bash

python3 -m venv venv
source venv/bin/activate

#pip install -r requirements.txt

bash scripts/setup_db.sh
python scripts/create_admin.py
#!/bin/bash

# Script wrapper để chạy 4_visualization.py
# Chạy local vì không cần Spark cluster cho visualization

cd ~/massive_data_mining

export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Activate venv nếu có
if [ -d ~/mmds-venv ]; then
    source ~/mmds-venv/bin/activate
fi

python3 src/4_visualization.py "$@"

# Deactivate venv
if [ -d ~/mmds-venv ]; then
    deactivate
fi

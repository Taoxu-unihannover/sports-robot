#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
python -m pytest tests/test_execution_regression.py -q

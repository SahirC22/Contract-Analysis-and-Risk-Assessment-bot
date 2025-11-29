#!/bin/bash

# Set UTF-8 environment variables
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Run Streamlit app
streamlit run app.py

## python -X utf8 -m streamlit run app.py
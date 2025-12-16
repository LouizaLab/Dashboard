#!/bin/bash
# Quick script to run the Streamlit app

cd "$(dirname "$0")"
source venv/bin/activate
streamlit run app.py


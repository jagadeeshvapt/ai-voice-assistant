#!/bin/bash
# Quick run script

if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

MODE=${1:---text}

case $MODE in
    --text)
        python main.py --text
        ;;
    --voice)
        python main.py
        ;;
    --gui)
        python main.py --gui
        ;;
    --server)
        pip install fastapi uvicorn --quiet
        python server.py
        ;;
    --single)
        shift
        python main.py --single "$*"
        ;;
    *)
        python main.py --text
        ;;
esac

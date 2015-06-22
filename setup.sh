#!/bin/bash
HERE=$(dirname $0)

VENV_DIR="${HERE}/.venv"

if [ ! -d ${VENV_DIR} ]; then
    pyvenv ${VENV_DIR}
fi

export CC="gcc"
export CXX="g++"

source ${VENV_DIR}/bin/activate
pip install -r requirements.txt

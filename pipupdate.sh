#! /bin/sh

export CUSTOM_COMPILE_COMMAND=./pipupdate.sh
pip-compile --generate-hashes "${@}" --output-file requirements.txt

#!/bin/bash
pushd code
pipenv run python ./generate.py
popd

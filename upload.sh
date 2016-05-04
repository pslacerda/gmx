#!/bin/sh

PREV_VERSION=$(git tag | grep '[0-9]\+' | sort | tail -1)
CURR_VERSION=$(cat VERSION)
test $CURR_VERSION -gt $PREV_VERSION        &&
    git tag $CURR_VERSION                   &&
    git push --tags                         &&
    python3 setup.py register -r pypi       &&
    python3 setup.py sdist upload -r pypi   &&
    sed -i "s/VERSION =.*/VERSION = \'$CURR_VERSION\'/" setup.py
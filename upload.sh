#!/bin/sh

PREV_VERSION=$(git tag | grep '[0-9]\+' | sort | tail -1)
CURR_VERSION=$(cat VERSION)
test $CURR_VERSION -gt $PREV_VERSION        &&
    sed -i "s/VERSION =.*/VERSION = \'$CURR_VERSION\'/" setup.py &&
    git add setup.py VERSION                &&
    git commit -m "bump version"            &&
    git tag $CURR_VERSION                   &&
    git push --tags                         &&
    python3 setup.py register -r pypi       &&
    python3 setup.py sdist upload -r pypi

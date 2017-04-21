#!/bin/sh
htmlcovdir="htmlcov"
covfile=".coverage"

if [ -f "$covfile" ]; then
    echo "Removing previous .coverage file.."
    coverage erase
fi

echo "Running tests.."
coverage run -m unittest tests.test_utils
coverage run -am unittest tests.test_jobnotify
coverage html
coverage report -m

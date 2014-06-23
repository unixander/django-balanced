#!/bin/bash

py.test tests/ \
    --cov django_balanced \
    --cov-config .coveragerc \
    --cov-report term-missing \
    --pep8 django_balanced

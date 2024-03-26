## About 

This mini-package, accompanied by its corresponding analysis notebooks, constitutes material towards the fulfilment of requirements of the Individual Assignment (NWI-IND001).

_Author: Kruthi Krishna, Radboud University Nijmegen (March 2024)_

## Contents

#### lc_lmfit.py: 

Module containing various broken power law functions and their respective cost functions. See docstrings for more documentation.

#### swift_scrape.py: 

Module containing functions to scrape www.swift.ac.uk (modified version of code by Benjamin Gompertz)

#### analysis_notebooks/: 

Jupyter notebooks used for fitting EE-SGRBs and FXTs. See readme files in further folders for more documentation.

## Installation instructions for mini-package:

Step 1: Clone this repository

    git clone https://github.com/Kruthi24/fxt_code.git

Step 2: Activate the python environment where you want to install the package. For instance:

    conda activate <env_name>

Step 3: ```cd``` to the directory containing setup.py, then do:

    pip install .

Note: to install an editable version use ```pip install -e .```

## Using the mini-package

The package has two modules as of now: lc_lmfit and swift_scrape. These can be import as
    
    import lc_lmfit
    import swift_scrape


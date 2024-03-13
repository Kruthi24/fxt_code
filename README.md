# fxt_code

1. Scripts for FXT project bundled into a mini-package 
2. Jupyter notebooks used for analysis

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


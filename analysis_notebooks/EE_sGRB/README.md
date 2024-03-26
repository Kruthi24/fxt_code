## Contents

eegrb_fit_parameters.csv
- has parameters for n-broken power law fit for all GRBs

GRB_LC_X.ipynb
- notebook for fitting 'GRB X'

LC_swift_workbook.ipynb
- initial exploration notebook based on Jonathan Quirola-Vásquez notebook (LC_paper_I.ipynb)

afterglow_data/
- folder with X-ray afterglow data of all the GRBs

GRB_final_fits.ipynb
- contains final fit parameters compiled from "GRB_LC_X.ipynb" notebooks
- output: eegrb_fit_parameters.csv & plot

## Tutorial: How to get XRT data?

    import swift_scrape
    
    location = os.path.abspath('./afterglow_data/')+'/'
    
    GRBs=['050724', '051227', '060614', '061006', '061210', '070714B', '071227', '080123', '080503', '111121A', '150424A', '211211A', '211227A']
    
    swift_scrape.get_targetIDs(save=True, loc=location)
    
    for grb in GRBs:
        swift_scrape.get_batxrt(grb, loc=location)

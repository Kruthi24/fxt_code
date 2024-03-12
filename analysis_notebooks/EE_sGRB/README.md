## Contents
grb_bpl.csv
- has broken power law parameters for all GRBs

grb_initial_pl.csv
- has parameters for initial emission's powelaw fit for all GRBs

GRB_LC_X.ipynb
- notebook for fitting 'GRB X'

LC_swift_workbook.ipynb
- initial/exploration notebook

afterglow_data/
- folder with X-ray afterglow data of all the GRBs

## Tutorial: How to get XRT data?

    import swift_scrape

    GRBs=["050724","060614", "061210", "070714B", "071227", "150424A","211211A",
          "211227A", "051227","061006","080123","080503","090531B","111121A"]
          
    swift_scrape.get_targetIDs(save=True)
    
    for grb in GRBs:
      swift_scrape.get_xrt(grb,keep=True)

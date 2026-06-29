# Progress Report

5th TEAMx workshop, 17-19 June 2026, Trento

Hackathon: Reanalysis group
- Code and readme by: Dana Grund (dana.grund@ethz.ch)
- Support on data assimilation and file formats: Hendrik Reich (Hendrik.Reich@dwd.de)
- Point of contact for dacepy: Daniela Littmann (Daniela-Christin.Littmann@dwd.de)
- Plotting lidar data together with ICON: Giorgio Doglioni (giorgio.doglioni@unitn.it)

## Overview
The goal of this hackathon was to transform lidar data from IOPs 7 (and 8) into the raw observation file (ROF) format that is required to feed the data into the DWD data assimilation system KENDA, which makes use of the data  assimilation coding environment (dace). The KENDA system provides feedback files after the analysis, which is why 'feedback files' and 'ROF files' are equivalent terms in this project. DWD is recently developing dacepy, a python package to handle input and output of dace, however, the code is not yet pulic and documentation is lacking. Participants got access to the internal GitLab repository hosted at dkrz.

As the result of this hackathon, a script was created to convert lidar data for the KITcube stations of IOP7 to ROF format. The validity of the created files will be tested at DWD.

## Ressources
All data for the hackathon can be downloaded from https://fileshare.uibk.ac.at/d/e70f5b3e77af494d9cb1/

This group used `hackathon_data/wind_lidar/profiles_20250629_sIOP7/kitcube/` as the lidar data to be converted.

The following other ressources were available used for the hackathon: 
- `code/from_Annika_Oertel/example_DWL_rof.py`: A script converting some lidar data to ROF format with dacepy. However, the input file format seems to differ from the data we have.
- `documentation/` of KENDA feedback files (a special case of ROF) and dace
- `examples/rof_KIT_SWM2023_DL_PILOT_2023070103.nc`: a ROF file created in the Swabian MOSES campaign


## Progress summary
The following was developed:
- `code/hackathon/plot_windbarbs.py`: Plot lidar data. The resulting figures are in `results/plot_windbarbs/`.
- `code/hackathon/convert_KITcube_DWL_to_ROF_TEAMx.py`: Convert lidar data to ROF. The resulting files are in `results/rof_files/`
- `code/hackathon/hackathon_reanalysis_rof.ipynb`: A collection of code snippets to print, plot, and interact with the data and file formats.


## On the use of dacepy
Following the dacepy readme, this worked to install it (on Windows WSL Ubuntu): 

    deactivate # Deactivate venv if active
    conda create -n workshop python=3.11
    conda activate workshop
    conda install -c conda-forge netcdf4 gdal geos proj eccodes
    pip install dacepy

- There are many active branches. Here, we used only the main branch.
- We mainly used the `dp.create_fdbk()` function to write the feedback files and the functionality of the `FeedbackFile` class which is returned by `dp.create_fdbk()`.
- We found the native plotting functionality rather complicated to use and instead developed our own visualizations.

## On the use of generative AI for coding
The code in `code/hackathon` was created with claude code pro. While we made sure to check essential parts of the code, given the short time of the hackathon, we cannot guarantee that there are minor bugs left. If you plan to use it for production of scientific results, please have a careful read of the code first!

Claude was tasked to document the changes it made to the script by Annika Oertel in `documentation/MODIFICATION_SUMMARY_claude.md`.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modified processing script for KITCUBE Wind Lidar data (DWL profiles)
Adapted from: code/from_Annika_Oertel/example_DWL_rof.py

PURPOSE:
--------
Read netCDF wind profile data from multiple lidar stations and convert to 
dacepy feedback format (dp.create_fdbk()) for data assimilation.

KEY MODIFICATIONS FROM ORIGINAL:
--------------------------------
1. FILE DISCOVERY: 
   - Changed from date-based subdirectory pattern to direct glob in kitcube directory
   - Handles 14 .nc files (7 stations × 2 days)
   
2. STATION ID EXTRACTION:
   - Extracts from filename (WLS200s_115 → "115", HYB → "100", WTX → "101")
   - Removed hardcoded logic based on file path length
   
3. TIME HANDLING:
   - Epoch seconds converted to datetime64[s], then proper datetime64[ns] for pandas
   - Hourly grouping based on actual data timestamps (not hardcoded 24-hour loop)
   
4. HEIGHT CONVERSION:
   - Heights are absolute (above sea level) = profile height + station elevation
   - This is required by dp.create_fdbk()
   
5. DATA RESHAPING:
   - Flattens (ntimes, nheights) arrays properly for observation-based dataframe
   - Creates one row per (time, height, station) combination
   
6. OUTPUT FILES:
   - Hourly feedback files: TEAMX_DL_fdbk_YYYYMMDD_HH.nc
   - Saves to results/rof_files/

REQUIRED SIGNATURE FOR dp.create_fdbk():
---------------------------------------
DataFrame columns:
  - time: datetime64[ns]  - observation time
  - lat: float - latitude  - lon: float - longitude
  - level: float - absolute height above sea level (m)
  - varno: str - 'u' or 'v' (wind components)
  - obs: float - observation value (m/s)
  - z_station: int - station elevation (m)
  - statid: str - station identifier

Created on Thu Mar 23 15:32:14 2023
Modified: June 2026 for TeamX workshop

@author: Annika Oertel (original)
@modified_by: claude (2026-06-17)
"""

import glob
import os
import numpy as np
import netCDF4
from netCDF4 import Dataset
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt

import dacepy as dp
import pandas as pd
import xarray as xa


this_dir = os.path.dirname(os.path.abspath(__file__))

path2obs = os.path.join(this_dir, "../../data/hackathon_data/wind_lidar/profiles_20250629_sIOP7/kitcube")

fdbk_dir = os.path.join(this_dir, "../../results/rof_files")

# Create feedback directory if it doesn't exist
os.makedirs(fdbk_dir, exist_ok=True)

# ============================================================================
# DATE CONFIGURATION - Modify these to process different dates
# ============================================================================
# Process all available dates or specify specific dates
target_date = datetime(2025, 6, 29)  # Date to process
print(f"Processing date: {target_date.strftime('%Y-%m-%d')}")

# ============================================================================
# FILE DISCOVERY - Glob pattern to find all .nc files in the directory
# ============================================================================
# Get available files matching the wind profile pattern
filelist = sorted(glob.glob(os.path.join(path2obs, "*_600s_100m_wind_profile.nc")))

# Optionally filter by date if you have multiple dates
# filelist = [f for f in filelist if target_date.strftime("%Y%m%d") in f]

print(f"Found {len(filelist)} files to process:")
for f in filelist:
    print(f"  - {os.path.basename(f)}")


# only start post-processing script if files are found:
if len(filelist) > 0:
    # empty arrays to store all stations
    lon_vec, lat_vec, time_vec, z_station_vec, level_vec, varno_vec, obs_vec, z_station_vec, statid_vec, ltype_vec = [],[],[],[],[],[],[],[],[],[]

    print("start post-processing Wind Lidar files")

    NAV = -999.0 # NANs
         
    nstation = len(filelist) # number of stations

    for ii in np.arange(0, len(filelist)):
        print(f"\nProcessing file {ii+1}/{len(filelist)}: {os.path.basename(filelist[ii])}")
        obsnc = netCDF4.Dataset(filelist[ii])

        level = np.squeeze(obsnc.variables["height"]) # height above ground 
        z_station = np.squeeze(obsnc.variables["zsl"]) # station height (elevation above sea level)
        lon = np.squeeze(obsnc.variables["lon"])
        lat = np.squeeze(obsnc.variables["lat"])
        u = np.squeeze(obsnc.variables["u"])
        v = np.squeeze(obsnc.variables["v"])

        # ====================================================================
        # HEIGHT CONVERSION: Add station elevation to get absolute heights
        # ====================================================================
        # 'level' is height above ground in the file
        # We need absolute height (above sea level) for dp.create_fdbk()
        level = level + z_station # level is now above sea level (NN)
        
        # ====================================================================
        # STATION ID EXTRACTION from filename
        # ====================================================================
        # Extract station ID from filename
        # Examples: "WLS200s_115_20250629..." → "115"
        #          "HYB_20250629..." → "HYB"
        #          "WTX_20250629..." → "WTX"
        filename = os.path.basename(filelist[ii])
        
        if "WLS200s_" in filename:
            # Extract the number after "WLS200s_"
            parts = filename.split("_")
            statid_i = parts[1].zfill(3)  # Get "115", "124", etc. and pad to 3 digits
        elif "HYB_" in filename:
            statid_i = "100"  # Assign a standard ID for HYB
        elif "WTX_" in filename:
            statid_i = "101"  # Assign a standard ID for WTX
        else:
            statid_i = "999"  # Fallback for unknown station types
            
        print(f"  Station ID: {statid_i}, Location: ({lon:.2f}, {lat:.2f}), Elevation: {z_station}m")


        # ====================================================================
        # QUALITY CONTROL: Flag bad observations
        # ====================================================================
        u[u==NAV] = np.nan
        v[v==NAV] = np.nan

        # Check if quality variables exist and apply flags
        if "qu" in obsnc.variables and "qv" in obsnc.variables:
            qu = np.squeeze(obsnc.variables["qu"])
            qv = np.squeeze(obsnc.variables["qv"])
            # Set observations with quality flag = 0 to NaN
            u[qu==0] = np.nan
            v[qv==0] = np.nan
            print(f"  Quality flags applied: qu and qv")
        else:
            print(f"  Warning: No quality variables (qu, qv) found in file")

        # ====================================================================
        # TIME CONVERSION: Convert epoch seconds to datetime64
        # ====================================================================
        # time is in seconds since 1970-01-01 00:00:00 UTC
        time = np.squeeze(obsnc.variables["time"]) 
        # Convert to datetime64[s] for proper handling
        time64 = time.astype('datetime64[s]')
        
        print(f"  Time range: {time64[0]} to {time64[-1]}")
        print(f"  Data shapes - u: {u.shape}, v: {v.shape}, time: {time64.shape}, height: {level.shape}")

        
        # ====================================================================
        # DATA RESHAPING: Flatten and replicate data for DataFrame
        # ====================================================================
        # The u and v arrays have shape (ntimes, nheights)
        # We need to create one row per observation (time, height pair)
        
        z_station = np.round(z_station, 0).astype('int32')

        # Flatten u and v in C order (row-major): goes through all heights for first time, then all heights for second time
        u = u.ravel(order='C')
        v = v.ravel(order='C')
        
        # Combine u and v observations into single array
        obs = np.concatenate([u, v])
        
        # Create corresponding variable names ('u' or 'v')
        varno = np.repeat(['u', 'v'],
                         [u.shape[0], v.shape[0]])
        
        # Replicate time and height for both u and v observations
        # For each time step, we have multiple height levels
        # tile repeats the pattern, repeat duplicates each element
        time = np.tile(np.repeat(time64, level.shape[0]), 2)   # use shape of level from nc file
        level = np.tile(level, 2*time64.shape[0])              # use shape of time64 from nc file
        
        # Replicate scalar metadata for each observation
        lat = np.full(level.shape[0], lat)                     # use shape of level for df
        lon = np.full(level.shape[0], lon)                     # use shape of level for df
        z_station = np.full(level.shape[0], z_station)         # use shape of level for df
        statid = np.full(level.shape[0], statid_i)             # use shape of level for df
        leveltype = np.full(level.shape[0], "HEIGHT") 


        # append all stations to vector
        lon_vec = np.append(lon_vec, lon)
        lat_vec = np.append(lat_vec, lat)
        level_vec = np.append(level_vec, level)
        z_station_vec = np.append(z_station_vec, z_station)
        varno_vec = np.append(varno_vec, varno)
        obs_vec = np.append(obs_vec, obs)
        statid_vec = np.append(statid_vec, statid)
        ltype_vec = np.append(ltype_vec, leveltype)

        # time has special time format
        if ii == 0:
            time_vec = time
        else:
            time_vec = np.append(time_vec,time)



    # ========================================================================
    # HOURLY GROUPING AND FILE WRITING
    # ========================================================================
    # Group observations by hour and write separate feedback files
    
    # Determine the date range from the data
    if len(time_vec) > 0:
        min_time = pd.to_datetime(time_vec.min())
        max_time = pd.to_datetime(time_vec.max())
        data_date = min_time.date()
        
        print(f"\n{'='*70}")
        print(f"Data date: {data_date}")
        print(f"Time range: {min_time} to {max_time}")
        print(f"Total observations collected: {len(time_vec)}")
        print(f"{'='*70}\n")
    else:
        print("ERROR: No data collected!")
        exit()

    for utc in np.arange(0, 24, 1):
        print(f"Processing UTC {int(utc):02d}:00 - {int(utc)+1:02d}:00 (+ 1 minute for boundary measurements)")
        
        # Create filename
        filename_fdbk = f'TEAMX_DL_fdbk_{data_date.strftime("%Y%m%d")}_{str(utc).zfill(2)}'

        # Select observations for this hour
        # Extend to include measurements at the :00 mark of the next hour (e.g., 13:00 for hour 12)
        # This ensures each hourly file contains measurements spanning 10,20,30,40,50,60 minutes
        if utc == 23:
            # Last hour of the day (23:00 to next day 00:01)
            hour_start = datetime(data_date.year, data_date.month, data_date.day, 23, 0, 0)
            # Need to handle next-day boundary
            hour_end = datetime(data_date.year, data_date.month, data_date.day, 23, 0, 0) + timedelta(hours=1, minutes=1)
        else:
            hour_start = datetime(data_date.year, data_date.month, data_date.day, utc, 0, 0)
            hour_end = hour_start + timedelta(hours=1, minutes=1)  # Extend 1 minute to include :00 of next hour

        # Convert to pandas datetime64[ns] for comparison
        hour_start_dt64 = pd.Timestamp(hour_start)
        hour_end_dt64 = pd.Timestamp(hour_end)
        
        # Find indices for this hour (including measurements up to and including the :00 mark of next hour)
        time_vec_pd = pd.to_datetime(time_vec)
        tt_ind = np.where((time_vec_pd >= hour_start_dt64) & (time_vec_pd < hour_end_dt64))[0]
        print("time_vec_pd", time_vec_pd)
        print(f"  Found {len(tt_ind)} observations for UTC {str(utc).zfill(2)}:00")

        # Skip if no data for this hour
        if len(tt_ind) == 0:
            print(f"  -> Skipping (no data)")
            continue
        
        # ====================================================================
        # CREATE DATAFRAME for dp.create_fdbk()
        # ====================================================================
        df = pd.DataFrame(dict(
            time=time_vec[tt_ind].astype('datetime64[ns]'),    # Convert to nanoseconds for pandas
            lat=lat_vec[tt_ind],
            lon=lon_vec[tt_ind],
            level=level_vec[tt_ind],                           # Absolute height (above sea level)
            varno=varno_vec[tt_ind],                           # 'u' or 'v'
            obs=obs_vec[tt_ind],                               # Wind component values
            z_station=z_station_vec[tt_ind].astype("int"),     # Station elevation
            statid=statid_vec[tt_ind],                         # Station identifier
        ))

        # Remove NaN observations
        df = df.loc[df['obs'].notna()]
        print(f"  After QC (removing NaN): {len(df)} observations")
        
        # Remove observations at the start hour's 0-minute mark (keep only 10, 20, 30, 40, 50, 60 minutes)
        # Only remove 0-minute mark if it's in the start hour (utc)
        df = df[~((df['time'].dt.hour == utc) & (df['time'].dt.minute == 0))]
        print(f"  After removing {utc}:00 mark: {len(df)} observations")

        # Skip if no valid data after QC
        if len(df) == 0:
            print(f"  -> Skipping file creation (no valid data after QC)")
            continue

        # ====================================================================
        # WRITE FEEDBACK FILE using dacepy
        # ====================================================================
        print(f"  Writing feedback file: {filename_fdbk}.nc")
        try:
            # Create feedback object with instrument type 'PILOT' (for lidar)
            f = dp.create_fdbk('PILOT', df)
            
            # Write to netCDF
            output_path = os.path.join(fdbk_dir, filename_fdbk + ".nc")
            f.to_netcdf(output_path)
            print(f"  ✓ Successfully saved to: {output_path}")
        except Exception as e:
            print(f"  ✗ ERROR writing file: {e}")
            import traceback
            traceback.print_exc()




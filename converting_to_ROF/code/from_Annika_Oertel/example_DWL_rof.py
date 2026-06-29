#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 15:32:14 2023

@author: annika
"""

import glob, os
import numpy as np
import netCDF4
from netCDF4 import Dataset
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt

import dacepy as dp
import pandas as pd
import xarray as xa


#%%
path2obs = ""

#%%
fdbk_dir = ""


# 24-h delay
date = datetime.now() - timedelta(hours=24)
print(date)


# get available files 
filelist = []
for file in glob.glob(path2obs + date.strftime("%Y%m/") + "sups_inst_scantype*" + date.strftime("%Y%m%d") + "*"):
    print(file)    
    filelist = np.append(filelist, os.path.join(path2obs, file))   


filelist.sort()
filelist=sorted(filelist)


# only start post-processing script if files are found:
if len(filelist) > 0:
    # empty arrays to store all stations
    lon_vec, lat_vec, time_vec, z_station_vec, level_vec, varno_vec, obs_vec, z_station_vec, statid_vec, ltype_vec = [],[],[],[],[],[],[],[],[],[]

    print("start post-processing Wind Lidar files")

    NAV = -999.0 # NANs
         
    nstation = len(filelist) # number of stations

    for ii in np.arange(0,len(filelist)):
        print(ii, filelist[ii])
        obsnc = netCDF4.Dataset(filelist[ii])

        level = np.squeeze(obsnc.variables["height"]) # height above ground 
        z_station = np.squeeze(obsnc.variables["zsl"]) # station height
        lon = np.squeeze(obsnc.variables["lon"])
        lat = np.squeeze(obsnc.variables["lat"])
        u = np.squeeze(obsnc.variables["u"])
        v = np.squeeze(obsnc.variables["v"])

        level = level + z_station # level is above NN
        # extract station ID (!!account for different length of Doppler station names!!)
        if len(filelist[ii]) == 152:
            statid_i = str(103).zfill(3) 
        elif len(filelist[ii]) == 155:   
            statid_i = filelist[ii][148:151].zfill(3)
        elif len(filelist[ii]) == 157:
            statid_i = filelist[ii][151:154].zfill(3)
        elif len(filelist[ii]) == 149:
            statid_i = str(102).zfill(3)
        print(statid_i)


        u[u==NAV] = np.nan
        v[v==NAV] = np.nan

        qu = np.squeeze(obsnc.variables["qu"])
        qv = np.squeeze(obsnc.variables["qv"])

        u[qu==0] = np.nan
        v[qv==0] = np.nan

        time = np.squeeze(obsnc.variables["time"]) # time:units = "seconds since 1970-01-01 00:00:00" 
        time64 = np.round(time, 0).astype('datetime64[s]')

        z_station = np.round(z_station, 0).astype('int32')

        u = u.ravel(order='C')
        v = v.ravel(order='C')
        obs       = np.concatenate([u,          v])
        varno     = np.repeat     (['u',        'v'],
                                   [u.shape[0], v.shape[0]],
                                   )
        time      = np.tile(np.repeat(time64, level.shape[0]), 2)   # use shape of level from nc file
        level     = np.tile(level, 2*time64.shape[0])               # use shape of time64 from nc file
        lat       = np.full(level.shape[0], lat)                    # use shape of level for df
        lon       = np.full(level.shape[0], lon)                    # use shape of level for df
        z_station = np.full(level.shape[0], z_station)              # use shape of level for df
        statid    = np.full(level.shape[0], statid_i)               # use shape of level for df
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



    for utc in np.arange(0,24,1):
        print("write file for UTC ", int(utc+1), ' UTC' )
        filename_fdbk = 'KIT_SWM2023_DL_fdbk_' + datetime(date.year, date.month, date.day).strftime("%Y%m%d_") + str(utc + 1).zfill(2)

        # constrain date/time by current day and loop through hours; always assign to next full hour
        tt_ind = np.where((time_vec > datetime(date.year, date.month, date.day, utc) ) & (time_vec <= datetime(date.year, date.month, date.day, utc) + timedelta(hours=1)) )[0]
        print(len(tt_ind))

        if utc == 23:
            print("write file for UTC ", int(utc+1), ' UTC >> ' '00')
            filename_fdbk = 'KIT_SWM2023_DL_fdbk_' + (datetime(date.year, date.month, date.day,0) + timedelta(days=1)).strftime("%Y%m%d_") + str(0).zfill(2)

            tt_ind = np.where((time_vec > datetime(date.year, date.month, date.day, utc) ) & (time_vec <= datetime(date.year, date.month, date.day, 0) + timedelta(days=1) ) )[0]
            print(len(tt_ind))
        
        # write hourly feedback files
        df = pd.DataFrame(dict(time=time_vec[tt_ind].astype('datetime64[ns]'), # round to nanoseconds precision time to suppress pandas df warning
                               lat=lat_vec[tt_ind],
                               lon=lon_vec[tt_ind],
                               level=level_vec[tt_ind],
                               varno=varno_vec[tt_ind],
                               obs=obs_vec[tt_ind],
                               z_station=z_station_vec[tt_ind].astype("int"),
                               #ltype=ltype_vec[tt_ind],
                               statid=statid_vec[tt_ind],
                              ))

        df = df.loc[df['obs'].notna()] # drops NAs

        # write and save fdbk
        f=dp.create_fdbk('PILOT', df)
        f.to_netcdf(fdbk_dir+filename_fdbk+".nc")




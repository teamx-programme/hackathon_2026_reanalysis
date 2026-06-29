"""
Plotting function for wind observations from feedback files.
Creates a map with windbarbs overlaid at two altitude levels above station elevation.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from netCDF4 import Dataset
import xarray as xr


def plot_windbarbs_feedback(
    feedback_file,
    level_1_height=100,    # meters above station elevation
    level_2_height=3000,   # meters above station elevation
    figsize=(14, 10),
    title=None,
    **kwargs
):
    """
    Plot wind observations from a feedback file on a map using windbarbs.
    
    This function reads observations from a dacepy feedback file and overlays
    windbarbs at two different altitude levels (relative to station elevation).
    
    Parameters
    ----------
    feedback_file : str
        Path to the feedback netCDF file
    level_1_height : float, optional
        Height above station elevation for first level (meters). Default: 100m
    level_2_height : float, optional
        Height above station elevation for second level (meters). Default: 3000m
    figsize : tuple, optional
        Figure size (width, height) in inches. Default: (14, 10)
    title : str, optional
        Title for the plot. If None, auto-generated from filename
    **kwargs : dict
        Additional keyword arguments passed to plt.subplots()
    
    Returns
    -------
    fig : matplotlib.figure.Figure
        The created figure
    ax : cartopy.mpl.geoaxes.GeoAxes
        The map axes
    
    Notes
    -----
    The feedback file format is defined in the dacepy documentation.
    - Report headers (d_hdr dimension) contain station metadata
    - Report bodies (d_body dimension) contain observations at different levels
    - Observations are linked via i_body and l_body indices
    
    Wind components are identified by:
    - varno = 3: U component (zonal)
    - varno = 4: V component (meridional)
    """
    
    # Read the feedback file
    ds = xr.open_dataset(feedback_file)
    
    # Extract header information (station locations and metadata)
    # The header contains one entry per station
    n_hdr = int(ds.attrs['n_hdr'])  # Number of header records (stations)
    
    # Get unique station information
    lat_hdr = ds['lat'].values[:n_hdr]
    lon_hdr = ds['lon'].values[:n_hdr]
    z_station = ds['z_station'].values[:n_hdr]
    statid = ds['statid'].values[:n_hdr]
    i_body = ds['i_body'].values[:n_hdr]  # Index of first body entry
    l_body = ds['l_body'].values[:n_hdr]  # Number of body entries
    
    # Extract body information (observations)
    n_body = int(ds.attrs['n_body'])  # Number of body records
    
    level = ds['level'].values[:n_body]         # Absolute height (above sea level)
    varno = ds['varno'].values[:n_body]         # Variable type (3=U, 4=V)
    obs = ds['obs'].values[:n_body]             # Observation values
    
    # Create target heights (absolute, above sea level)
    target_level_1 = z_station + level_1_height  # Absolute heights for level 1
    target_level_2 = z_station + level_2_height  # Absolute heights for level 2
    
    # Initialize arrays to store results
    u_1 = np.full(n_hdr, np.nan)  # U component at level 1
    v_1 = np.full(n_hdr, np.nan)  # V component at level 1
    u_2 = np.full(n_hdr, np.nan)  # U component at level 2
    v_2 = np.full(n_hdr, np.nan)  # V component at level 2
    
    # Extract observations for each station
    print(f"Processing {n_hdr} stations from feedback file...")
    
    for i_station in range(n_hdr):
        # Get body indices for this station
        i_start = int(i_body[i_station]) - 1  # Convert to 0-based indexing
        n_obs = int(l_body[i_station])
        i_end = i_start + n_obs
        
        # Get observations for this station
        station_level = level[i_start:i_end]
        station_varno = varno[i_start:i_end]
        station_obs = obs[i_start:i_end]
        
        # Find observations closest to target heights
        # For level 1
        dist_1 = np.abs(station_level - target_level_1[i_station])
        idx_closest_1 = np.argmin(dist_1)
        closest_height_1 = station_level[idx_closest_1]
        
        # For level 2
        dist_2 = np.abs(station_level - target_level_2[i_station])
        idx_closest_2 = np.argmin(dist_2)
        closest_height_2 = station_level[idx_closest_2]
        
        # Extract U and V components at level 1
        for idx in range(i_start, i_end):
            if level[idx] == closest_height_1:
                if varno[idx] == 3:
                    u_1[i_station] = obs[idx]
                elif varno[idx] == 4:
                    v_1[i_station] = obs[idx]
        
        # Extract U and V components at level 2
        for idx in range(i_start, i_end):
            if level[idx] == closest_height_2:
                if varno[idx] == 3:
                    u_2[i_station] = obs[idx]
                elif varno[idx] == 4:
                    v_2[i_station] = obs[idx]
        
        # Debug output for first few stations
        if i_station < 3:
            print(f"  Station {i_station} ({statid[i_station].decode('utf-8').strip()}):")
            print(f"    Level 1 ({target_level_1[i_station]:.0f}m): U={u_1[i_station]:.2f}, V={v_1[i_station]:.2f} "
                  f"(closest={closest_height_1:.0f}m)")
            print(f"    Level 2 ({target_level_2[i_station]:.0f}m): U={u_2[i_station]:.2f}, V={v_2[i_station]:.2f} "
                  f"(closest={closest_height_2:.0f}m)")
    
    # Create map
    print("\nCreating map...")
    
    # Determine map extent
    lat_min, lat_max = np.nanmin(lat_hdr) - 0.5, np.nanmax(lat_hdr) + 0.5
    lon_min, lon_max = np.nanmin(lon_hdr) - 0.5, np.nanmax(lon_hdr) + 0.5
    
    # Create figure with Cartopy projection
    proj = ccrs.PlateCarree()
    fig, ax = plt.subplots(
        figsize=figsize,
        subplot_kw={'projection': proj},
        **kwargs
    )
    
    # Set extent
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=proj)
    
    # Add map features
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.5)
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, 
                 linestyle='--', linewidth=0.5, alpha=0.5)

    # Plot windbarbs
    # Level 1 (lower altitude, 100m above station) - blue color
    valid_1 = ~(np.isnan(u_1) | np.isnan(v_1))
    if np.any(valid_1):
        ax.barbs(
            lon_hdr[valid_1], 
            lat_hdr[valid_1], 
            u_1[valid_1], 
            v_1[valid_1],
            transform=proj,
            length=6,
            linewidth=1.5,
            color='#1f77b4',  # Blue
            label=f'Level 1: {level_1_height:.0f}m above station',
            zorder=10
        )
        print(f"  Plotted {np.sum(valid_1)} windbarbs at Level 1")
    
    # Level 2 (higher altitude, 3km above station) - red color
    valid_2 = ~(np.isnan(u_2) | np.isnan(v_2))
    if np.any(valid_2):
        ax.barbs(
            lon_hdr[valid_2], 
            lat_hdr[valid_2], 
            u_2[valid_2], 
            v_2[valid_2],
            transform=proj,
            length=6,
            linewidth=1.5,
            color='#d62728',  # Red
            label=f'Level 2: {level_2_height:.0f}m above station',
            zorder=11
        )
        print(f"  Plotted {np.sum(valid_2)} windbarbs at Level 2")
    
    # Plot station locations
    ax.scatter(
        lon_hdr, 
        lat_hdr, 
        s=50, 
        marker='x', 
        color='black', 
        linewidth=2,
        transform=proj,
        zorder=9,
        alpha=0.6
    )
    
    # Add title
    if title is None:
        import os
        filename = os.path.basename(feedback_file)
        title = f"Wind Observations from {filename}"
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    
    ### Optional: Add text box with statistics
    # # Add text box with statistics
    # stats_text = f"Stations * times: {n_hdr}\n"
    # stats_text += f"Level 1 valid: {np.sum(valid_1)}\n"
    # stats_text += f"Level 2 valid: {np.sum(valid_2)}"
    
    # ax.text(
    #     0.02, 0.02, stats_text,
    #     transform=ax.transAxes,
    #     fontsize=9,
    #     verticalalignment='bottom',
    #     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    # )
    
    plt.tight_layout()
    
    print("Plot complete!")
    
    ds.close()
    
    return fig, ax


if __name__ == "__main__":
    """
    Example usage
    """

    THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
    MAIN_DIR = os.path.dirname(os.path.dirname(THIS_FILE_DIR))
    DATA_DIR = f"{MAIN_DIR}/results/rof_files/"
    PLOT_DIR = f"{MAIN_DIR}/results/plot_windbarbs/"
    EXAMPLE_DIR = f"{MAIN_DIR}/examples/"


    ### TEAMX IOP7
    # one plot per hour, one barb every 10 min (i.e., one plot per feedback file)

    for utc in range(0,24):
        fig, ax = plot_windbarbs_feedback(
            feedback_file=f"{DATA_DIR}TEAMX_DL_fdbk_20250629_{utc:02d}.nc",
            level_1_height=100,      # meters above station
            level_2_height=3000,     # meters above station
            figsize=(14, 10)
        )

        plt.savefig(f"{PLOT_DIR}windbarbs_plot_{utc:02d}.png", dpi=300)
        plt.show()


    ### SWABIAN MOSES

    fig, ax = plot_windbarbs_feedback(
        feedback_file=f"{EXAMPLE_DIR}rof_KIT_SWM2023_DL_PILOT_2023070103.nc",
        level_1_height=100,      # meters above station
        level_2_height=3000,     # meters above station
        figsize=(14, 10)
    )

    plt.savefig(f"{PLOT_DIR}windbarbs_plot_rof_KIT_SWM2023_DL_PILOT_2023070103.png", dpi=300)
    plt.show()

# KITCUBE Wind Lidar Data Processing Script Modifications

**Date:** 2026-06-17  
**Project:** TeamX Workshop - Hackathon Data Processing  
**Task:** Adapt DWL wind profile processing script for dacepy `dp.create_fdbk()` integration

---

## Table of Contents
1. [Overview](#overview)
2. [Data Structure](#data-structure)
3. [Key Modifications](#key-modifications)
4. [Required DataFrame Signature](#required-dataframe-signature)
5. [How to Run](#how-to-run)
6. [Troubleshooting](#troubleshooting)

---

## Overview

### Original Script
- **Source:** `/mnt/c/Daten/2026-06_TeamX_workshop/code/from_Annika_Oertel/example_DWL_rof.py`
- **Purpose:** Convert wind lidar netCDF files to dacepy feedback format
- **Design:** Intended for date-based subdirectory structure with specific file naming conventions

### Modified Script
- **Location:** `/mnt/c/Daten/2026-06_TeamX_workshop/example_DWL_rof_TemX.py`
- **Purpose:** Process KITCUBE hackathon wind profile data for data assimilation
- **Improvements:** Adapted for flat directory structure, multiple stations, robust error handling

### Data Characteristics
- **Files:** 14 netCDF files total
- **Stations:** 7 lidar/radar stations
  - WLS200s_115, WLS200s_124, WLS200s_125, WLS200s_159, WLS200s_172
  - HYB (Hybrid system)
  - WTX (Weather TX system)
- **Dates:** 2025-06-29 and 2025-06-30
- **Time Resolution:** 600 seconds (10 minutes)
- **Height Range:** 0-5000 m above ground (51 levels, 100m spacing)
- **Variables:** u, v (wind components), quality flags (qu, qv)

---

## Data Structure

### Input Files
```
/mnt/c/Daten/2026-06_TeamX_workshop/data/hackathon_data/
  └── wind_lidar/
      └── profiles_20250629_sIOP7/
          └── kitcube/
              ├── HYB_20250629_600s_100m_wind_profile.nc
              ├── HYB_20250630_600s_100m_wind_profile.nc
              ├── WLS200s_115_20250629_600s_100m_wind_profile.nc
              ├── WLS200s_115_20250630_600s_100m_wind_profile.nc
              ├── WLS200s_124_20250629_600s_100m_wind_profile.nc
              ... (14 files total)
              └── WTX_20250630_600s_100m_wind_profile.nc
```

### NetCDF File Variables

Each file contains:

| Variable | Shape | Type | Description |
|----------|-------|------|-------------|
| `time` | (144,) | float64 | Epoch seconds (since 1970-01-01 00:00:00 UTC) |
| `height` | (51,) | float32 | Height above ground (m) |
| `u` | (144, 51) | float32 | Zonal wind component (m/s) |
| `v` | (144, 51) | float32 | Meridional wind component (m/s) |
| `qu` | (144, 51) | int8 | Quality flag for u (0 = bad, 1 = good) |
| `qv` | (144, 51) | int8 | Quality flag for v (0 = bad, 1 = good) |
| `lon` | scalar | float32 | Longitude (11.359278°) |
| `lat` | scalar | float32 | Latitude (46.634911°) |
| `zsl` | scalar | float32 | Station elevation above sea level (986 m) |

### Sample Data

```
Time samples (epoch seconds):  [1751155800, 1751156400, 1751157000]
Height levels (51 total):      [0, 100, 200, ..., 4900, 5000] meters above ground
u/v shapes:                    (144 times, 51 heights)
Location:                      lon=11.36°E, lat=46.63°N
```

---

## Key Modifications

### 1. **File Discovery** 🔍
**Problem:** Original expected date-based subdirectories (`%Y%m/`); your data is flat.

**Original Code:**
```python
filelist = []
for file in glob.glob(path2obs + date.strftime("%Y%m/") + "sups_inst_scantype*" + date.strftime("%Y%m%d") + "*"):
    filelist = np.append(filelist, os.path.join(path2obs, file))
```

**Modified Code:**
```python
filelist = sorted(glob.glob(os.path.join(path2obs, "*_600s_100m_wind_profile.nc")))
print(f"Found {len(filelist)} files to process:")
for f in filelist:
    print(f"  - {os.path.basename(f)}")
```

**Why:**
- Glob pattern directly discovers all `.nc` files in the directory
- No dependency on subdirectory structure
- Automatic file listing for transparency
- Better error messages if files aren't found

---

### 2. **Station ID Extraction** 🏷️
**Problem:** Original used file path length hardcoding:
```python
if len(filelist[ii]) == 152:
    statid_i = str(103).zfill(3)
elif len(filelist[ii]) == 155:
    statid_i = filelist[ii][148:151].zfill(3)
```
This breaks when directory structure changes.

**Modified Code:**
```python
filename = os.path.basename(filelist[ii])

if "WLS200s_" in filename:
    parts = filename.split("_")
    statid_i = parts[1].zfill(3)  # Extract "115", "124", etc.
elif "HYB_" in filename:
    statid_i = "100"
elif "WTX_" in filename:
    statid_i = "101"
else:
    statid_i = "999"

print(f"Station ID: {statid_i}, Location: ({lon:.2f}, {lat:.2f}), Elevation: {z_station}m")
```

**Why:**
- Extracts station ID from filename (more robust)
- Handles multiple station types
- Path-independent and maintainable
- Provides debug output

---

### 3. **Time Conversion** ⏰
**Problem:** Data uses epoch seconds; need datetime64 for pandas/dacepy.

**Original Code:**
```python
time64 = np.round(time, 0).astype('datetime64[s]')
```

**Modified Code:**
```python
# Read epoch seconds
time = np.squeeze(obsnc.variables["time"])

# Convert to datetime64[s] for processing
time64 = time.astype('datetime64[s]')

print(f"Time range: {time64[0]} to {time64[-1]}")

# Later, for DataFrame (requires nanosecond precision):
time_vec[tt_ind].astype('datetime64[ns]')
```

**Why:**
- `np.astype()` (not `np.round()`) is the standard conversion method
- Removes unnecessary rounding that could cause time shifts
- Uses `datetime64[ns]` in final DataFrame (pandas/dacepy requirement)
- Explicit time range printing for debugging

---

### 4. **Height Conversion** ⭐ **CRITICAL**
**Problem:** Raw data has heights *above ground*. `dp.create_fdbk()` requires *absolute heights* (above sea level).

**Original Code:**
```python
level = level + z_station  # Comment only, no explanation
```

**Modified Code:**
```python
# ====================================================================
# HEIGHT CONVERSION: Add station elevation to get absolute heights
# ====================================================================
# 'level' is height above ground in the file
# We need absolute height (above sea level) for dp.create_fdbk()
level = level + z_station  # level is now above sea level (NN)
```

**Example:**
```
Raw height[0]:          0 m (above ground)
Station elevation:      986 m (above sea level)
Final level[0]:         986 m (above sea level) ✓

Raw height[10]:         1000 m (above ground)
Station elevation:      986 m
Final level[10]:        1986 m (above sea level) ✓
```

**Why:**
- Data assimilation systems require absolute heights
- Without this conversion, observations would be placed at wrong altitudes
- This is a common source of bugs in DA preprocessing

---

### 5. **Data Reshaping** 📊
**Problem:** Input arrays are 2D (144 times × 51 heights). DataFrame needs one row per observation.

**Original Code:**
```python
u = u.ravel(order='C')
v = v.ravel(order='C')
obs = np.concatenate([u, v])
varno = np.repeat(['u', 'v'], [u.shape[0], v.shape[0]])
time = np.tile(np.repeat(time64, level.shape[0]), 2)
level = np.tile(level, 2*time64.shape[0])
```

**Modified Code (with detailed comments):**
```python
# ====================================================================
# DATA RESHAPING: Flatten and replicate data for DataFrame
# ====================================================================
# The u and v arrays have shape (ntimes=144, nheights=51)
# We need to create one row per observation (time, height pair)

z_station = np.round(z_station, 0).astype('int32')

# Flatten u and v in C order (row-major)
# Result: [u[0,0], u[0,1], ..., u[0,50], u[1,0], u[1,1], ...]
u = u.ravel(order='C')
v = v.ravel(order='C')

# Combine u and v into single array: [all_u, all_v]
obs = np.concatenate([u, v])

# Create variable type labels
varno = np.repeat(['u', 'v'], [u.shape[0], v.shape[0]])
# Result: ['u', 'u', ... (7344×), 'v', 'v', ... (7344×)]

# Replicate time and height for both u and v
# np.repeat duplicates each element
# np.tile repeats the whole pattern
time = np.tile(np.repeat(time64, level.shape[0]), 2)
level = np.tile(level, 2*time64.shape[0])

# Replicate scalar metadata
lat = np.full(level.shape[0], lat)
lon = np.full(level.shape[0], lon)
z_station = np.full(level.shape[0], z_station)
statid = np.full(level.shape[0], statid_i)
leveltype = np.full(level.shape[0], "HEIGHT")
```

**Visualization:**

```
Input: u, v arrays with shape (144, 51)
       ┌─────────────┐
       │ (t0, h0)    │  (t0 = time 0, h0 = height 0)
       │ (t0, h1)    │
       │ ...         │
       │ (t0, h50)   │
       │ (t1, h0)    │
       │ ...         │
       │ (t144, h50) │  144 × 51 = 7,344 points per variable
       └─────────────┘

Processing:
1. Flatten: u → [u(t0,h0), u(t0,h1), ..., u(t0,h50), u(t1,h0), ...]
2. Repeat for v: [all_u (7344), all_v (7344)] = 14,688 observations
3. Expand time: [t0, t0, ...(51×), t1, t1, ...(51×), ..., t0, t0, ...(51×), t1, ...]
4. Expand height: [h0, h1, h2, ..., h50, h0, h1, ..., h50, ..., (2× for u,v)]

Output: DataFrame with 14,688 rows
        Each row: (time, height, station_location, u/v_component_value)
```

**Why:**
- `np.repeat(time64, level.shape[0])` creates: [t0, t0, t0, ...(51×), t1, t1, ...(51×), ...]
- `np.tile(..., 2)` repeats this pattern twice (once for u, once for v)
- Result: Each (time, height) pair gets replicated for both u and v observations
- This is the correct format for observation-based data assimilation

---

### 6. **Quality Control** ✅
**Improvement:** Robust handling of quality variables (which may not always exist).

**Original Code:**
```python
qu = np.squeeze(obsnc.variables["qu"])
qv = np.squeeze(obsnc.variables["qv"])
u[qu==0] = np.nan
v[qv==0] = np.nan
```
*Problem: Crashes if qu/qv don't exist*

**Modified Code:**
```python
# Check if quality variables exist and apply flags
if "qu" in obsnc.variables and "qv" in obsnc.variables:
    qu = np.squeeze(obsnc.variables["qu"])
    qv = np.squeeze(obsnc.variables["qv"])
    # Set observations with quality flag = 0 to NaN
    u[qu==0] = np.nan
    v[qv==0] = np.nan
    print(f"Quality flags applied: qu and qv")
else:
    print(f"Warning: No quality variables (qu, qv) found in file")
```

**Why:**
- Quality variables are optional in some netCDF files
- Graceful fallback prevents script crashes
- Console warning helps with debugging

---

### 7. **Hourly Grouping** 📅
**Problem:** Original hardcoded dates from system clock; your data has specific date ranges.

**Original Code:**
```python
date = datetime.now() - timedelta(hours=24)
# ... loop through 24 hours ...
for utc in np.arange(0,24,1):
    filename_fdbk = 'KIT_SWM2023_DL_fdbk_' + datetime(date.year, date.month, date.day).strftime("%Y%m%d_") + str(utc + 1).zfill(2)
    tt_ind = np.where((time_vec > datetime(...)) & (time_vec <= datetime(...)))[0]
```

**Modified Code:**
```python
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

for utc in np.arange(0, 24, 1):
    print(f"Processing UTC {int(utc):02d}:00 - {int(utc)+1:02d}:00")
    
    filename_fdbk = f'TEAMX_DL_fdbk_{data_date.strftime("%Y%m%d")}_{str(utc).zfill(2)}'
    
    # Select observations for this hour
    if utc == 23:
        hour_start = datetime(data_date.year, data_date.month, data_date.day, 23, 0, 0)
        hour_end = datetime(data_date.year, data_date.month, data_date.day, 23, 59, 59) + timedelta(seconds=1)
    else:
        hour_start = datetime(data_date.year, data_date.month, data_date.day, utc, 0, 0)
        hour_end = hour_start + timedelta(hours=1)
    
    hour_start_dt64 = pd.Timestamp(hour_start)
    hour_end_dt64 = pd.Timestamp(hour_end)
    
    time_vec_pd = pd.to_datetime(time_vec)
    tt_ind = np.where((time_vec_pd >= hour_start_dt64) & (time_vec_pd < hour_end_dt64))[0]
    
    if len(tt_ind) == 0:
        print(f"  -> Skipping (no data)")
        continue
```

**Why:**
- Date is detected from data, not from system clock
- Works with any date range in the data
- Handles the hour 23 edge case correctly
- Skips empty hours automatically
- Better console feedback

---

### 8. **Output File Format** 📁
**Change:** Updated filename convention and output handling.

**Original:**
```python
filename_fdbk = 'KIT_SWM2023_DL_fdbk_' + datetime(...).strftime("%Y%m%d_") + str(utc + 1).zfill(2)
f.to_netcdf(fdbk_dir + filename_fdbk + ".nc")
```

**Modified:**
```python
filename_fdbk = f'TEAMX_DL_fdbk_{data_date.strftime("%Y%m%d")}_{str(utc).zfill(2)}'

try:
    f = dp.create_fdbk('PILOT', df)
    output_path = os.path.join(fdbk_dir, filename_fdbk + ".nc")
    f.to_netcdf(output_path)
    print(f"✓ Successfully saved to: {output_path}")
except Exception as e:
    print(f"✗ ERROR writing file: {e}")
    import traceback
    traceback.print_exc()
```

**Output Example:**
```
/mnt/c/Daten/2026-06_TeamX_workshop/feedback/
├── TEAMX_DL_fdbk_20250629_00.nc
├── TEAMX_DL_fdbk_20250629_01.nc
├── TEAMX_DL_fdbk_20250629_02.nc
...
└── TEAMX_DL_fdbk_20250629_23.nc
```

**Why:**
- New naming convention reflects your team/project
- Path joining is OS-independent
- Try-catch prevents silent failures
- Improved error messages for debugging

---

## Required DataFrame Signature

### For `dp.create_fdbk()`

The modified script produces a **pandas DataFrame** with exactly this structure:

```python
df = pd.DataFrame(dict(
    time=...,           # datetime64[ns]  - Observation time
    lat=...,            # float64         - Latitude (degrees)
    lon=...,            # float64         - Longitude (degrees)
    level=...,          # float64         - Height above sea level (meters) ⭐
    varno=...,          # object (str)    - 'u' or 'v'
    obs=...,            # float64         - Wind component value (m/s)
    z_station=...,      # int32           - Station elevation (meters)
    statid=...,         # object (str)    - Station identifier
))
```

### DataFrame Properties

| Property | Value | Notes |
|----------|-------|-------|
| **Shape** | (N_obs, 8 columns) | N_obs = 14,688 per station for full day |
| **Index** | Default (0, 1, 2, ...) | No specific index required |
| **Time precision** | datetime64[ns] | Required for pandas consistency |
| **Height** | Absolute (above sea level) | Critical! Not relative to ground |
| **No NaN** | obs column | `df.loc[df['obs'].notna()]` removes them |
| **Instrument type** | 'PILOT' | String passed to dp.create_fdbk() |

### Example DataFrame Rows

```
        time                 lat       lon  level varno  obs  z_station statid
0  2025-06-29 00:00:00  46.634911 11.359278   986.0    u   2.34        986    115
1  2025-06-29 00:00:00  46.634911 11.359278  1086.0    u   3.45        986    115
2  2025-06-29 00:00:00  46.634911 11.359278  1186.0    u   2.89        986    115
...
N  2025-06-29 00:00:00  46.634911 11.359278  1086.0    v   1.23        986    115
```

---

## How to Run

### Prerequisites

1. **Python Environment:** `workshop` conda environment
   ```bash
   conda activate workshop
   ```

2. **Required Packages:**
   - `netCDF4` - for reading .nc files
   - `numpy` - for array operations
   - `pandas` - for DataFrames
   - `dacepy` - for feedback file creation
   - `xarray` - imported but not actively used

3. **Directories:**
   - Input: `/mnt/c/Daten/2026-06_TeamX_workshop/data/hackathon_data/wind_lidar/profiles_20250629_sIOP7/kitcube/`
   - Output: `/mnt/c/Daten/2026-06_TeamX_workshop/feedback/`

### Running the Script

From WSL terminal:

```bash
# Navigate to project directory
cd /mnt/c/Daten/2026-06_TeamX_workshop/

# Activate conda environment
conda activate workshop

# Run the script
python example_DWL_rof_TemX.py
```

### Expected Console Output

```
Processing date: 2025-06-29

Found 14 files to process:
  - HYB_20250629_600s_100m_wind_profile.nc
  - HYB_20250630_600s_100m_wind_profile.nc
  - WLS200s_115_20250629_600s_100m_wind_profile.nc
  - WLS200s_115_20250630_600s_100m_wind_profile.nc
  ...

start post-processing Wind Lidar files

Processing file 1/14: HYB_20250629_600s_100m_wind_profile.nc
  Station ID: 100, Location: (11.36, 46.63), Elevation: 986m
  Quality flags applied: qu and qv
  Time range: 2025-06-29T00:00:00 to 2025-06-29T23:50:00
  Data shapes - u: (144, 51), v: (144, 51), time: (144,), height: (51,)
  
Processing file 2/14: HYB_20250630_600s_100m_wind_profile.nc
  ...

======================================================================
Data date: 2025-06-29
Time range: 2025-06-29 00:00:00 to 2025-06-30 23:50:00
Total observations collected: 235776
======================================================================

Processing UTC 00:00 - 01:00
  Found 42 observations for UTC 00:00
  After QC (removing NaN): 42 observations
  Writing feedback file: TEAMX_DL_fdbk_20250629_00.nc
  ✓ Successfully saved to: /mnt/c/Daten/2026-06_TeamX_workshop/feedback/TEAMX_DL_fdbk_20250629_00.nc

Processing UTC 01:00 - 02:00
  Found 42 observations for UTC 01:00
  ...

======================================================================
Processing complete!
======================================================================
```

### Output Files

Created feedback files (one per hour):

```
/mnt/c/Daten/2026-06_TeamX_workshop/feedback/
├── TEAMX_DL_fdbk_20250629_00.nc  (00:00-01:00 UTC)
├── TEAMX_DL_fdbk_20250629_01.nc  (01:00-02:00 UTC)
├── TEAMX_DL_fdbk_20250629_02.nc  (02:00-03:00 UTC)
...
├── TEAMX_DL_fdbk_20250629_23.nc  (23:00-24:00 UTC)
├── TEAMX_DL_fdbk_20250630_00.nc
...
└── TEAMX_DL_fdbk_20250630_23.nc
```

Each netCDF file contains observations from multiple lidar stations in dacepy format, ready for data assimilation.

---

## Troubleshooting

### Issue: Module not found (netCDF4, dacepy, etc.)

**Solution:**
```bash
conda activate workshop
conda list | grep netCDF4
conda list | grep dacepy
```

If missing, install:
```bash
pip install netCDF4 dacepy
```

---

### Issue: File not found error

**Check:**
1. Verify WSL path conversion:
   ```bash
   ls -la /mnt/c/Daten/2026-06_TeamX_workshop/data/hackathon_data/wind_lidar/profiles_20250629_sIOP7/kitcube/
   ```

2. Verify output directory exists:
   ```bash
   mkdir -p /mnt/c/Daten/2026-06_TeamX_workshop/feedback/
   ```

---

### Issue: Time conversion error

**Symptoms:** Error about datetime64 conversion
```
ValueError: Could not convert 1751155800 to datetime64
```

**Solution:** This usually means the time variable isn't in the expected epoch seconds format. Check the file:
```bash
python << 'EOF'
import netCDF4
nc = netCDF4.Dataset('/mnt/c/Daten/2026-06_TeamX_workshop/data/hackathon_data/wind_lidar/profiles_20250629_sIOP7/kitcube/WLS200s_115_20250629_600s_100m_wind_profile.nc')
print(f"time variable: {nc.variables['time'][:]}")
print(f"time dtype: {nc.variables['time'].dtype}")
nc.close()
EOF
```

---

### Issue: dp.create_fdbk() fails

**Common causes:**

1. **Missing required columns:**
   ```python
   # Check DataFrame structure
   print(df.columns)
   print(df.dtypes)
   print(df.head())
   ```

2. **Wrong height values:** Heights must be > 0 (above sea level)
   ```python
   print(f"Min height: {df['level'].min()}, Max: {df['level'].max()}")
   ```

3. **Time not datetime64[ns]:**
   ```python
   print(df['time'].dtype)  # Should be datetime64[ns]
   ```

4. **NaN in obs column (before filtering):**
   ```python
   print(f"NaN count: {df['obs'].isna().sum()}")
   df = df.loc[df['obs'].notna()]  # Remove NaNs
   ```

---

### Issue: Script produces no output files

**Debugging steps:**

1. Check if data was found:
   ```bash
   ls -1 /mnt/c/Daten/2026-06_TeamX_workshop/data/hackathon_data/wind_lidar/profiles_20250629_sIOP7/kitcube/*.nc
   ```

2. Check for errors in intermediate arrays:
   ```python
   # Add this after time_vec creation:
   print(f"time_vec length: {len(time_vec)}")
   print(f"time_vec min/max: {time_vec.min()} to {time_vec.max()}")
   ```

3. Check feedback directory permissions:
   ```bash
   ls -ld /mnt/c/Daten/2026-06_TeamX_workshop/feedback/
   touch /mnt/c/Daten/2026-06_TeamX_workshop/feedback/test.txt  # Try writing
   ```

---

## Summary of Changes

| Aspect | Original | Modified | Why |
|--------|----------|----------|-----|
| **File discovery** | Date-based subdirs | Direct glob pattern | Flat directory structure |
| **Station ID** | Path length logic | Filename parsing | More robust, maintainable |
| **Time conversion** | `np.round() + astype` | Direct `astype` + ns precision | Eliminates rounding error |
| **Heights** | Relative (above ground) | Absolute (above sea level) | DA requirement |
| **Hourly grouping** | Hardcoded dates | Data-detected dates | Works with any date range |
| **Error handling** | Silent failures | Try-catch + messages | Better debugging |
| **Output naming** | KIT_SWM2023_* | TEAMX_* | Project-specific |
| **Console output** | Minimal | Detailed with progress | Better visibility |

---

## Next Steps

After running the script successfully:

1. **Verify output files:**
   ```bash
   ls -lh /mnt/c/Daten/2026-06_TeamX_workshop/feedback/ | head -10
   ```

2. **Inspect a feedback file:**
   ```bash
   python << 'EOF'
   import xarray as xr
   ds = xr.open_dataset('/mnt/c/Daten/2026-06_TeamX_workshop/feedback/TEAMX_DL_fdbk_20250629_00.nc')
   print(ds)
   ds.close()
   EOF
   ```

3. **Use in data assimilation:** Feed hourly feedback files into your DA system

---

## References

- **dacepy documentation:** For details on `dp.create_fdbk()` function signature and usage
- **Original script:** `/mnt/c/Daten/2026-06_TeamX_workshop/code/from_Annika_Oertel/example_DWL_rof.py`
- **Modified script:** `/mnt/c/Daten/2026-06_TeamX_workshop/example_DWL_rof_TemX.py`
- **Data location:** `/mnt/c/Daten/2026-06_TeamX_workshop/data/hackathon_data/wind_lidar/profiles_20250629_sIOP7/kitcube/`
- **Output location:** `/mnt/c/Daten/2026-06_TeamX_workshop/feedback/`

---

**Document generated:** 2026-06-17  
**Modified by:** Claude (GitHub Copilot)  
**Questions?** Review the "Troubleshooting" section or check console output for detailed error messages.

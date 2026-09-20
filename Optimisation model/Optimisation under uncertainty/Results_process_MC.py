
import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter, FormatStrFormatter, MultipleLocator
import seaborn as sns

# Root folder
base_dir = "Results"

# Find Simulation folders
sim_folders = sorted(
    [f for f in os.listdir(base_dir)
     if os.path.isdir(os.path.join(base_dir, f)) and f.startswith("Simulation_")],
    key=lambda x: int(x.split("_")[-1])
)
print(f"Found {len(sim_folders)} simulation folders.")

datasets = []

for folder in sim_folders:
    folder_path = os.path.join(base_dir, folder)

    # Extract simulation index from folder name
    sim_idx = folder.split("_")[-1]

    # Construct filename
    nc_file = os.path.join(folder_path, f"model_results_{sim_idx}.nc")

    if os.path.exists(nc_file):
        print(f"Reading {nc_file}")
        ds = xr.open_dataset(nc_file, engine="h5netcdf")


        ds = ds.expand_dims(simulation=[int(sim_idx)])

        datasets.append(ds)
    else:
        print(f"Warning: file not found -> {nc_file}")

# Combine all datasets
if datasets:
    combined = xr.concat(datasets, dim="simulation")
    print("Datasets successfully combined.")

    # Optional save
    combined.to_netcdf("Configuration_1_combined_results.nc")

    print("Saved combined dataset.")
else:
    print("No datasets found.")
    
    
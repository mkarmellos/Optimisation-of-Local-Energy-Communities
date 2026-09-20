# -*- coding: utf-8 -*-


import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter, FormatStrFormatter, MultipleLocator
import seaborn as sns
import pandas as pd

# Ensure files are in the same directory
files = {
    "Configuration A": "Model_results_Configuration_A.nc",
    "Configuration B": "Model_results_Configuration_B.nc",
    "Configuration C": "Model_results_Configuration_C.nc",
    "Configuration D": "Model_results_Configuration_D.nc",
    "Configuration E": "Model_results_Configuration_E.nc",
}

flow_cap_list = []
storage_cap_list = []

for name, path in files.items():
    ds = xr.open_dataset(path, engine="h5netcdf")

    tech_options = ["Solar_PV", "Battery"]
    available_tech = [t for t in tech_options if t in ds.flow_cap.techs.values]

    carrier_options = ['Electricity', 'Solar_electricity']
    available_carrier = [c for c in carrier_options if c in ds.flow_cap.carriers.values]


    if not available_tech or not available_carrier:
        print(f"{name}: skipped (no matching tech/carrier)")
        continue

    flow_cap = (
        ds.flow_cap
        .sel(techs=available_tech, carriers=available_carrier)
        .sum(dim="carriers")
        )

    flow_cap_df = (
        flow_cap
        .to_dataframe(name="Flow Capacity [kW]")
        .reset_index()
    )
    
    flow_cap_df["Configuration"] = name
    
    flow_cap_df.rename(
        columns={
            "nodes": "Node",
            "techs": "Tech"
        },
        inplace=True
    )
    
    flow_cap_df = flow_cap_df[
        ["Configuration", "Node", "Tech", "Flow Capacity [kW]"]
    ]
    
    flow_cap_list.append(flow_cap_df)

    # --- STORAGE CAP ---
    storage_cap = (
        ds
        .storage_cap
        .sel(techs='Battery')
        .dropna(dim="nodes", how="all")
    )
    
    storage_cap_df = pd.DataFrame({
        "Configuration" : name,
        "Node" : storage_cap.nodes.values,
        "Tech" : storage_cap.techs.values,
        "Storage Capacity [kWh]": storage_cap.values
    })
        
    storage_cap_list.append(storage_cap_df)

flow_cap_df_all = pd.concat(flow_cap_list, ignore_index=True)
storage_cap_df_all = pd.concat(storage_cap_list, ignore_index=True)

flow_cap_table = (
    flow_cap_df_all
    .pivot_table(
        index=["Node", "Tech"],
        columns="Configuration",
        values="Flow Capacity [kW]",
        fill_value=0
    )
    .reset_index()
)

storage_cap_table = (
    storage_cap_df_all
    .pivot_table(
        index=["Node"],   
        columns="Configuration",
        values="Storage Capacity [kWh]",
        fill_value=0
    )
    .reset_index()
)

all_configs = list(files.keys())  

all_techs = flow_cap_df_all["Tech"].unique()

flow_cap_table = (
    flow_cap_df_all
    .pivot_table(
        index="Node",
        columns=["Configuration", "Tech"],
        values="Flow Capacity [kW]",
        fill_value=0
    )

)

flow_cap_table.to_csv('Flow Capacity per Node and Tech Table.csv')

storage_cap_table = (
    storage_cap_df_all
    .pivot_table(
        index="Node",
        columns=["Configuration", "Tech"],
        values="Storage Capacity [kWh]",
        fill_value=0
    )
)

storage_cap_table.to_csv('Storage Capacity per Node and Tech Table.csv')


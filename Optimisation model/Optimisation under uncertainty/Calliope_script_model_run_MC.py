# -*- coding: utf-8 -*-

import calliope
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyproj
from pathlib import Path
import os
import xarray as xr
import logging
import time

# Configure logging
logging.basicConfig(
    filename="runtime.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

start = time.perf_counter()

#%% Plotting Section
pio.renderers.default = "json"

OUTDIR = Path("Results") 
OUTDIR.mkdir(exist_ok=True)

demand_original = "demand_original.csv"
export_flow_original = "export_availability_original.csv"


data_dir = "data_tables"
n_runs = 1000
p_curtail = 0.25  # probability export flow is limited

rng = np.random.default_rng()

# =========================
# Monte Carlo
# =========================
for k in range(n_runs):    
    
    results_dir = OUTDIR / f'Simulation_{k}' 
    results_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = results_dir / f"Plots_{k}"
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nRUNNING SCENARIO: {k+1}/{n_runs}\n")


    demand_original_data = pd.read_csv(
        demand_original,
        header=[0, 1],          
        index_col=0,
        parse_dates=True
    )

    export_limit = pd.read_csv(
        export_flow_original,
        header=0,              
        index_col=0,
        parse_dates=True
    )


    export_limit_col = export_limit.columns[0]

    # =====================
    # PV CURTAILMENT
    # =====================
    hours = export_limit.index.hour
    days = export_limit.index.normalize()

    unique_days = pd.unique(days)
    day_index = pd.Series(range(len(unique_days)), index=unique_days)
    d_idx = days.map(day_index).values

    Z = rng.binomial(1, 1-p_curtail, size=len(unique_days))

    mask = (hours >= 9) & (hours < 16)

    export_limit.loc[mask, export_limit_col] = (
        export_limit.loc[mask, export_limit_col].values *
        Z[d_idx[mask]]
    )

    # =====================
    # DEMAND UNCERTAINTY
    # =====================

    factor = rng.normal(1.0, 0.03)
    factor = np.maximum(factor, 0)   # ensure non-negative


    demand = demand_original_data * factor

    # =====================
    # ELECTRICITY PRICE (parameter)
    # =====================
    price = rng.triangular(0.8, 1.2, 1.4)
   
    # =====================
    # SAVE TO data_tables
    # =====================
    demand.to_csv(os.path.join(data_dir, "demand.csv"))
    export_limit.to_csv(os.path.join(data_dir, "export_availability.csv"))
    
    # =====================
    # Model
    # =====================    
    calliope.set_log_verbosity("INFO", include_solver_output=True)
    
    grid_residential_price_cost = price*0.2652
    grid_commercial_price_cost = price*0.2664
    cost_export_price = price * (-0.11)

  # parameters names might differ across configurations
    parameters_dict = {
                   'nodes.R1.techs.Grid_supply.cost_flow_in.data' : grid_residential_price_cost,
                   'nodes.R2.techs.Grid_supply.cost_flow_in.data' : grid_residential_price_cost,
                   'nodes.R3.techs.Grid_supply.cost_flow_in.data' : grid_residential_price_cost,
                   'nodes.R4.techs.Grid_supply.cost_flow_in.data' : grid_residential_price_cost,
                   'nodes.R5.techs.Grid_supply.cost_flow_in.data' : grid_residential_price_cost,
                   'nodes.R6.techs.Grid_supply.cost_flow_in.data' : grid_residential_price_cost,
                   'nodes.C1.techs.Grid_supply.cost_flow_in.data' : grid_commercial_price_cost,
                   'nodes.C2.techs.Grid_supply.cost_flow_in.data' : grid_commercial_price_cost,
                   'techs.EC_Solar_PV_supply.cost_export.data' : cost_export_price}
    
    model = calliope.read_yaml('model_scen5.yaml', override_dict=parameters_dict)
        
    model.build()
    model.solve()
    
    ds_res = model.results
    ds_res.to_netcdf(results_dir/f"model_results_{k}.nc", engine="h5netcdf")

    model.to_csv(results_dir/f'EC_model_S5_{k}')

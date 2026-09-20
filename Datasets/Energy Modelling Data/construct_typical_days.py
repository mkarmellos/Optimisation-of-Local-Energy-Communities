# -*- coding: utf-8 -*-

import pandas as pd
import os
from pathlib import Path
from sys import exit
import matplotlib.pyplot as plt
import copy
import tsam

# Construct typical days
date_range = pd.date_range(start='2021-01-01', end='2021-12-31 23:00:00', freq='1h')

energy_demand_residential_year = pd.read_csv('Residential Loads.csv', index_col=0)
energy_demand_residential_year.columns = [
    f"Residential_Electricity_Load_{col}"
    for col in energy_demand_residential_year.columns
]
energy_demand_residential_year.set_index(date_range, inplace=True)

energy_demand_commercial_year = pd.read_csv('Commercial Loads.csv', index_col=0)
energy_demand_commercial_year.columns = [
    f"Small_Commercial_Electricity_Load_{col}"
    for col in energy_demand_commercial_year.columns
]
energy_demand_commercial_year.set_index(date_range, inplace=True)

pv_cf = pd.read_csv('Solar PV capacity factor.csv', index_col=0)
pv_cf.set_index(date_range, inplace=True)

availability = pd.read_csv('Availability.csv', index_col=0)
availability.columns = [
    f"Availability_{col}"
    for col in availability.columns
]
availability.set_index(date_range, inplace=True)

ev_demand = pd.read_csv('Mobility_EVs.csv', index_col=0)
ev_demand.columns = [
    f"EV_Demand_{col}"
    for col in ev_demand.columns
]
ev_demand.set_index(date_range, inplace=True)

original_data = pd.concat([energy_demand_residential_year, energy_demand_commercial_year, pv_cf, availability, ev_demand], axis=1)
original_data.index.name = 'Datetime'


aggregated_data = tsam.aggregate(original_data,
                                  n_clusters  = 12,
                                  period_duration = '1D',
                                  cluster=tsam.ClusterConfig(method='kmedoids')
    )
aggregated_data_cluster_counts  = aggregated_data.cluster_counts 
aggregated_data_clusters  = aggregated_data.cluster_assignments  
typPeriods = aggregated_data.cluster_representatives

typPeriods.to_csv('typPeriods.csv')


accuracyIndicators = aggregated_data.accuracy

# Indices of the original days selected as cluster centers
centers = list(aggregated_data.clustering.cluster_centers)


representative_dates = (
    original_data
    .resample("1D")
    .first()
    .iloc[centers]
    .index
    .date
)

representative_dates_df = pd.DataFrame(
    representative_dates,
    columns=["Representative Date"]
)

representative_dates_df.to_csv(
    "Representative Dates.csv",
    index=False
)

# ---------------------------------------------------------
# Map every original day to its representative date
# ---------------------------------------------------------

daily_data = original_data.resample("1D").first()

cluster_days = pd.Series(
    [
        representative_dates[int(cluster)]
        for cluster in aggregated_data.cluster_assignments
    ],
    index=daily_data.index,
    name="Representative Date"
)

cluster_days.index = cluster_days.index.date

cluster_days.to_csv("cluster_days.csv")

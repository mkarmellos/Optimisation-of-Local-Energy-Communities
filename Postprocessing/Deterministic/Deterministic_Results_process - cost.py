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

total_cost_list = []
levelised_cost_list = []
total_cost_node_list = []

for name, path in files.items():
    ds = xr.open_dataset(path, engine="h5netcdf")
    
    total_cost = ds.min_cost_optimisation.values.item()
    total_cost_df = pd.DataFrame({
        "Configuration": [name],
        "Total Annualised Cost [€]": [total_cost]
    })    
    total_cost_list.append(total_cost_df)
    
    levelised_cost = (
        ds.total_levelised_cost
        .sel(costs='monetary',carriers='Electricity')
        .values
        .item()
        )
    levelised_cost_df = pd.DataFrame({
        "Configuration": [name],
        "Total levelised cost - Electricity [€/kWh]": [levelised_cost]
    })
    levelised_cost_list.append(levelised_cost_df)
    
    nodes_names = ds.cost["nodes"].values
    
    total_cost_node = (
        ds.cost
        .sel(costs='monetary')
        .sum(dim="techs")
        .values
        )
    total_cost_node_df = pd.DataFrame({
        "Configuration" : [name] * len(nodes_names),
        "Node": nodes_names,
        "Total Annualised Cost per Node [€]": total_cost_node
    })
    total_cost_node_list.append(total_cost_node_df)



total_cost_df_all = pd.concat(total_cost_list, ignore_index=True)
total_cost_df_all.to_csv('Total_Annual_Cost - Configuration.csv')

levelised_cost_df_all = pd.concat(levelised_cost_list, ignore_index=True)
levelised_cost_df_all.to_csv('Levelised_Electricity_Cost - Configuration.csv')

total_cost_node_df_all = pd.concat(total_cost_node_list, ignore_index=True)
total_cost_node_df_all.to_csv('Total Cost per Node - Configuration.csv')

total_cost_node_df_all_table = total_cost_node_df_all.pivot(
    index="Configuration",
    columns="Node",
    values="Total Annualised Cost per Node [€]"
)
total_cost_node_df_all_table.to_csv('Total Cost per Node - Configuration Table.csv')

## Plot TAC and levelised cost  

fig, ax1 = plt.subplots(figsize = (10, 6), dpi = 600)
sns.barplot(
    x=total_cost_df_all.columns[0],
    y=total_cost_df_all.columns[1],
    data=total_cost_df_all,
    ax=ax1,
    label=total_cost_df_all.columns[1],
    legend=False
    )
ax1.set_ylabel(total_cost_df_all.columns[1])
ax1.tick_params(axis='y')
ax1.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))


ax2 = ax1.twinx()
sns.scatterplot(
    data=levelised_cost_df_all,
    x=levelised_cost_df_all.columns[0],
    y=levelised_cost_df_all.columns[1],
    marker='o',
    color='#f42111',
    label=levelised_cost_df_all.columns[1],
    legend=False
    )

ax2.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
ax2.yaxis.set_minor_locator(MultipleLocator(0.005))

ax2.set_ylabel(levelised_cost_df_all.columns[1])
ax2.tick_params(axis='y')



handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()

ax1.legend(handles1 + handles2, labels1 + labels2, loc='best')

plt.tight_layout()
plt.savefig('Deterministic Results.png')
plt.close()

# Drop T node for plotting relevant node plots
total_cost_node_df_all_table_filter = total_cost_node_df_all_table.drop(columns="T")

## Plot node cost heat map

fig, ax1 = plt.subplots(figsize = (10, 6), dpi = 600)

hm = sns.heatmap(
    total_cost_node_df_all_table_filter,
    annot=True,
    fmt=",.0f",
    cmap="viridis"
#    cbar_kws={"label": "Cost (€)"}
    )

cbar = hm.collections[0].colorbar
cbar.ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

plt.title("Total Annualised Cost per Node (€)")
plt.xlabel("Node")
plt.ylabel("Configuration")

plt.tight_layout()
plt.savefig('Cost by Node - Configuration - Heatmap.png')
plt.close()

## Plot node cost heat map with T

fig, ax1 = plt.subplots(figsize = (10, 6), dpi = 600)

hm = sns.heatmap(
    total_cost_node_df_all_table,
    annot=True,
    fmt=",.0f",
    cmap="viridis"
    )

cbar = hm.collections[0].colorbar
cbar.ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

plt.title("Total Annualised Cost per Node (€)")
plt.xlabel("Node")
plt.ylabel("Configuration")

plt.tight_layout()
plt.savefig('Cost by Node - Configuration - Heatmap - all nodes.png')
plt.close()


## Plot node cost stacked bar
fig, ax1 = plt.subplots(figsize = (10, 6), dpi = 600)
total_cost_node_df_all_table_filter.plot(
    kind="bar",
    stacked=True,
    figsize=(10, 6)
)

plt.ylabel("Total Annualised Cost (€)")
plt.title("Cost Breakdown per Configuration")
plt.legend(title="Node", bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.savefig('Cost by Node - Configuration - Stacked bar.png')
plt.close()

## Plot node groubed bar chart
fig, ax1 = plt.subplots(figsize = (10, 6), dpi = 600)

total_cost_node_df_all_table_filter.T.plot(
    kind="bar",
    figsize=(10, 6)
)

plt.ylabel("Total Annualised Cost (€)")
plt.title("Node-wise Cost Comparison")
plt.legend(title="Configuration", bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.savefig('Cost by Node - Configuration - Grouped bar.png')
plt.close()
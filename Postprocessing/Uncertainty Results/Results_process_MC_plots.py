import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter, FormatStrFormatter, MultipleLocator
import seaborn as sns
import pandas as pd


model_path = #insert the path of the main folder having the potential configurations

file_configuration_a = os.path.join(
    model_path, #path with file as .nc format)
file_configuration_b = os.path.join(
    model_path, #path with file as .nc format)
file_configuration_c = os.path.join(
    model_path, #path with file as .nc format)
file_configuration_d = os.path.join(
    model_path, #path with file as .nc format)
file_configuration_e = os.path.join(
    model_path, #path with file as .nc format)

files = {
    "Configuration A": file_configuration_a,
    "Configuration B": file_configuration_b,
    "Configuration C": file_configuration_c,
    "Configuration D": file_configuration_d,
    "Configuration E": file_configuration_e,
}


total_cost_list = []
solar_pv_list = []
battery_capacity_list = []

for name, path in files.items():
    ds = xr.open_dataset(path, engine="h5netcdf")

    total_cost = ds.min_cost_optimisation.values
    total_cost_df = pd.DataFrame({
        "Total Cost": total_cost,
        "Configuration": name
    })    
    total_cost_list.append(total_cost_df)
    
    
    ## Cost plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=600)

    # histogram (primary axis)

    sns.histplot(
        
        data=total_cost_df,
        x="Total Cost",
        stat="count",     # or "density"
        common_norm=False,
        ax=ax1
    )

    
    sns.histplot(
        data=total_cost_df,
        x="Total Cost",
        stat='density',
        element='step',
        cumulative=True,
        legend=False,
        color='red',
        fill=False,
        ax=ax2
    )
    
    ax2.set_ylabel("Cumulative probability")

    ax1.set_xlabel("Total Annual Cost [€]")
    ax1.set_ylabel("Frequency")
    ax1.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    
    plt.title(f"Total Annual Cost Histogram - {name}")
    plt.tight_layout()
    plt.savefig(f"Total Annual Cost Histogram - {name}.png")
    plt.close()
 
    # Solar
    if "flow_cap" in ds:
        tech_options = ["Solar_PV", "EC_Solar_PV_supply"]
        available = [t for t in tech_options if t in ds.flow_cap.techs.values]
    
        if available:
            tech_name = available[0]
    
            solar_capacity = (
                ds.flow_cap
                .sel(techs=tech_name)
                .sum(dim=("nodes", "carriers"))
                .values
            )
    
            solar_capacity_df = pd.DataFrame({
                "Solar PV": solar_capacity,
                "Configuration": name
            })    
            solar_pv_list.append(solar_capacity_df)
    
            # plot
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=600)
            
            sns.histplot(
                data=solar_capacity_df,
                x="Solar PV",
                stat="count",
                common_norm=False,
                ax=ax1
            )  
            ax1.set_xlabel("Solar PV Capacity [kW]")
            ax1.set_ylabel("Frequency")
            
            
            sns.histplot(
                data=solar_capacity_df,
                x="Solar PV",
                stat='density',
                element='step',
                cumulative=True,
                legend=False,
                color='red',
                fill=False,
                ax=ax2
            )
            
            ax2.set_ylabel("Cumulative probability")
            
            plt.title(f"Solar PV Capacity Histogram - {name}")
            plt.tight_layout()
            plt.savefig(f"Solar PV Capacity Histogram - {name}.png")
            plt.close()
    
        else:
            print(f"Skipping Solar for {name} (tech not found)")
    else:
        print(f"Skipping Solar for {name} (flow_cap missing)")
     
 
  # Battery 
    if "storage_cap" in ds and "Battery" in ds.storage_cap.techs.values:
        
        battery_capacity = (
            ds.storage_cap
            .sel(techs="Battery")
            .sum(dim="nodes")
            .values
        )
    
        battery_capacity_df = pd.DataFrame({
            "Battery Capacity": battery_capacity,
            "Configuration": name
        })    
        battery_capacity_list.append(battery_capacity_df)
    
        # plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=600)
    
        sns.histplot(
            data=battery_capacity_df,
            x="Battery Capacity",
            stat="count",
            common_norm=False,
            discrete=True,
            ax=ax1
        )
    
        ax1.set_xlabel("Storage Capacity [kWh]")
        ax1.set_ylabel("Frequency")
        ax1.set_xlim(0, None)
        

        sns.histplot(
            data=battery_capacity_df,
            x="Battery Capacity",
            stat='density',
            element='step',
            cumulative=True,
            legend=False,
            fill=False,
            color='red',
            ax=ax2
        )
            
        
        ax2.set_ylabel("Cumulative probability")    
        
        plt.title(f"Storage Capacity Histogram - {name}")
        plt.tight_layout()
        plt.savefig(f"Storage Capacity Histogram  - {name}.png")
        plt.close()
    
    else:
        print(f"Skipping Battery for {name} (not available)")
    

total_cost_df_all = pd.concat(total_cost_list, ignore_index=True)
solar_pv_df_all = pd.concat(solar_pv_list, ignore_index=True)
battery_capacity_df_all = pd.concat(battery_capacity_list, ignore_index=True)

solar_pv_df_all.columns


#---------------
## Group plots
#---------------


# Solar plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=600)



sns.histplot(
    data=solar_pv_df_all,
    x="Solar PV",
    hue="Configuration",
    stat="count",     
    element="step",   
    common_norm=False,
    ax=ax1
)

ax1.set_xlabel("Total Solar PV Capacity [kW]")
ax1.set_ylabel("Frequency")
ax1.set_title("Solar PV Capacity Histogram - Frequency", loc='center')

sns.histplot(
    data=solar_pv_df_all,
    x="Solar PV",
    hue="Configuration",
    stat="density",
    element="step",     
    common_norm=False,
    cumulative=True,
    legend=True,
    fill=False,
    ax=ax2
)

ax2.set_ylabel("Cumulative probability")  
ax2.set_xlabel("Total Solar PV Capacity [kW]")
ax2.set_title("Solar PV Capacity Histogram - Density", loc='center')
    

plt.tight_layout()
plt.savefig("Solar PV Capacity Histogram.png")
plt.close()

## Battery Histogram

# plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=600)

# histogram (primary axis)
sns.histplot(
    data=battery_capacity_df_all,
    x="Battery Capacity",
    hue="Configuration",
    stat="count",     
    element="step",   
    common_norm=False,
    ax=ax1
)
ax1.set_xlabel("Storage Capacity [kWh]")
ax1.set_ylabel("Frequency")
ax1.set_title("Storage Capacity Histogram - Frequency", loc='center')


sns.histplot(
    data=battery_capacity_df_all,
    x="Battery Capacity",
    hue="Configuration",
    stat="density",
    element="step",
    common_norm=False,
    cumulative=True,
    legend=True,
    fill=False,
    ax=ax2
)

ax2.set_ylabel("Cumulative probability") 
ax2.set_xlabel("Storage Capacity [kWh]") 
ax2.set_title("Storage Capacity Histogram - Density", loc='center')

    
plt.tight_layout()
plt.savefig("Storage Capacity Histogram.png")
plt.close()


#---------------
## Cost plot
#---------------

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=600)

sns.histplot(
    data=total_cost_df_all,
    x="Total Cost",
    hue="Configuration",
    stat="count",
    element="step",
    common_norm=False,
    ax=ax1
)

ax1.set_xlabel("Total Annual Cost [€]")
ax1.set_ylabel("Frequency")
ax1.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
ax1.set_title("Total Annual Cost Histogram - Frequency", loc='center')


sns.histplot(
    data=total_cost_df_all,
    x=total_cost_df_all['Total Cost'],
    hue="Configuration",
    stat="density",
    element="step",     
    common_norm=False,
    cumulative=True,
    legend=True,
    fill=False,
    ax=ax2
)

ax2.set_ylabel("Cumulative probability")
ax2.set_xlabel("Total Annual Cost [€]")
ax2.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
ax2.set_title("Total Annual Cost Histogram - Density", loc='center')

plt.tight_layout()
plt.savefig("Total Annual Cost Histogram.png", bbox_inches="tight")
plt.close()


#---------------
## Density plots
#---------------


# Cost plot


fig, ax1 = plt.subplots(figsize=(10, 6), dpi=600)

sns.histplot(
    data=total_cost_df_all,
    x="Total Cost",
    hue="Configuration",
    stat="density",
    element="step",  
    common_norm=False,
    cumulative=True,
    fill=False,
    ax=ax1
)

ax1.set_xlabel("Total Annual Cost [€]")
ax1.set_ylabel("Density")
ax1.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))


# Move legend to the right
leg = ax1.get_legend()
if leg is not None:
    leg.set_bbox_to_anchor((1.02, 0.5))  
    leg.set_loc('center left')
    leg.set_frame_on(True)               

plt.title("Total Annual Cost Histogram - Density")

plt.tight_layout()

plt.savefig("Total Annual Cost Histogram - Density.png", bbox_inches="tight")
plt.close()

# Solar plot


fig, ax1 = plt.subplots(figsize=(10, 6), dpi=600)

sns.histplot(
    data=solar_pv_df_all,
    x="Solar PV",
    hue="Configuration",
    stat="density",
    element="step",  
    common_norm=False,
    cumulative=True,
    fill=False,
    ax=ax1
)

ax1.set_xlabel("Solar PV Capacity [kW]")
ax1.set_ylabel("Density")
ax1.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))


# Move legend to the right
leg = ax1.get_legend()
if leg is not None:
    leg.set_bbox_to_anchor((1.02, 0.5))  
    leg.set_loc('center left')
    leg.set_frame_on(True)               

plt.title("Solar PV Capacity - Density")

plt.tight_layout()

plt.savefig("Solar PV Capacity - Density.png", bbox_inches="tight")
plt.close()


# Battery plot


fig, ax1 = plt.subplots(figsize=(10, 6), dpi=600)

sns.histplot(
    data=battery_capacity_df_all,
    x="Battery Capacity",
    hue="Configuration",
    stat="density",
    element="step",  
    common_norm=False,
    cumulative=True,
    fill=False,
    ax=ax1
)

ax1.set_xlabel("Storage Capacity [kWh]")
ax1.set_ylabel("Density")
ax1.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))


leg = ax1.get_legend()
if leg is not None:
    leg.set_bbox_to_anchor((1.02, 0.5))  
    leg.set_loc('center left')
    leg.set_frame_on(True)               

plt.title("Storage Capacity - Density")

plt.tight_layout()

plt.savefig("Storage Capacity - Density.png", bbox_inches="tight")
plt.close()


#---------------
## Violin plots
#---------------

## Solar PV violin plot

fig, ax = plt.subplots(figsize=(10, 6), dpi=600)

sns.violinplot(
    data=solar_pv_df_all,
    x="Configuration",
    y="Solar PV",
    hue="Configuration",
    legend=False,
    cut=0,
    ax=ax
)

ax.set_xlabel("Configuration")
ax.set_ylabel("Total Solar PV Capacity [kW]")
ax.set_title("Solar PV Capacity Distribution", loc='center')

plt.tight_layout()
plt.savefig("Solar PV Violin Plot.png")
plt.close()


## Battery violin plot

fig, ax = plt.subplots(figsize=(10, 6), dpi=600)

sns.violinplot(
    data=battery_capacity_df_all,
    x="Configuration",
    y="Battery Capacity",
    hue="Configuration",
    legend=False,
    cut=0,
    ax=ax
)

ax.set_xlabel("Configuration")
ax.set_ylabel("Storage Capacity [kWh]")
ax.set_title("Storage Capacity Distribution", loc='center')

plt.tight_layout()
plt.savefig("Storage Capacity Violin Plot.png")
plt.close()


## Cost violin plot

fig, ax = plt.subplots(figsize=(10, 6), dpi=600)

sns.violinplot(
    data=total_cost_df_all,
    x="Configuration",
    y="Total Cost",
    hue="Configuration",
    legend=False,
    ax=ax
)

ax.set_xlabel("Configuration")
ax.set_ylabel("Total Annual Cost [€]")
ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
ax.set_title("Total Annual Cost Distribution", loc='center')

plt.tight_layout()
plt.savefig("Total Annual Cost Violin Plot.png", bbox_inches="tight")
plt.close()


#---------------
## Group plots with violin
#---------------
## Solar Histogram

# Solar plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=600)

# histogram (primary axis)

sns.histplot(
    data=solar_pv_df_all,
    x="Solar PV",
    hue="Configuration",
    stat="count",     
    element="step",   
    common_norm=False,
    ax=ax1
)

ax1.set_xlabel("Total Solar PV Capacity [kW]")
ax1.set_ylabel("Frequency")
ax1.set_title("Solar PV Capacity Histogram - Frequency", loc='center')

sns.violinplot(
    data=solar_pv_df_all,
    x="Configuration",
    y="Solar PV",
    hue="Configuration",
    legend=False,
    cut=0,
    ax=ax2
)

ax2.set_xlabel("Configuration")
ax2.set_ylabel("Total Solar PV Capacity [kW]")
ax2.set_title("Solar PV Capacity Distribution", loc='center')

plt.tight_layout()
plt.savefig("Solar PV Capacity Histogram - Violin.png")
plt.close()

## Battery Histogram

# plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=600)

# histogram (primary axis)
sns.histplot(
    data=battery_capacity_df_all,
    x="Battery Capacity",
    hue="Configuration",
    stat="count",     # or "density"
    element="step",   # cleaner overlay
    common_norm=False,
    ax=ax1
)
ax1.set_xlabel("Storage Capacity [kWh]")
ax1.set_ylabel("Frequency")
ax1.set_title("Storage Capacity Histogram - Frequency", loc='center')

sns.violinplot(
    data=battery_capacity_df_all,
    x="Configuration",
    y="Battery Capacity",
    hue="Configuration",
    cut=0,
    legend=False,
    ax=ax2
)

ax2.set_xlabel("Configuration")
ax2.set_ylabel("Storage Capacity [kWh]")
ax2.set_title("Storage Capacity Distribution", loc='center')

    
plt.tight_layout()
plt.savefig("Storage Capacity Histogram - Violin.png")
plt.close()


#---------------
## Cost plot
#---------------

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=600)

sns.histplot(
    data=total_cost_df_all,
    x="Total Cost",
    hue="Configuration",
    stat="count",
    element="step",
    common_norm=False,
    ax=ax1
)

ax1.set_xlabel("Total Annual Cost [€]")
ax1.set_ylabel("Frequency")
ax1.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
ax1.set_title("Total Annual Cost Histogram - Frequency", loc='center')


sns.violinplot(
    data=total_cost_df_all,
    x="Configuration",
    y="Total Cost",
    hue="Configuration",
    legend=False,
    ax=ax2
)

ax2.set_xlabel("Configuration")
ax2.set_ylabel("Total Annual Cost [€]")
ax2.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
ax2.tick_params(axis='x', labelrotation=0, labelsize=9)
ax2.set_title("Total Annual Cost Distribution", loc='center')

plt.tight_layout()
plt.savefig("Total Annual Cost Histogram - Violin.png", bbox_inches="tight")
plt.close()

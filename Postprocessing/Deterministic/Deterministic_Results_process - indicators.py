import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

# Ensure files are in the same directory
files = {
    "Configuration A": "Model_results_Configuration_A.nc",
    "Configuration B": "Model_results_Configuration_B.nc",
    "Configuration C": "Model_results_Configuration_C.nc",
    "Configuration D": "Model_results_Configuration_D.nc",
    "Configuration E": "Model_results_Configuration_E.nc",
}



cluster_days = pd.read_csv("Cluster_days_count.csv")
cluster_days["Representative Date"] = pd.to_datetime(
    cluster_days["Representative Date"]
)

weights = cluster_days.set_index("Representative Date")["Counts"]

results = []


for name, path in files.items():

    ds = xr.open_dataset(path, engine="h5netcdf")

    dates = pd.to_datetime(ds.timesteps.values).normalize()

    timestep_weights = pd.Series(
        dates.map(weights),
        index=ds.timesteps.values
    )


    grid = (
        ds.flow_out.sel(techs="Grid_supply")
        .sum(dim="nodes")
    )

    annual_grid = (
        grid
        * xr.DataArray(
            timestep_weights.values,
            dims=["timesteps"],
            coords={"timesteps": ds.timesteps}
        )
    ).sum().item()


    techs = ds.techs.values.tolist()

    if (
        "EC_Solar_PV_supply" not in techs
        and "Solar_PV" not in techs
    ):

        results.append({
            "Configuration": name,
            "Metric": "Electricity from the grid",
            "Value": annual_grid,
        })

        ds.close()
        continue


    demand = (
        ds.flow_in.sel(techs="Electricity_demand")
        .sum(dim="nodes")
    )

    ev_demand = (
        ds.flow_in.sel(techs="EV_charger")
        .sum(dim="nodes")
    )

    total_demand = demand + ev_demand

    annual_demand = (
        total_demand
        * xr.DataArray(
            timestep_weights.values,
            dims=["timesteps"],
            coords={"timesteps": ds.timesteps}
        )
    ).sum().item()


    if "EC_Solar_PV_supply" in techs:
        solar_tech = "EC_Solar_PV_supply"
    else:
        solar_tech = "Solar_PV"

    solar = (
        ds.flow_out.sel(techs=solar_tech)
        .sum(dim="nodes")
    )

    annual_solar = (
        solar
        * xr.DataArray(
            timestep_weights.values,
            dims=["timesteps"],
            coords={"timesteps": ds.timesteps}
        )
    ).sum().item()

    exports = (
        ds.flow_export.sel(techs=solar_tech)
        .sum(dim="nodes")
    )

    annual_exports = (
        exports
        * xr.DataArray(
            timestep_weights.values,
            dims=["timesteps"],
            coords={"timesteps": ds.timesteps}
        )
    ).sum().item()

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    self_consumption = (
        annual_solar - annual_exports
    ) / annual_solar

    self_sufficiency = (
        annual_demand - annual_grid
    ) / annual_demand

    results.extend([
        {
            "Configuration": name,
            "Metric": "Self-consumption",
            "Value": self_consumption,
        },
        {
            "Configuration": name,
            "Metric": "Self-sufficiency",
            "Value": self_sufficiency,
        },
        {
            "Configuration": name,
            "Metric": "Electricity exports to the grid",
            "Value": annual_exports,
        },
        {
            "Configuration": name,
            "Metric": "Electricity from the grid",
            "Value": annual_grid,
        },
    ])

    ds.close()


# ============================================================
# Final DataFrame
# ============================================================

final_df = pd.DataFrame(results)



final_df_2 = final_df.pivot(
    index="Metric",
    columns="Configuration",
    values="Value"
).reset_index()

final_df_2.to_csv("Deterministic_results_metrics.csv")


# ============================================================
# Plots
# ============================================================

metrics = [
    "Self-consumption",
    "Self-sufficiency",
    "Electricity exports to the grid",
    "Electricity from the grid",
]

from matplotlib.ticker import PercentFormatter, StrMethodFormatter

for metric in metrics:

    plot_df = final_df[
        final_df["Metric"] == metric
    ].dropna(subset=["Value"])

    fig, ax = plt.subplots(
        figsize=(10, 6),
        dpi=600
    )

    ax.bar(
        plot_df["Configuration"],
        plot_df["Value"]
    )

    ax.set_xlabel("Configuration")
    ax.set_ylabel(metric)
    ax.set_title(metric)

    if metric in [
        "Self-consumption",
        "Self-sufficiency"
    ]:
        ax.yaxis.set_major_formatter(
            PercentFormatter(1.0)
        )
        ax.set_ylim(0, 1)

    elif metric == "Electricity exports to the grid":
        ax.set_ylabel(
            "Electricity exports to the grid [kWh]"
        )
        ax.yaxis.set_major_formatter(
            StrMethodFormatter("{x:,.0f}")
        )

    elif metric == "Electricity from the grid":
        ax.set_ylabel(
            "Electricity from the grid [kWh]"
        )
        ax.yaxis.set_major_formatter(
            StrMethodFormatter("{x:,.0f}")
        )

    plt.tight_layout()
    plt.savefig(f"Indicator - {metric}.png")
    plt.close()
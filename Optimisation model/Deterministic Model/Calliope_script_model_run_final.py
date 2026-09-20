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

#os.chdir(os.path.dirname(__file__))

#%% Model Run
calliope.set_log_verbosity("INFO", include_solver_output=True)
model = calliope.read_yaml('model_scen1.yaml')

model.build()
model.solve()

model.to_csv('Cyprus_EC_model_S1_min_cost')
ds_res = model.results
ds_res.to_netcdf("Model_results_Configuration_A.nc", engine="h5netcdf")
model.to_netcdf("Cyprus_EC_S1_min_cost.nc")
#model = calliope.read_netcdf('Cyprus_EC_model_S3.nc')

#%% Plotting Section
pio.renderers.default = "json"

OUTDIR = Path("plots")
OUTDIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
net_flow = model.results.flow_out.fillna(0) - model.results.flow_in.fillna(0)

colors = model.inputs.color.to_series().to_dict()

# ------------------------------------------------------------------
#%%% 1a. System-level balance (HTML – ALL carriers)
# ------------------------------------------------------------------

all_carriers = net_flow.carriers.values
base_tech = model.inputs.base_tech.to_series()

has_flow_export = hasattr(model.results, "flow_export")
has_flow_in     = hasattr(model.results, "flow_in")

for carrier in all_carriers:

    # ------------------ FLOW OUT ------------------
    df_out = (
        model.results.flow_out
        .sel(carriers=carrier)
        .sum("nodes")
        .to_series()
        .dropna()
        .to_frame("value")
        .reset_index()
    )
    if df_out.empty:
        continue

    df_out = df_out[df_out.techs.map(base_tech) != "transmission"]
    df_out["type"] = "out"

    # ------------------ FLOW IN (NEGATIVE) ------------------
    df_in = pd.DataFrame()
    if has_flow_in:
        df_in = (
            model.results.flow_in
            .sel(carriers=carrier)
            .sum("nodes")
            .to_series()
            .dropna()
            .to_frame("value")
            .reset_index()
        )
        if not df_in.empty:
            df_in["value"] = -df_in["value"]
            df_in["type"]  = "in"
            df_in = df_in[df_in.techs.map(base_tech) != "transmission"]

    # ------------------ DEMAND TECH ------------------
    demand_tech = f"{carrier}_demand"   #

    # EXCLUDE demand from flow_in
    if not df_in.empty:
        df_in = df_in[df_in.techs != demand_tech]


    df_exp = pd.DataFrame()
    if has_flow_export:
        df_exp = (
            model.results.flow_export
            .sel(carriers=carrier)
            .sum("nodes")
            .to_series()
            .dropna()
            .to_frame("value")
            .reset_index()
        )
        if not df_exp.empty:
            df_exp["value"] = -df_exp["value"]
            df_exp["type"]  = "export"
            df_exp = df_exp[df_exp.techs.map(base_tech) != "transmission"]


    frames = [df_out]
    if not df_in.empty:  frames.append(df_in)
    if not df_exp.empty: frames.append(df_exp)
    df_sys = pd.concat(frames, ignore_index=True)


    tech_tot = df_sys.groupby("techs")["value"].sum()
    used_techs = tech_tot[tech_tot != 0].index
    df_sys = df_sys[df_sys.techs.isin(used_techs)]
    if df_sys.empty:
        continue


# ------------------ DEMAND SERIES ------------------
    if demand_tech in net_flow.techs.values:
        df_demand = (
            net_flow
            .sel(carriers=carrier, techs=demand_tech)
            .sum("nodes")
            .to_series()
            .dropna()
            .to_frame("demand")
            .reset_index()
        )
    else:
        df_demand = pd.DataFrame()
    # ------------------ HTML FIGURE ------------------
    # FLOW OUT (positive bars)
    fig_html = px.bar(
        df_sys[df_sys.type == "out"],
        x="timesteps",
        y="value",
        color="techs",
        color_discrete_map=colors,
        title=f"{carrier} Balance - System",
    )

    # FLOW IN 
    df_in_plot = df_sys[df_sys.type == "in"]
    if not df_in_plot.empty:
        fig_html.add_bar(
            x=df_in_plot["timesteps"],
            y=df_in_plot["value"],
            marker_color=[colors.get(t,"grey") for t in df_in_plot.techs],
            name=None,
            showlegend=False,
        )

    # FLOW EXPORT
    df_exp_plot = df_sys[df_sys.type == "export"]
    if not df_exp_plot.empty:
        for tech in df_exp_plot.techs.unique():
            dft = df_exp_plot[df_exp_plot.techs == tech]
            if not (dft["value"] != 0).any():
                continue
            fig_html.add_bar(
                x=dft["timesteps"],
                y=dft["value"],
                marker_color=colors.get(tech,"grey"),
                marker_pattern_shape="\\",
                name=f"{tech}_export",
            )

    # DEMAND LINE (unchanged)
    if not df_demand.empty:
        fig_html.add_scatter(
            x=df_demand["timesteps"],
            y=-df_demand["demand"],
            marker_color=colors.get(demand_tech, "black"),
            name=f"{demand_tech}",
        )

    fig_html.update_layout(
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(t=60)
    )

    fig_html.write_html(OUTDIR / f"{carrier}_Balance_System.html")

# ------------------------------------------------------------------#
#%%% 1b. System-level balance (PNG – ALL carriers)
# ------------------------------------------------------------------#

all_carriers = net_flow.carriers.values
base_tech = model.inputs.base_tech.to_series()

has_flow_export = hasattr(model.results, "flow_export")
has_flow_in     = hasattr(model.results, "flow_in")

for carrier in all_carriers:

    # ----------- flow_out -----------
    df_out = (
        model.results.flow_out
        .sel(carriers=carrier)
        .sum("nodes")
        .to_series()
        .dropna().to_frame("value").reset_index()
    )
    if df_out.empty:
        continue

    df_out = df_out[df_out.techs.map(base_tech) != "transmission"]
    df_out["type"] = "out"

    # ----------- flow_in -----------
    df_in = pd.DataFrame()
    if has_flow_in:
        df_in = (
            model.results.flow_in
            .sel(carriers=carrier)
            .sum("nodes")
            .to_series()
            .dropna().to_frame("value").reset_index()
        )
        if not df_in.empty:
            df_in["value"] = -df_in["value"]
            df_in["type"]  = "in"
            df_in = df_in[df_in.techs.map(base_tech) != "transmission"]

    # ----------- demand tech -----------
    demand_tech = f"{carrier}_demand"

    # EXCLUDE demand from flow_in:
    if not df_in.empty:
        df_in = df_in[df_in.techs != demand_tech]

    # ----------- flow_export -----------
    df_exp = pd.DataFrame()
    if has_flow_export:
        df_exp = (
            model.results.flow_export
            .sel(carriers=carrier)
            .sum("nodes")
            .to_series()
            .dropna().to_frame("value").reset_index()
        )
        if not df_exp.empty:
            df_exp["value"] = -df_exp["value"]
            df_exp["type"]  = "export"
            df_exp = df_exp[df_exp.techs.map(base_tech) != "transmission"]

    # combine flows
    frames = [df_out]
    if not df_in.empty: frames.append(df_in)
    if not df_exp.empty: frames.append(df_exp)
    df_sys = pd.concat(frames, ignore_index=True)

    # remove zero-techs
    tech_tot = df_sys.groupby("techs")["value"].sum()
    used = tech_tot[tech_tot != 0].index
    df_sys = df_sys[df_sys.techs.isin(used)]

    if df_sys.empty:
        continue


# ----------- demand -----------
    if demand_tech in net_flow.techs.values:
        df_demand = (
            net_flow
            .sel(carriers=carrier, techs=demand_tech)
            .sum("nodes")
            .to_series()
            .dropna().to_frame("demand").reset_index()
        )
    else:
        df_demand = pd.DataFrame()


    # ----------- PNG FIGURE -----------
    timesteps = np.sort(df_sys["timesteps"].unique())
    x = np.arange(len(timesteps))

    fig, ax = plt.subplots(figsize=(12,6), dpi=600)
    bottom_pos = np.zeros(len(timesteps))
    bottom_neg = np.zeros(len(timesteps))
    labeled = set()

    # ************* flow_out STACK *************
    for tech in used:
        vals = (
            df_sys[(df_sys.techs == tech) & (df_sys.type == "out")]
            .set_index("timesteps")["value"]
            .reindex(timesteps).fillna(0).values
        )
        if np.all(vals == 0):
            continue
   
        ax.bar(
            x, vals, bottom=bottom_pos, width=0.9,
            color=colors.get(tech),
            label=tech
        )
        
        bottom_pos += vals
        labeled.add(tech)

    # ************* flow_in (negative) *************
    if not df_in.empty:
        for tech in df_in.techs.unique():
            vals = (
                df_in[df_in.techs == tech]
                .set_index("timesteps")["value"]
                .reindex(timesteps).fillna(0).values
            )
            if np.all(vals == 0): continue

            label = None if tech in labeled else tech

            ax.bar(
                x, vals, bottom=bottom_neg, width=0.9,
                color=colors.get(tech),
                label=label     # no legend for flow_in
            )
            bottom_neg += vals

    # ************* flow_export (negative + hatch) *************
    if not df_exp.empty:
        for tech in df_exp.techs.unique():
            vals = (
                df_exp[df_exp.techs == tech]
                .set_index("timesteps")["value"]
                .reindex(timesteps).fillna(0).values
            )
            if np.all(vals == 0): continue

            ax.bar(
                x, vals, bottom=bottom_neg, width=0.9,
                color=colors.get(tech),
                hatch="\\\\",
                label = f"{tech}_export" if f"{tech}_export" not in labeled else None
            )
            bottom_neg += vals
            labeled.add(f"{tech}_export")

    # ----------- demand (line) -----------
    if not df_demand.empty:
        dem = (
            df_demand.set_index("timesteps")["demand"]
            .reindex(timesteps).fillna(0).values
        )
        if not np.all(dem == 0):
            ax.plot(
                x, -dem,
                color=colors.get(demand_tech, "black"),
                linewidth=1,
                label= f"{demand_tech}"
            )


    ax.set_title(f"{carrier} Balance - System")

    handles, labels = ax.get_legend_handles_labels()
    seen=set(); H=[]; L=[]
    for h,l in zip(handles,labels):
        if l and l not in seen:
            H.append(h); L.append(l); seen.add(l)

    if H:
        ax.legend(
            H, L, loc="lower center",
            bbox_to_anchor=(0.5,-0.45),
            ncol=min(6,len(L)),
            frameon=True
        )

    ax.grid(True, axis='y', linestyle="--", linewidth=0.5, alpha=0.7)
    ax.set_ylabel("Flow in/out (kWh)")
    ax.set_xlabel("Timestep",labelpad=8)


    STEPS = 24; HOUR = [0,6,12,18]
    rd_pos=[]; rd_lab=[]; hr_pos=[]; hr_lab=[]
    n=len(timesteps)

    for b in range(0,n,STEPS):
        e=min(b+STEPS,n)
        rd_pos.append(b+(e-b)/2-0.5)
        rd_lab.append(f"D{b//STEPS+1}")
        for i in range(b,e):
            h=(i-b)%STEPS
            if h in HOUR:
                hr_pos.append(i); hr_lab.append(str(h))

    ax.set_xticks(rd_pos); ax.set_xticklabels(rd_lab)
    ax.set_xticks(hr_pos,minor=True); ax.set_xticklabels(hr_lab,minor=True)
    ax.tick_params(axis="x",which="major",length=0,pad=18)
    ax.tick_params(axis="x",which="minor",pad=4)


    ax.autoscale(axis="y", tight=True)
    ymin,ymax = ax.get_ylim()
    pos_pad=0.10*ymax if ymax>0 else 0
    neg_pad=0.10*abs(ymin) if ymin<0 else 0

    if ymax>0 and ymin<0:
        ymin_new=ymin-neg_pad; ymax_new=ymax+pos_pad
    elif ymax>0 and ymin>=0:
        ymin_new=-0.10*ymax; ymax_new=ymax+pos_pad
    else:
        ymin_new=ymin-neg_pad; ymax_new=0.10*abs(ymin)

    ax.set_ylim(ymin_new,ymax_new)

    ymin,ymax = ax.get_ylim()
    ax.set_ylim(ymin, ymax * 1.05)

    plt.tight_layout()
    plt.savefig(OUTDIR / f"{carrier}_Balance_System.png")
    plt.close()

# ------------------------------------------------------------------#
#%%% 2a. Node-level balance 

# ------------------------------------------------------------------#

all_carriers = net_flow.carriers.values
has_flow_export = hasattr(model.results, "flow_export")

for carrier in all_carriers:

    # Base net_flow for carrier
    df_carrier = (
        net_flow
        .sel(carriers=carrier)
        .to_series()
        .dropna()
        .to_frame("Flow in/out (kWh)")
        .reset_index()
    )
    if df_carrier.empty:
        continue

    # Export for this carrier
    df_export_carrier = pd.DataFrame()
    if has_flow_export:
        df_export_carrier = (
            model.results.flow_export
            .sel(carriers=carrier)
            .to_series()
            .dropna()
            .to_frame("Flow export (kWh)")
            .reset_index()
        )

    demand_tech = f"{carrier}_demand"

    # ----- Loop nodes -----
    for node in df_carrier.nodes.unique():

        df_node = df_carrier[df_carrier.nodes == node]
        if df_node.empty:
            continue

        timesteps = np.sort(df_node.timesteps.unique())

        # Demand separated
        df_demand = df_node[df_node.techs == demand_tech]
        df_other  = df_node[df_node.techs != demand_tech]

        # Node-level export
        df_exp_node = pd.DataFrame()
        if has_flow_export and not df_export_carrier.empty:
            df_exp_node = df_export_carrier[df_export_carrier.nodes == node].copy()
            if not df_exp_node.empty:
                df_exp_node["Flow export (kWh)"] = -df_exp_node["Flow export (kWh)"]

        # ----- Node activity check -----
        activity = False


        if df_other["Flow in/out (kWh)"].abs().sum() > 0:
            activity = True


        if not df_exp_node.empty and df_exp_node["Flow export (kWh)"].abs().sum() > 0:
            activity = True


        if not df_demand.empty and df_demand["Flow in/out (kWh)"].abs().sum() > 0:
            activity = True

        if not activity:
            continue

        # ----- Zero-tech filtering for net_flow -----
        tech_active = set()

        # net_flow non-zero techs
        for tech in df_other.techs.unique():
            vals = (
                df_other[df_other.techs == tech]
                .set_index("timesteps")["Flow in/out (kWh)"]
                .reindex(timesteps).fillna(0)
            )
            if (vals != 0).any():
                tech_active.add(tech)


        if not df_exp_node.empty:
            for tech in df_exp_node.techs.unique():
                vals = (
                    df_exp_node[df_exp_node.techs == tech]
                    .set_index("timesteps")["Flow export (kWh)"]
                    .reindex(timesteps).fillna(0)
                )
                if (vals != 0).any():
                    tech_active.add(tech)


        df_other_nz = df_other[df_other.techs.isin(tech_active)]

        # ----- Base net_flow bars -----
        fig_html = px.bar(
            df_other_nz,
            x="timesteps",
            y="Flow in/out (kWh)",
            color="techs",
            color_discrete_map=colors,
            title=f"{carrier} Balance – {node}",
        )


        if not df_exp_node.empty:
            for tech in df_exp_node.techs.unique():
                if tech not in tech_active:
                    continue

                vals = (
                    df_exp_node[df_exp_node.techs == tech]
                    .set_index("timesteps")["Flow export (kWh)"]
                    .reindex(timesteps).fillna(0).values
                )

                if (vals != 0).any():
                    fig_html.add_bar(
                        x=timesteps,
                        y=vals,
                        marker_color=colors.get(tech),
                        marker_pattern_shape="\\",
                        name=f"{tech}_export",
                        showlegend=True,
                    )


        if not df_demand.empty:
            dem_vals = (
                df_demand.set_index("timesteps")["Flow in/out (kWh)"]
                .reindex(timesteps).fillna(0).values
            )
            if (dem_vals != 0).any():
                fig_html.add_scatter(
                    x=timesteps,
                    y=-dem_vals,
                    marker_color=colors.get(demand_tech, "black"),
                    name=f"{demand_tech}",
                )


        fig_html.update_layout(
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5
            ),
            margin=dict(t=60)
        )
        fig_html.write_html(OUTDIR / f"{carrier}_Balance_{node}.html")
        
# ------------------------------------------------------------------#
#%%% 2b. Node-level balance (PNG – ALL carriers, FINAL CORRECTED)
# ------------------------------------------------------------------#

all_carriers = net_flow.carriers.values
has_flow_export = hasattr(model.results, "flow_export")

for carrier in all_carriers:

    # 
    df_carrier = (
        net_flow
        .sel(carriers=carrier)
        .to_series()
        .dropna()
        .to_frame("Flow in/out (kWh)")
        .reset_index()
    )
    if df_carrier.empty:
        continue


    df_export_carrier = pd.DataFrame()
    if has_flow_export:
        df_export_carrier = (
            model.results.flow_export
            .sel(carriers=carrier)
            .to_series()
            .dropna()
            .to_frame("Flow export (kWh)")
            .reset_index()
        )

    demand_tech = f"{carrier}_demand"

    for node in df_carrier.nodes.unique():


        df_node = df_carrier[df_carrier.nodes == node]
        if df_node.empty:
            continue

        df_exp_node = pd.DataFrame()
        if has_flow_export and not df_export_carrier.empty:
            df_exp_node = df_export_carrier[df_export_carrier.nodes == node].copy()
            if not df_exp_node.empty:
                df_exp_node["Flow export (kWh)"] = -df_exp_node["Flow export (kWh)"]

        node_has_activity = False
        if df_node["Flow in/out (kWh)"].abs().sum() > 0:
            node_has_activity = True
        if not df_exp_node.empty and df_exp_node["Flow export (kWh)"].abs().sum() > 0:
            node_has_activity = True

        if not node_has_activity:
            continue

        # Timesteps
        timesteps = np.sort(df_node.timesteps.unique())
        x = np.arange(len(timesteps))

        # Demand separated
        df_demand = df_node[df_node.techs == demand_tech]
        df_other  = df_node[df_node.techs != demand_tech]

        #  Zero-tech filtering ----
        tech_active = set()

        # net_flow
        for tech in df_other.techs.unique():
            vals = (
                df_other[df_other.techs == tech]
                .set_index("timesteps")["Flow in/out (kWh)"]
                .reindex(timesteps).fillna(0)
            )
            if (vals != 0).any():
                tech_active.add(tech)

        # export
        if not df_exp_node.empty:
            for tech in df_exp_node.techs.unique():
                vals = (
                    df_exp_node[df_exp_node.techs == tech]
                    .set_index("timesteps")["Flow export (kWh)"]
                    .reindex(timesteps).fillna(0)
                )
                if (vals != 0).any():
                    tech_active.add(tech)

        # Filter net_flow to active techs
        df_other_nz = df_other[df_other.techs.isin(tech_active)]

        #  PLOT ----
        fig, ax = plt.subplots(figsize=(12,6), dpi=600)
        bottom_pos = np.zeros(len(timesteps))
        bottom_neg = np.zeros(len(timesteps))
        labeled = set()

        # -------- net_flow stack -------
        for tech in df_other_nz.techs.unique():

            vals = (
                df_other_nz[df_other_nz.techs == tech]
                .set_index("timesteps")["Flow in/out (kWh)"]
                .reindex(timesteps).fillna(0).values
            )

            if np.all(vals == 0):
                continue

            vpos = np.where(vals > 0, vals, 0)
            vneg = np.where(vals < 0, vals, 0)

            base_label = None if tech in labeled else tech

            if np.any(vpos):
                ax.bar(
                    x, vpos, bottom=bottom_pos, width=0.9,
                    color=colors.get(tech),
                    label=base_label
                )
                bottom_pos += vpos
                labeled.add(tech)

            if np.any(vneg):
                ax.bar(
                    x, vneg, bottom=bottom_neg, width=0.9,
                    color=colors.get(tech),
                    label=base_label
                )
                bottom_neg += vneg
                labeled.add(tech)


        if not df_exp_node.empty:
            for tech in df_exp_node.techs.unique():

                if tech not in tech_active:
                    continue

                vals = (
                    df_exp_node[df_exp_node.techs == tech]
                    .set_index("timesteps")["Flow export (kWh)"]
                    .reindex(timesteps).fillna(0).values
                )

                if np.all(vals == 0):
                    continue

                export_label = f"{tech}_export"
                if export_label in labeled:
                    export_label = None

                ax.bar(
                    x, vals, bottom=bottom_neg, width=0.9,
                    color=colors.get(tech),
                    hatch="\\\\",
                    label=export_label
                )
                bottom_neg += vals
                labeled.add(f"{tech}_export")

        # -------- DEMAND LINE --------
        if not df_demand.empty:
            dem_vals = (
                df_demand.set_index("timesteps")["Flow in/out (kWh)"]
                .reindex(timesteps).fillna(0).values
            )
            if not np.all(dem_vals == 0):
                ax.plot(
                    x, -dem_vals,
                    color=colors.get(demand_tech, "black"),
                    linewidth=1,
                    label=f"{demand_tech}"
                )

        # ----- Title -----
        ax.set_title(f"{carrier} Balance – {node}")

        #  Legend de‑dup ----
        handles, labels_ = ax.get_legend_handles_labels()
        seen=set(); H=[]; L=[]
        for h,l in zip(handles,labels_):
            if l and l not in seen:
                H.append(h); L.append(l); seen.add(l)

        if H:
            ax.legend(
                H, L,
                loc="lower center",
                bbox_to_anchor=(0.5,-0.3),
                ncol=min(6,len(L)), frameon=True
            )

        #  Grid + labels ----
        ax.grid(True, axis='y', linestyle="--", linewidth=0.5, alpha=0.7)
        ax.set_ylabel("Flow in/out (kWh)")
        ax.set_xlabel("Timestep",labelpad=8)

        #  RD ticks ----
        STEPS=24; HOURS=[0,6,12,18]
        rd_pos=[]; rd_lab=[]; hr_pos=[]; hr_lab=[]
        n=len(timesteps)

        for b in range(0,n,STEPS):
            e=min(b+STEPS,n)
            rd_pos.append(b+(e-b)/2-0.5)
            rd_lab.append(f"D{b//STEPS+1}")
            for i in range(b,e):
                h=(i-b)%STEPS
                if h in HOURS:
                    hr_pos.append(i); hr_lab.append(str(h))

        ax.set_xticks(rd_pos); ax.set_xticklabels(rd_lab)
        ax.set_xticks(hr_pos,minor=True); ax.set_xticklabels(hr_lab,minor=True)
        ax.tick_params(axis="x",which="major",length=0,pad=18)
        ax.tick_params(axis="x",which="minor",pad=4)


        ax.autoscale(axis="y", tight=True)
        ymin,ymax = ax.get_ylim()
        pos_pad = 0.10*ymax if ymax>0 else 0
        neg_pad = 0.10*abs(ymin) if ymin<0 else 0

        if ymax>0 and ymin<0:
            ymin_new=ymin-neg_pad; ymax_new=ymax+pos_pad
        elif ymax>0 and ymin>=0:
            ymin_new=-0.10*ymax;   ymax_new=ymax+pos_pad
        else:
            ymin_new=ymin-neg_pad; ymax_new=0.10*abs(ymin)

        ax.set_ylim(ymin_new,ymax_new)

        ymin,ymax = ax.get_ylim()
        ax.set_ylim(ymin, ymax * 1.05)

        plt.tight_layout()
        plt.savefig(OUTDIR / f"{carrier}_Balance_{node}.png")
        plt.close()



#%%% 3. Installed capacity — per carrier
# ------------------------------------------------------------------

df_capacity = (
    model.results.flow_cap
    .where(model.inputs.base_tech.isin(["supply", "conversion", "storage"]))
    .to_series()
    .where(lambda x: x != 0)
    .dropna()
    .to_frame("Flow capacity (kW)")
    .reset_index()
)

df_capacity = df_capacity.loc[
    ~df_capacity['techs'].isin(['Grid_supply'])
]

if not df_capacity.empty:

    for carrier in df_capacity["carriers"].unique():

        df_c = df_capacity[df_capacity["carriers"] == carrier]
        if df_c.empty:
            continue

        # ---------------------------------------------------------
        # PER-NODE CHARTS 
        # ---------------------------------------------------------
        df_node = (
            df_c.groupby(["nodes", "techs"], as_index=False)["Flow capacity (kW)"].sum()
        )


        df_node = df_node[df_node["Flow capacity (kW)"] != 0]
        if df_node.empty:
            continue

        fig_html_nodes = px.bar(
            df_node,
            x="nodes",
            y="Flow capacity (kW)",
            color="techs",
            color_discrete_map=colors,
            title=f"Installed capacity by node (carrier = {carrier})",
        )
        ymax = df_node["Flow capacity (kW)"].max()
        fig_html_nodes.update_yaxes(range=[0, ymax * 1.1])
        fig_html_nodes.write_html(
            OUTDIR / f"Installed_capacity_{carrier}_nodes.html"
        )

        nodes = df_node["nodes"].unique()
        techs_present = df_node["techs"].unique()

        x = np.arange(len(nodes))
        fig, ax = plt.subplots(figsize=(12, 6), dpi=600)
        bottoms = np.zeros(len(nodes))

        for tech in techs_present:
            vals = (
                df_node[df_node["techs"] == tech]
                .set_index("nodes")["Flow capacity (kW)"]
                .reindex(nodes).fillna(0).values
            )
            if np.all(vals == 0):
                continue

            ax.bar(
                x, vals, bottom=bottoms,
                color=colors.get(tech, "tab:blue"),
                label=tech, width=0.8
            )
            bottoms += vals

        ax.set_xticks(x)
        ax.set_xticklabels(nodes)
        ax.set_ylabel("Flow capacity (kW)")
        ax.set_xlabel("Nodes")
        ax.set_title(f"Installed capacity by node (carrier = {carrier})")
        ax.grid(True, axis='y', linestyle="--", linewidth=0.5, alpha=0.7)

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(
                handles, labels,
                loc="lower center",
                bbox_to_anchor=(0.5, -0.3),
                ncol=min(6, len(labels)),
                frameon=True,
            )

        plt.tight_layout()
        plt.savefig(OUTDIR / f"Installed_capacity_{carrier}_nodes.png")
        plt.close(fig)

        # ---------------------------------------------------------
        # SYSTEM-WIDE CHARTS (HTML + PNG)
        # ---------------------------------------------------------
        df_sys = (
            df_c.groupby("techs", as_index=False)["Flow capacity (kW)"].sum()
        )

        df_sys = df_sys[df_sys["Flow capacity (kW)"] != 0]
        if df_sys.empty:
            continue

        fig_html_sys = px.bar(
            df_sys,
            x="techs",
            y="Flow capacity (kW)",
            color="techs",
            color_discrete_map=colors,
            title=f"System installed capacity (carrier = {carrier})",
        )
        ymax = df_sys["Flow capacity (kW)"].max()
        fig_html_sys.update_yaxes(range=[0, ymax * 1.1])
        fig_html_sys.update_layout(showlegend=False)

        fig_html_sys.write_html(
            OUTDIR / f"Installed_capacity_{carrier}_system_by_tech.html"
        )

        techs_sys = df_sys["techs"].to_numpy()
        vals = df_sys["Flow capacity (kW)"].to_numpy()

        xi = np.arange(len(techs_sys))
        fig, ax = plt.subplots(figsize=(12, 6), dpi=600)

        ax.bar(
            xi, vals,
            color=[colors.get(t, "tab:blue") for t in techs_sys],
            width=0.8
        )

        ax.set_xticks(xi)
        ax.set_xticklabels(techs_sys)
        ax.set_ylabel("Flow capacity (kW)")
        ax.set_xlabel("Techs")
        ax.set_title(f"System installed capacity (carrier = {carrier})")
        ax.grid(True, axis='y', linestyle="--", linewidth=0.5, alpha=0.7)

        plt.tight_layout()
        plt.savefig(OUTDIR / f"Installed_capacity_{carrier}_system_by_tech.png")
        plt.close(fig)

# ------------------------------------------------------------------#
#%%% 4. Plot SOC (generic for any storage tech & any carrier) 
# ------------------------------------------------------------------#



soc_df = (
    model.results.storage
    .to_series()
    .dropna()
    .to_frame("storage")           # kWh stored
    .reset_index()
)

cap_df = (
    model.results.storage_cap
    .to_series()
    .dropna()
    .to_frame("cap")               # kWh capacity
    .reset_index()
)

if not soc_df.empty and not cap_df.empty:
    soc_df = soc_df.merge(cap_df, on=["nodes", "techs"], how="left")


    soc_df = soc_df[pd.notna(soc_df["cap"]) & (soc_df["cap"] > 0)]


    soc_df["SOC"] = soc_df["storage"] / soc_df["cap"]


    has_carriers = "carriers" in soc_df.columns
    carriers_list = soc_df["carriers"].unique() if has_carriers else [None]

    # ----------------------------- LOOP carriers -----------------------------
    for carrier in carriers_list:
        df_c = soc_df if carrier is None else soc_df[soc_df["carriers"] == carrier]
        if df_c.empty:
            continue


        for tech in df_c["techs"].unique():
            df_ct = df_c[df_c["techs"] == tech]
            if df_ct.empty:
                continue

            # ------------------------- LOOP nodes -------------------------
            for node in df_ct["nodes"].unique():
                df_ctn = df_ct[df_ct["nodes"] == node].copy()
                if df_ctn.empty:
                    continue

                # Timesteps sorted; ensure continuous index for plotting
                timesteps = np.sort(df_ctn["timesteps"].unique())
                if len(timesteps) == 0:
                    continue

                soc_vals = (
                    df_ctn.set_index("timesteps")["SOC"]
                         .reindex(timesteps)
                         .to_numpy()
                )


                if np.all(pd.isna(soc_vals)):
                    continue

                # =========================== PNG ===========================
                x = np.arange(len(timesteps))
                fig, ax = plt.subplots(figsize=(12, 6), dpi=600)

                ax.plot(
                    x,
                    soc_vals,
                    color=colors.get(tech, "steelblue"),
                    linewidth=1.4,
                    label="SOC",
                )

                # Grid, labels, title
                ax.grid(True, alpha=0.25)
                title_carrier = (carrier + " – ") if carrier is not None else ""
                ax.set_title(f"State of Charge – {title_carrier}{tech} – {node}")
                ax.set_ylim(0, 1.05)
                ax.set_ylabel("State of Charge")
                ax.legend()


                STEPS_PER_BLOCK = 24
                HOUR_TICKS = [0, 6, 12, 18]

                hour_pos, hour_lab = [], []
                rd_pos, rd_lab = [], []
                n = len(timesteps)

                for block_start in range(0, n, STEPS_PER_BLOCK):
                    block_end = min(block_start + STEPS_PER_BLOCK, n)
                    rd_pos.append(block_start + (block_end - block_start) / 2 - 0.5)
                    rd_lab.append(f"D{block_start // STEPS_PER_BLOCK + 1}")
                    for i in range(block_start, block_end):
                        hour = (i - block_start) % STEPS_PER_BLOCK
                        if hour in HOUR_TICKS:
                            hour_pos.append(i)
                            hour_lab.append(str(hour))

                ax.set_xticks(rd_pos)
                ax.set_xticklabels(rd_lab)
                ax.set_xticks(hour_pos, minor=True)
                ax.set_xticklabels(hour_lab, minor=True)
                ax.tick_params(axis="x", which="major", length=0, pad=18)
                ax.tick_params(axis="x", which="minor", pad=4)

                ax.set_xlabel("Timestep", labelpad=8)

                plt.tight_layout()

                if carrier is None:
                    png_name = OUTDIR / f"{tech}_SOC_{node}.png"
                else:
                    png_name = OUTDIR / f"{carrier}_{tech}_SOC_{node}.png"
                plt.savefig(png_name)
                plt.close(fig)


                df_plot_html = (
                    df_ctn.set_index("timesteps")[["SOC"]]
                          .reindex(timesteps)
                          .reset_index()
                )
                fig_html = px.line(
                    df_plot_html,
                    x="timesteps",
                    y="SOC",
                    markers=False,
                    title=f"State of Charge – {title_carrier}{tech} – {node}",
                )
                fig_html.update_traces(line=dict(color=colors.get(tech, "steelblue"), width=1.4))
                fig_html.update_yaxes(range=[0, 1], title_text="State of Charge")
                fig_html.update_layout(height=600)

                if carrier is None:
                    html_name = OUTDIR / f"{tech}_SOC_{node}.html"
                else:
                    html_name = OUTDIR / f"{carrier}_{tech}_SOC_{node}.html"
                fig_html.write_html(html_name)
else:
    # Nothing to plot: either storage or storage_cap missing
    pass


# ------------------------------------------------------------------#
#%%% 5. Spatial plots
# ------------------------------------------------------------------#


df_trans = (
    model.results.flow_cap
    .where(model.inputs.base_tech == "transmission")
    .sel(carriers="Electricity")
    .to_series()
    .where(lambda x: x != 0)
    .dropna()
    .to_frame("Flow capacity (kW)")
    .reset_index()
)


has_edges_raw = (len(df_trans) > 0)

if has_edges_raw:

    nodes = df_trans["techs"].str.split("_to_", n=1, expand=True)
    df_trans["node_from"] = nodes[0]
    df_trans["node_to"]   = nodes[1]
    df_trans = df_trans.dropna(subset=["node_from", "node_to"])
    df_trans = df_trans.loc[df_trans["node_from"] != df_trans["node_to"]]

    df_trans["lat_from"]  = df_trans["node_from"].map(coords["latitude"])
    df_trans["lon_from"]  = df_trans["node_from"].map(coords["longitude"])
    df_trans["lat_to"]    = df_trans["node_to"].map(coords["latitude"])
    df_trans["lon_to"]    = df_trans["node_to"].map(coords["longitude"])


    df_trans = df_trans.dropna(subset=["lat_from","lon_from","lat_to","lon_to"]).copy()

has_edges = has_edges_raw and (len(df_trans) > 0)

df_capacity_coords = None
if has_edges:
    df_capacity_coords = pd.concat([
        pd.DataFrame({
            "edge_id": df_trans.index,  # stable id per edge
            "techs": df_trans["techs"],
            "latitude": df_trans["lat_from"],
            "longitude": df_trans["lon_from"],
            "Flow capacity (kW)": df_trans["Flow capacity (kW)"],
        }),
        pd.DataFrame({
            "edge_id": df_trans.index,
            "techs": df_trans["techs"],
            "latitude": df_trans["lat_to"],
            "longitude": df_trans["lon_to"],
            "Flow capacity (kW)": df_trans["Flow capacity (kW)"],
        }),
    ], ignore_index=True)




tech_colors = model.inputs.color.to_series().to_dict()

def tech_color(tech, fallback="blue"):
    c = tech_colors.get(tech)
    return fallback if (c is None or str(c).lower() == "nan") else c


node_names = coords.index.astype(str).tolist()
node_lat   = coords["latitude"].to_numpy()
node_lon   = coords["longitude"].to_numpy()

fig = go.Figure()


fig.add_trace(
    go.Scattermap(
        lat=node_lat,
        lon=node_lon,
        mode="markers",
        marker=dict(size=7, color="black"),
        text=node_names,               # <- provide names
        hoverinfo="text",              # <- show text on hover

        showlegend=False,
        name="Nodes",
    )
)




fig.add_trace(
    go.Scattermap(
        lat=node_lat,
        lon=node_lon,
        mode="text",
        text=node_names,
        textposition="top center",
        textfont=dict(size=14, color="white"),
        hoverinfo="skip",
        hovertemplate=None,
        showlegend=False,
        name="Node labels (halo)",
    )
)


fig.add_trace(
    go.Scattermap(
        lat=node_lat,
        lon=node_lon,
        mode="text",
        text=node_names,
        textposition="top center",
        textfont=dict(size=12, color="black"),
        hoverinfo="skip",
        hovertemplate=None,
        showlegend=False,
        name="Node labels",
    )
)


if has_edges and df_capacity_coords is not None and len(df_capacity_coords) > 0:
    fig_lines = px.line_map(
        df_capacity_coords,
        lat="latitude",
        lon="longitude",
        color="techs",
        color_discrete_map=tech_colors,
        hover_data=["Flow capacity (kW)"],
        line_group="edge_id",
        height=720,
    )
    for tr in fig_lines.data:
        fig.add_trace(tr)

fig.update_layout(
    map_style="open-street-map",
    map=dict(
        center=dict(
            lat=float((df_capacity_coords["latitude"].mean() if has_edges else coords["latitude"].mean())),
            lon=float((df_capacity_coords["longitude"].mean() if has_edges else coords["longitude"].mean())),
        ),
        zoom=15,
    ),
    margin=dict(r=0, t=40, l=0, b=0),
    height=720,
)

OUTDIR.mkdir(parents=True, exist_ok=True)
fig.write_html(
    OUTDIR / ("transmission_map.html" if has_edges else "nodes_map.html"),
    include_plotlyjs=True,
    full_html=True,
    config={"scrollZoom": True, "displaylogo": False},
)

# ------------------------------------------------------
#%%%% 5b Spatial plot png
# ------------------------------------------------------

lat0 = float(coords["latitude"].mean())
lon0 = float(coords["longitude"].mean())

zone = int((lon0 + 180) // 6) + 1
is_north = lat0 >= 0

wgs84_longlat = pyproj.CRS.from_proj4("+proj=longlat +datum=WGS84 +no_defs")
utm_proj4 = (
    f"+proj=utm +zone={zone} "
    f"{'+north' if is_north else '+south'} "
    "+datum=WGS84 +units=m +no_defs"
)
utm_crs = pyproj.CRS.from_proj4(utm_proj4)
to_metric = pyproj.Transformer.from_crs(wgs84_longlat, utm_crs, always_xy=True)

origin_x, origin_y = to_metric.transform(lon0, lat0)


node_x_abs, node_y_abs = to_metric.transform(
    coords["longitude"].to_numpy(), coords["latitude"].to_numpy()
)
node_x_rel = node_x_abs - origin_x
node_y_rel = node_y_abs - origin_y


if has_edges:
    x_from_abs, y_from_abs = to_metric.transform(
        df_trans["lon_from"].to_numpy(), df_trans["lat_from"].to_numpy()
    )
    x_to_abs, y_to_abs = to_metric.transform(
        df_trans["lon_to"].to_numpy(), df_trans["lat_to"].to_numpy()
    )

    x_from_rel = x_from_abs - origin_x
    y_from_rel = y_from_abs - origin_y
    x_to_rel   = x_to_abs   - origin_x
    y_to_rel   = y_to_abs   - origin_y

    USE_KM = False
    scale = 0.001 if USE_KM else 1.0
    unit_label = "km" if USE_KM else "m"

    x_from_rel *= scale; y_from_rel *= scale
    x_to_rel   *= scale; y_to_rel   *= scale
    node_x_rel *= scale; node_y_rel *= scale

    df_plot = df_trans.assign(
        x_from=x_from_rel, y_from=y_from_rel,
        x_to=x_to_rel,     y_to=y_to_rel
    )
else:
    USE_KM = False
    scale = 0.001 if USE_KM else 1.0
    unit_label = "km" if USE_KM else "m"
    node_x_rel *= scale; node_y_rel *= scale


FIGSIZE = (10, 8)
DPI = 600
NODE_SIZE = 18
LABEL_FS = 9
LABEL_OFFSET_PT = 4

fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)

if has_edges:
    cap_max = df_trans["Flow capacity (kW)"].max()
    has_cap = pd.notna(cap_max) and (cap_max > 0)
    for _, r in df_plot.iterrows():
        width = 1 + 3 * (r["Flow capacity (kW)"] / cap_max) if has_cap else 2
        ax.plot(
            [r.x_from, r.x_to],
            [r.y_from, r.y_to],
            linewidth=width,
            color=tech_color(r.techs, fallback="tab:blue"),
            alpha=0.9,
            zorder=2,
        )


ax.scatter(
    node_x_rel,
    node_y_rel,
    color="black",
    s=NODE_SIZE,
    zorder=3,
)

for (node, nx, ny) in zip(coords.index.astype(str), node_x_rel, node_y_rel):
    ax.annotate(
        text=str(node),
        xy=(nx, ny),
        xytext=(0, LABEL_OFFSET_PT),
        textcoords="offset points",
        ha="center", va="bottom",
        fontsize=LABEL_FS, color="black",
        zorder=4,
        clip_on=False,
    )

ax.set_title("System Configuration")
ax.set_xlabel(f"Relative X ({unit_label})")
ax.set_ylabel(f"Relative Y ({unit_label})")
ax.set_aspect("equal", adjustable="box")
ax.margins(y=0.06)

try:
    ax.ticklabel_format(useOffset=False, style="plain", axis="both")
except Exception:
    pass

plt.tight_layout()
OUTDIR.mkdir(parents=True, exist_ok=True)
plt.savefig(OUTDIR / ("transmission_map.png" if has_edges else "nodes_map.png"))
plt.close()

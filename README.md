# Optimisation-of-Local-Energy-Communities
This is a repository with a Calliope model for the optimal design of Local Energy Communities operating in self consumption, with a case study applied in Cyprus. The model examines five configurations:
  - Configuration A: This is a business-as-usual configuration with electricity provided only from the grid and will be used only for comparison
  - Configuration B: Decentralised configuration where each user (if technically possible) can become a prosumer, without any collective generation and consumption (this configuration is not considered an energy community)
  - Configuration C: Decentralised configuration with electricity exchange between users via a collective self-consumption scheme, as a local energy community
  - Configuration D: District configuration where a central PV park is installed at a plot to serve the local energy community
  - Configuration E: It is assumed that energy generation and storage technologies can be installed at buildings, and at a nearby plot acting as central node that allows users to share energy virtually

The model is based on the [Calliope energy modelling framework](https://github.com/calliope-project/calliope) and has the same license (Apache 2.0). To install and run Calliope follow the instructions in the documentation.

The repository has the following structure:
- Datasets
  - Loads (including the code to generate synthetic loads if needed)
  - CY Ramp Results for the calculation of EV data
  - Energy modelling data (all data required for the optimisation model and the code to generate typical days)
- Optimisation model
  - Deterministic model
    - A script called Calliope_script_model_run_final.py that the user can run to solve the problem. This will generate a folder with all the results of the model in csv and a folder called plots with all plots as pictures and html files.
    - Files:
      - model_config: This folder contains the yaml files with locations and techs of the model
      - data_tables: This folder contains the csv files with all relative datasets
      - A yaml file called model_scen which provides the main model file for each configuration
      - A set of yaml files containing additional math required by the model
  - Uncertainty model
    - Files:
    - A script called Calliope_script_model_run_MC.py that the user can use to run Monte Carlo simulations. Within the script the user can define the key parameters and the probability distributions.
    - A script called Results_process_MC.py that the user can use to generate a NetCDF file with all available results after 1000 simulations and will be used for postprocessing
    - Files:
      - model_config: This folder contains the yaml files with locations and techs of the model
      - data_tables: This folder contains the csv files with all relative datasets
      - A yaml file called model_scen which provides the main model file for each configuration
      - A set of yaml files containing additional math required by the model
  - Postprocessing:
    - Deterministic results:
      - Scripts:
        - Deterministic_Results_process - capacity.py: used to generate figures and tables of the capacity of technologies
        - Deterministic_Results_process - cost.py: used to generate the figures and tables of the system costs
        - Deterministic_Results_process - indicators.py: a script used to calculate the relevant indicators for the evaluation of the model (e.g. self-sufficiency)
      - Uncertainty_results:
        - Results_process_MC_plots.py: a script used to read the NetCDF files and generates plots for totaly system costs, solar PV capacity, and batteries capacities.

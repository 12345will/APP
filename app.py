import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yaml

# --- Load Config ---
@st.cache_data
def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

config = load_config()

# --- Sidebar Inputs ---
st.sidebar.title("Factory Scenario Configuration")
factory = st.sidebar.selectbox("Factory Location", ["India", "UK", "Global Average"])
timeline_mode = st.sidebar.radio("Select Time Mode", ["Yearly", "Cumulative (2026–2035)"])
if timeline_mode == "Yearly":
    year = st.sidebar.selectbox("Select Year", list(range(2026, 2036)))
    year_range = [year]
else:
    year_range = list(range(2026, 2036))

energy_mix = st.sidebar.radio("Energy Sourcing Strategy", ["100% Grid", "Grid + PPA (70:30)", "Grid + Gas Backup (70:30)"])
total_cells_produced = st.sidebar.number_input("Total Cells Produced per Year", value=4150000, step=100000)
mla_pct = st.sidebar.slider("% MLA", 0, 100, 50)
ema_pct = 100 - mla_pct
phev_pct = st.sidebar.slider("% PHEV", 0, 100, 50)
mhev_pct = 100 - phev_pct
if timeline_mode == "Yearly" and year > 2030:
    mhev_pct = 0

battery_chemistry = st.sidebar.selectbox("Battery Chemistry", ["LFP", "NMC 622", "NMC 811"])
cells_per_pack = st.sidebar.number_input("Cells per Pack", value=100, step=10)
pack_kwh = st.sidebar.number_input("kWh per Pack", value=60.0, step=1.0)
carbon_price_scenario = st.sidebar.selectbox("Carbon Price Scenario", ["Low", "Medium", "High"])

# --- Load Config Variables ---
energy_demand_per_cell_kwh = config["energy_demand_per_cell_kwh"]
grid_factor = config["energy_emission_factors"]["Grid"][factory]
ppa_factor = config["energy_emission_factors"]["PPA"]
gas_factor = config["energy_emission_factors"]["Gas"]
scope1_factor = config["scope1_emission_factor"]
chemistry_ef = config["battery_chemistry_emissions"]
energy_costs = config["energy_costs_eur_per_kwh"]
carbon_prices = config["carbon_price_paths"][carbon_price_scenario]

# --- Run Model ---
def run_simulation(years):
    results = []
    for yr in years:
        energy_gwh = total_cells_produced * energy_demand_per_cell_kwh
        scope1 = energy_gwh * scope1_factor
        if energy_mix == "100% Grid":
            scope2 = energy_gwh * grid_factor
            energy_cost = energy_gwh * 1000 * energy_costs["Grid"]
        elif energy_mix == "Grid + PPA (70:30)":
            scope2 = energy_gwh * (0.7 * grid_factor + 0.3 * ppa_factor)
            energy_cost = energy_gwh * 1000 * (0.7 * energy_costs["Grid"] + 0.3 * energy_costs["PPA"])
        else:
            scope2 = energy_gwh * (0.7 * grid_factor + 0.3 * gas_factor)
            energy_cost = energy_gwh * 1000 * (0.7 * energy_costs["Grid"] + 0.3 * energy_costs["Gas"])
        total_kwh = (total_cells_produced / cells_per_pack) * pack_kwh
        scope3 = (total_kwh * chemistry_ef[battery_chemistry]) / 1000
        total_emissions = scope1 + scope2 + scope3
        carbon_price = carbon_prices[int(yr)]
        carbon_cost = total_emissions * carbon_price

        results.append({
            "Year": yr,
            "Scope 1 (tCO₂)": round(scope1, 2),
            "Scope 2 (tCO₂)": round(scope2, 2),
            "Scope 3 (tCO₂)": round(scope3, 2),
            "Total Emissions (tCO₂)": round(total_emissions, 2),
            "Carbon Cost (€)": round(carbon_cost, 2),
            "Energy Cost (€)": round(energy_cost, 2)
        })
    return pd.DataFrame(results)

# --- Display Results ---
df_results = run_simulation(year_range)

st.title("🔋 Battery Manufacturing Carbon Scenario Tool")
st.subheader(f"Results for Factory: {factory}, Chemistry: {battery_chemistry}")
st.dataframe(df_results)

if len(df_results) > 1:
    st.subheader("📈 Emissions and Carbon Cost Over Time")
    st.line_chart(df_results.set_index("Year")[["Total Emissions (tCO₂)", "Carbon Cost (€)"]])

st.markdown("---")
st.markdown("📄 Edit assumptions in the *Edit_Config* tab.")

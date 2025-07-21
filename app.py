import streamlit as st
import pandas as pd

# --- Sidebar Inputs ---
st.sidebar.title("Factory Scenario Configuration")

# 1. Factory Selection
factory = st.sidebar.selectbox("Factory Location", ["India", "UK", "Global Average"])

# 2. Year or Cumulative Range
timeline_mode = st.sidebar.radio("Select Time Mode", ["Yearly", "Cumulative"])
if timeline_mode == "Yearly":
    year = st.sidebar.selectbox("Select Year", [2026, 2030, 2035])
else:
    year_range = st.sidebar.multiselect("Select Years", [2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035], default=[2026, 2030, 2035])

# 3. Energy Mix Strategy
energy_mix = st.sidebar.radio("Energy Sourcing Strategy", ["100% Grid", "Grid + PPA (70:30)", "Grid + Gas Backup (70:30)"])

# 4. Production Mix
total_cells_produced = st.sidebar.number_input("Total Cells Produced per Year", value=4150000, step=100000)
mla_pct = st.sidebar.slider("% MLA", 0, 100, 50)
ema_pct = 100 - mla_pct

phev_pct = st.sidebar.slider("% PHEV", 0, 100, 50)
mhev_pct = 100 - phev_pct

# Constraint after 2030
if timeline_mode == "Yearly" and year > 2030:
    mhev_pct = 0

# 5. Battery Chemistry
battery_chemistry = st.sidebar.selectbox("Battery Chemistry", ["LFP", "NMC 622", "NMC 811"])

# 6. Pack Configuration
cells_per_pack = st.sidebar.number_input("Cells per Pack", value=100, step=10)
pack_kwh = st.sidebar.number_input("kWh per Pack", value=60.0, step=1.0)

# 7. Carbon Price Selection
carbon_price_scenario = st.sidebar.selectbox("Carbon Price Scenario", ["Low (€50)", "Medium (€100)", "High (€150)"])
carbon_price_dict = {"Low (€50)": 50, "Medium (€100)": 100, "High (€150)": 150}
carbon_price = carbon_price_dict[carbon_price_scenario]

# --- Constants (Mocked for Now) ---
energy_demand_per_cell_kwh = 0.01  # GWh per cell
grid_emission_factor = 0.7         # tCO2/MWh
ppa_emission_factor = 0.05
gas_emission_factor = 0.25

chemistry_emission_factors = {
    "LFP": 55,     # kg CO2 per kWh
    "NMC 622": 75,
    "NMC 811": 85
}

energy_costs = {
    "Grid": 0.10,   # €/kWh
    "PPA": 0.07,
    "Gas": 0.09
}

# --- Emission & Cost Calculation ---
st.title("Battery Manufacturing Carbon Scenario Tool")

# Convert total cells to GWh of demand
annual_energy_demand_gwh = total_cells_produced * energy_demand_per_cell_kwh

# Scope 2 Emissions & Energy Cost
if energy_mix == "100% Grid":
    scope2_emissions = annual_energy_demand_gwh * grid_emission_factor
    energy_cost = annual_energy_demand_gwh * 1000 * energy_costs["Grid"]
elif energy_mix == "Grid + PPA (70:30)":
    scope2_emissions = (annual_energy_demand_gwh * 0.7 * grid_emission_factor +
                        annual_energy_demand_gwh * 0.3 * ppa_emission_factor)
    energy_cost = (annual_energy_demand_gwh * 1000 * 0.7 * energy_costs["Grid"] +
                   annual_energy_demand_gwh * 1000 * 0.3 * energy_costs["PPA"])
elif energy_mix == "Grid + Gas Backup (70:30)":
    scope2_emissions = (annual_energy_demand_gwh * 0.7 * grid_emission_factor +
                        annual_energy_demand_gwh * 0.3 * gas_emission_factor)
    energy_cost = (annual_energy_demand_gwh * 1000 * 0.7 * energy_costs["Grid"] +
                   annual_energy_demand_gwh * 1000 * 0.3 * energy_costs["Gas"])

# Scope 3: Materials
total_kwh = (total_cells_produced / cells_per_pack) * pack_kwh
scope3_emissions = (total_kwh * chemistry_emission_factors[battery_chemistry]) / 1000  # in tCO2

# Scope 1 (mocked for now)
scope1_emissions = annual_energy_demand_gwh * 0.1

# Total emissions and cost
total_emissions = scope1_emissions + scope2_emissions + scope3_emissions
carbon_cost = total_emissions * carbon_price

# --- Display Results ---
st.subheader("Scenario Results")
st.metric("Scope 1 Emissions (tCO₂)", f"{scope1_emissions:,.0f}")
st.metric("Scope 2 Emissions (tCO₂)", f"{scope2_emissions:,.0f}")
st.metric("Scope 3 Emissions (tCO₂)", f"{scope3_emissions:,.0f}")
st.metric("Total Emissions (tCO₂)", f"{total_emissions:,.0f}")
st.metric("Estimated Carbon Cost (€)", f"{carbon_cost:,.0f}")
st.metric("Annual Energy Cost (€)", f"{energy_cost:,.0f}")

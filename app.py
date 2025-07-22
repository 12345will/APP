import streamlit as st
import pandas as pd

st.set_page_config(page_title="Agratas Carbon & Cost Scenario Tool", layout="wide")
st.title("Agratas Carbon Sensitivity & Scenario Analysis (2026–2035)")

# Sidebar for configuration
st.sidebar.header("🔧 Model Configuration")

# ------------------ SIDEBAR CONFIGURATION ------------------
factory = st.sidebar.selectbox("Factory Location", ["India", "UK", "Global Average"])
year_mode = st.sidebar.radio("Year Mode", ["Single Year", "Cumulative (2026–YYYY)"])
selected_year = st.sidebar.slider("Select Year", min_value=2026, max_value=2035, value=2026)
num_lines = st.sidebar.slider("Number of Manufacturing Lines", 1, 10, 2)
cells_per_line = 4_150_000

mla_percent = st.sidebar.slider("% MLA production", 0, 100, 50)
phev_percent = st.sidebar.slider("% of cells for PHEV", 0, 100, 100 if selected_year > 2030 else 60)
mhev_percent = 0 if selected_year > 2030 else 100 - phev_percent

energy_mix = st.sidebar.selectbox("Energy Strategy", ["100% Grid", "Grid + Renewable PPA (70:30)", "Grid + Gas Backup (30%)"])
grid_emission = st.sidebar.number_input("Grid Emission Factor (tCO₂/kWh)", value=0.21)
renewable_emission = st.sidebar.number_input("Renewable Emission Factor (tCO₂/kWh)", value=0.05)
gas_emission = st.sidebar.number_input("Gas Emission Factor (tCO₂/kWh)", value=0.20)

grid_cost = st.sidebar.number_input("Grid Cost (€/kWh)", value=0.10)
renew_cost = st.sidebar.number_input("Renewable Cost (€/kWh)", value=0.08)
gas_cost = st.sidebar.number_input("Gas Cost (€/kWh)", value=0.12)

pack_kwh = st.sidebar.number_input("Pack capacity (kWh)", value=50.0)
cells_per_pack = st.sidebar.number_input("Cells per pack", value=100.0)
chemistry = st.sidebar.selectbox("Battery Chemistry", ["LFP", "NMC 811", "NMC 622"])

scope1_emission_factor = st.sidebar.number_input("Scope 1 emission factor (tCO₂/kWh)", value=0.18)
carbon_price = st.sidebar.number_input("Carbon price (€/tCO₂)", value=80.0)

# Material inputs
total_cells = num_lines * cells_per_line * (selected_year - 2025 if year_mode.startswith("Cumulative") else 1)

st.sidebar.subheader("Materials per Cell (kg)")
lithium = st.sidebar.number_input("Lithium", value=0.0)
nickel = st.sidebar.number_input("Nickel", value=0.0)
cobalt = st.sidebar.number_input("Cobalt", value=0.0)
manganese = st.sidebar.number_input("Manganese", value=0.0)
graphite = st.sidebar.number_input("Graphite", value=0.0)
aluminum = st.sidebar.number_input("Aluminum", value=0.0)
copper = st.sidebar.number_input("Copper", value=0.0)

# Material CO₂ factors (tCO₂/ton)
co2_per_kg = {
    "lithium": st.sidebar.number_input("tCO₂/ton - Lithium", value=5.0),
    "nickel": st.sidebar.number_input("tCO₂/ton - Nickel", value=8.0),
    "cobalt": st.sidebar.number_input("tCO₂/ton - Cobalt", value=10.0),
    "manganese": st.sidebar.number_input("tCO₂/ton - Manganese", value=4.0),
    "graphite": st.sidebar.number_input("tCO₂/ton - Graphite", value=2.5),
    "aluminum": st.sidebar.number_input("tCO₂/ton - Aluminum", value=9.0),
    "copper": st.sidebar.number_input("tCO₂/ton - Copper", value=3.5)
}

# ------------------ MAIN DISPLAY ------------------
if year_mode == "Cumulative (2026–YYYY)":
    year_range = list(range(2026, selected_year + 1))
else:
    year_range = [selected_year]

# Emission and energy cost logic
if energy_mix == "100% Grid":
    emission_factor = grid_emission
    energy_cost = grid_cost
elif energy_mix == "Grid + Renewable PPA (70:30)":
    emission_factor = 0.7 * grid_emission + 0.3 * renewable_emission
    energy_cost = 0.7 * grid_cost + 0.3 * renew_cost
elif energy_mix == "Grid + Gas Backup (30%)":
    emission_factor = 0.7 * grid_emission + 0.3 * gas_emission
    energy_cost = 0.7 * grid_cost + 0.3 * gas_cost

# Energy and emissions calculations
total_energy_kwh = (total_cells / cells_per_pack) * pack_kwh
total_energy_mwh = total_energy_kwh / 1000
scope2_emissions = total_energy_kwh * emission_factor
scope1_emissions = total_energy_kwh * scope1_emission_factor * 0.05

material_weights = {
    "lithium": lithium,
    "nickel": nickel,
    "cobalt": cobalt,
    "manganese": manganese,
    "graphite": graphite,
    "aluminum": aluminum,
    "copper": copper
}
scope3_emissions = sum((total_cells * kg * (co2_per_kg[mat]/1000)) for mat, kg in material_weights.items())
total_emissions = scope1_emissions + scope2_emissions + scope3_emissions

# Business cost outputs
total_carbon_cost = total_emissions * carbon_price
energy_cost_total = total_energy_kwh * energy_cost

# ------------------ RESULTS ------------------
st.header("Scenario Outputs")
st.subheader("Emissions")
st.metric("Scope 1 Emissions (tCO₂)", f"{scope1_emissions:,.0f}")
st.metric("Scope 2 Emissions (tCO₂)", f"{scope2_emissions:,.0f}")
st.metric("Scope 3 Emissions (tCO₂)", f"{scope3_emissions:,.0f}")
st.metric("Total Emissions (tCO₂)", f"{total_emissions:,.0f}")

st.subheader("Cost to Business")
st.metric("Total Carbon Cost (€)", f"€{total_carbon_cost:,.0f}")
st.metric("Total Energy Cost (€)", f"€{energy_cost_total:,.0f}")

st.success("Adjust configuration in the sidebar to explore different scenarios.")

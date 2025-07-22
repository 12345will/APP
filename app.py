import streamlit as st
import pandas as pd

st.set_page_config(page_title="Agratas Carbon & Cost Scenario Tool")
st.title("Agratas Carbon Sensitivity & Scenario Analysis (2026–2035)")

# ------------------ SECTION 1: FACTORY & YEAR ------------------
st.header("1. Factory Selection and Timeline")

factory = st.selectbox("Select Factory Location", ["India", "UK", "Global Average"])
year_mode = st.radio("Select Year Mode", ["Single Year", "Cumulative (2026–YYYY)"])
selected_year = st.slider("Select Year", min_value=2026, max_value=2035, value=2026)

if year_mode == "Cumulative (2026–YYYY)":
    year_range = list(range(2026, selected_year + 1))
    st.write(f"Cumulative period: {year_range[0]}–{year_range[-1]} ({len(year_range)} years)")
else:
    year_range = [selected_year]

# Factory emission settings (placeholders for actual data)
factory_data = {
    "India": {"grid_intensity": 0.75, "waste_heat": 0.10, "renewables": 0.60},
    "UK": {"grid_intensity": 0.21, "waste_heat": 0.20, "renewables": 0.80},
    "Global Average": {"grid_intensity": 0.45, "waste_heat": 0.15, "renewables": 0.70}
}

factory_profile = factory_data[factory]

# ------------------ SECTION 2: ENERGY SOURCING STRATEGY ------------------
st.header("2. Energy Sourcing Strategy")

energy_mix = st.selectbox("Select Energy Strategy", ["100% Grid", "Grid + Renewable PPA (70:30)", "Grid + Gas Backup (30%)"])

grid_emission = factory_profile["grid_intensity"]  # tCO2/kWh
renewable_emission = st.number_input("Renewable PPA emission factor (tCO₂/kWh)", value=0.05)
gas_emission = st.number_input("Gas emission factor (tCO₂/kWh)", value=0.20)

grid_cost = st.number_input("Grid electricity cost (€/kWh)", value=0.10)
renew_cost = st.number_input("Renewable PPA cost (€/kWh)", value=0.08)
gas_cost = st.number_input("Gas cost (€/kWh)", value=0.12)

if energy_mix == "100% Grid":
    emission_factor = grid_emission
    energy_cost = grid_cost
elif energy_mix == "Grid + Renewable PPA (70:30)":
    emission_factor = 0.7 * grid_emission + 0.3 * renewable_emission
    energy_cost = 0.7 * grid_cost + 0.3 * renew_cost
elif energy_mix == "Grid + Gas Backup (30%)":
    emission_factor = 0.7 * grid_emission + 0.3 * gas_emission
    energy_cost = 0.7 * grid_cost + 0.3 * gas_cost

# ------------------ SECTION 3: BATTERY PRODUCTION CONFIGURATION ------------------
st.header("3. Battery Production Setup")

num_lines = st.slider("Number of Manufacturing Lines", 1, 10, 2)
cells_per_line = 4_150_000

mla_percent = st.slider("% MLA production", 0, 100, 50)
ema_percent = 100 - mla_percent

phev_percent = st.slider("% of cells for PHEV (MHEV disabled after 2030)", 0, 100, 100 if selected_year > 2030 else 60)
mhev_percent = 0 if selected_year > 2030 else 100 - phev_percent

# ------------------ SECTION 4: BATTERY PACK CONFIGURATION ------------------
st.header("4. Battery Pack Configuration")

chemistry = st.selectbox("Battery Chemistry", ["LFP", "NMC 811", "NMC 622"])
pack_kwh = st.number_input("Pack capacity (kWh)", value=50.0)
cells_per_pack = st.number_input("Number of cells per pack", value=100.0)

# Materials per cell input (kg)
st.subheader("Material Breakdown per Cell (kg)")
lithium = st.number_input("Lithium", value=0.0)
nickel = st.number_input("Nickel", value=0.0)
cobalt = st.number_input("Cobalt", value=0.0)
manganese = st.number_input("Manganese", value=0.0)
graphite = st.number_input("Graphite", value=0.0)
aluminum = st.number_input("Aluminum", value=0.0)
copper = st.number_input("Copper", value=0.0)

# ------------------ SECTION 5: EMISSIONS CALCULATION ENGINE ------------------
st.header("5. Emissions & Cost Calculation")

total_cells = num_lines * cells_per_line * len(year_range)
total_energy_mwh = (total_cells / cells_per_pack) * pack_kwh / 1000  # MWh
total_energy_kwh = total_energy_mwh * 1000

scope2_emissions = total_energy_kwh * emission_factor  # tCO₂
scope1_emission_factor = st.number_input("Scope 1 emission factor (tCO₂/kWh)", value=0.18)
scope1_emissions = total_energy_kwh * scope1_emission_factor * 0.05  # example on-site fraction

# Scope 3 emissions (materials)
st.subheader("Scope 3 Emissions from Materials")
co2_per_kg = {
    "lithium": st.number_input("tCO₂/ton - Lithium", value=5.0),
    "nickel": st.number_input("tCO₂/ton - Nickel", value=8.0),
    "cobalt": st.number_input("tCO₂/ton - Cobalt", value=10.0),
    "manganese": st.number_input("tCO₂/ton - Manganese", value=4.0),
    "graphite": st.number_input("tCO₂/ton - Graphite", value=2.5),
    "aluminum": st.number_input("tCO₂/ton - Aluminum", value=9.0),
    "copper": st.number_input("tCO₂/ton - Copper", value=3.5)
}

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

# ------------------ SECTION 6: COST TO BUSINESS ------------------
st.header("6. Cost to Business")
carbon_price = st.number_input("Carbon price (€/tCO₂)", value=80.0)
total_carbon_cost = total_emissions * carbon_price
energy_cost_total = total_energy_kwh * energy_cost

# ------------------ SECTION 7: OUTPUTS ------------------
st.header("7. Scenario Outputs")

st.subheader("Emissions Summary")
st.metric("Scope 1 Emissions (tCO₂)", f"{scope1_emissions:,.0f}")
st.metric("Scope 2 Emissions (tCO₂)", f"{scope2_emissions:,.0f}")
st.metric("Scope 3 Emissions (tCO₂)", f"{scope3_emissions:,.0f}")
st.metric("Total Emissions (tCO₂)", f"{total_emissions:,.0f}")

st.subheader("Cost Summary")
st.metric("Total Carbon Cost (€)", f"€{total_carbon_cost:,.0f}")
st.metric("Total Energy Cost (€)", f"€{energy_cost_total:,.0f}")

st.success("Scenario simulation complete. Adjust inputs to test new assumptions or compare alternatives.")

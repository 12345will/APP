import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Agratas Carbon & Cost Scenario Tool", layout="wide")

# ------------------ INIT SESSION STATE ------------------
def init_session():
    defaults = {
        "factory": "India",
        "year_mode": "Single Year",
        "selected_year": 2026,
        "mla_percent": 50,
        "phev_percent": 60,
        "grid_cost": 0.10,
        "renew_cost": 0.08,
        "gas_cost": 0.12,
        "mla_pack_kwh": 122,
        "ema_pack_kwh": 114,
        "mla_cells_per_pack": 344,
        "ema_cells_per_pack": 188,
        "chemistry": "LFP",
        "scope1_emission_factor": 0.18,
        "carbon_price": 80.0,
        "grid_emission_factor": 70.0,
        "electricity_mix": "100% Grid",
        "materials": {
            "lithium": 0.0,
            "nickel": 0.0,
            "cobalt": 0.0,
            "manganese": 0.0,
            "graphite": 0.0,
            "aluminum": 0.0,
            "copper": 0.0
        },
        "co2_per_kg": {
            "lithium": 5.0,
            "nickel": 8.0,
            "cobalt": 10.0,
            "manganese": 4.0,
            "graphite": 2.5,
            "aluminum": 9.0,
            "copper": 3.5
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ------------------ PAGE SELECTION ------------------
page = st.sidebar.radio("Navigate", ["Input Settings", "Scenario Outputs"])

# ------------------ FIXED ANNUAL ENERGY DEMAND FOR UK (GWh) ------------------
custom_uk_energy = {
    2026: 100,
    2027: 125,
    2028: 130,
    2029: 135,
    2030: 140,
    2031: 145,
    2032: 140,
    2033: 135,
    2034: 130,
    2035: 125,
}

# ------------------ FIXED EMISSION FACTORS FOR 100% GRID (tCO2/GWh) ------------------
custom_emission_factors = {
    2026: 70,
    2027: 68.0,
    2028: 65.0,
    2029: 62.0,
    2030: 60.0,
    2031: 58.0,
    2032: 55.0,
    2033: 52.0,
    2034: 50.0,
    2035: 48.0,
}

# ------------------ INPUT PAGE ------------------
if page == "Input Settings":
    st.title("⚙️ Model Configuration")
    st.session_state.factory = st.selectbox("Factory Location", ["India", "UK", "Global Average"], index=["India", "UK", "Global Average"].index(st.session_state.factory))
    st.session_state.year_mode = st.radio("Year Mode", ["Single Year", "Cumulative (2026–YYYY)"], index=["Single Year", "Cumulative (2026–YYYY)"].index(st.session_state.year_mode))
    st.session_state.selected_year = st.slider("Select Year", 2026, 2035, value=st.session_state.selected_year)
    st.session_state.mla_percent = st.slider("% MLA production", 0, 100, value=st.session_state.mla_percent)
    st.session_state.phev_percent = st.slider("% of cells for PHEV", 0, 100, value=st.session_state.phev_percent)

    st.subheader("Energy Sourcing")
    electricity_options = ["100% Grid", "PPA : Grid (70:30)", "Grid + Gas (30% demand)"]
    st.session_state.electricity_mix = st.radio("Electricity Sourcing Strategy", electricity_options, index=electricity_options.index(st.session_state.electricity_mix))

    st.session_state.grid_cost = st.number_input("Grid Cost (€/kWh)", value=st.session_state.grid_cost)
    st.session_state.renew_cost = st.number_input("Renewable Cost (€/kWh)", value=st.session_state.renew_cost)
    st.session_state.gas_cost = st.number_input("Gas Cost (€/kWh)", value=st.session_state.gas_cost)
    st.session_state.grid_emission_factor = st.number_input("Grid Emission Factor (tCO₂/GWh)", value=st.session_state.grid_emission_factor)
    st.info("To override yearly emission factors for 100% Grid, edit the `custom_emission_factors` dictionary in code.")

    st.subheader("Battery Pack & Materials")
    st.session_state.mla_pack_kwh = st.number_input("MLA Pack capacity (kWh)", value=st.session_state.mla_pack_kwh)
    st.session_state.ema_pack_kwh = st.number_input("EMA Pack capacity (kWh)", value=st.session_state.ema_pack_kwh)
    st.session_state.mla_cells_per_pack = st.number_input("MLA Cells per pack", value=st.session_state.mla_cells_per_pack)
    st.session_state.ema_cells_per_pack = st.number_input("EMA Cells per pack", value=st.session_state.ema_cells_per_pack)
    st.session_state.chemistry = st.selectbox("Battery Chemistry", ["LFP", "NMC 811", "NMC 622"], index=["LFP", "NMC 811", "NMC 622"].index(st.session_state.chemistry))

    for mat in st.session_state.materials:
        st.session_state.materials[mat] = st.number_input(f"{mat.capitalize()} per cell (kg)", value=st.session_state.materials[mat])
    for mat in st.session_state.co2_per_kg:
        st.session_state.co2_per_kg[mat] = st.number_input(f"tCO₂/ton - {mat.capitalize()}", value=st.session_state.co2_per_kg[mat])

    st.session_state.scope1_emission_factor = st.number_input("Scope 1 Emission Factor (tCO₂/kWh)", value=st.session_state.scope1_emission_factor)
    st.session_state.carbon_price = st.number_input("Carbon Price (€/tCO₂)", value=st.session_state.carbon_price)

# ------------------ OUTPUT PAGE ------------------
else:
    st.title("📊 Scenario Outputs")

    year_range = list(range(2026, st.session_state.selected_year + 1)) if st.session_state.year_mode.startswith("Cumulative") else [st.session_state.selected_year]

    total_scope3_emissions = 0
    total_scope1_scope2 = 0

    for y in year_range:
        uk_energy = custom_uk_energy[y]
        emission_factor = custom_emission_factors[y]

        if st.session_state.factory == "India":
            energy_demand = uk_energy * 1.5
        elif st.session_state.factory == "Global Average":
            energy_demand = (uk_energy + uk_energy * 1.5) / 2
        else:
            energy_demand = uk_energy

        if st.session_state.electricity_mix == "100% Grid":
            emission_factor = custom_emission_factors[y]
            scope1_scope2 = energy_demand * emission_factor
        elif st.session_state.electricity_mix == "PPA : Grid (70:30)":
            scope1_scope2 = 41.13761 * (energy_demand ** 0.551674)
        elif st.session_state.electricity_mix == "Grid + Gas (30% demand)":
            scope1_scope2 = 596.09563 * (energy_demand ** 0.423023)
        else:
            scope1_scope2 = energy_demand * custom_emission_factors[y]
            
        total_scope1_scope2 += scope1_scope2

        for mat, kg_per_cell in st.session_state.materials.items():
            tons_total = (kg_per_cell * 4_150_000 * 2) / 1000
            co2_per_ton = st.session_state.co2_per_kg.get(mat, 0)
            total_scope3_emissions += tons_total * co2_per_ton

    total_emissions_all = total_scope1_scope2 + total_scope3_emissions
    carbon_cost = total_scope1_scope2 * st.session_state.carbon_price

    st.header("📌 Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Emissions (tCO₂)", f"{total_emissions_all:,.0f}")
    col2.metric("Carbon Cost (€)", f"{carbon_cost:,.0f}")
    col3.metric("Years Covered", f"{len(year_range)}")

    st.subheader("🔍 Emissions Breakdown")
    st.write(f"**Scope 1 & 2 Total:** {total_scope1_scope2:,.0f} tCO₂")
    st.write(f"**Scope 3 Materials Total:** {total_scope3_emissions:,.0f} tCO₂")

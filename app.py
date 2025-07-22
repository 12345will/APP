import streamlit as st
import pandas as pd

st.set_page_config(page_title="Agratas Carbon & Cost Scenario Tool", layout="wide")

# ------------------ PAGE SELECTION ------------------
page = st.sidebar.radio("Navigate", ["Input Settings", "Scenario Outputs"])

# ------------------ FIXED ANNUAL CO2 VALUES FOR UK (tCO2) ------------------
custom_uk_emissions = {
    "100% Grid": {
        2026: 610,
        2027: 20037,
        2028: 21018,
        2029: 17757,
        2030: 22280,
        2031: 18719,
        2032: 14743,
        2033: 11701,
        2034: 9412,
        2035: 9400,
    },
    "PPA : Grid (70:30)": {
        2026: 242,
        2027: 8598,
        2028: 9436,
        2029: 8457,
        2030: 10941,
        2031: 9873,
        2032: 8680,
        2033: 7768,
        2034: 7081,
        2035: 7000,
    },
    "Grid + Gas (30% demand)": {
        2026: 818,
        2027: 31272,
        2028: 35568,
        2029: 33303,
        2030: 43984,
        2031: 41491,
        2032: 38707,
        2033: 36578,
        2034: 34976,
        2035: 34900,
    }
}

# ------------------ SESSION STATE INIT ------------------
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
        "mla_pack_kwh": 50.0,
        "ema_pack_kwh": 75.0,
        "cells_per_pack": 100.0,
        "chemistry": "LFP",
        "scope1_emission_factor": 0.18,
        "carbon_price": 80.0,
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

# ------------------ INPUT PAGE ------------------
if page == "Input Settings":
    st.title("⚙️ Model Configuration")
    st.session_state.factory = st.selectbox("Factory Location", ["India", "UK", "Global Average"], index=["India", "UK", "Global Average"].index(st.session_state.factory))
    st.session_state.year_mode = st.radio("Year Mode", ["Single Year", "Cumulative (2026–YYYY)"], index=0 if st.session_state.year_mode == "Single Year" else 1)
    st.session_state.selected_year = st.slider("Select Year", min_value=2026, max_value=2035, value=st.session_state.selected_year)
    st.session_state.mla_percent = st.slider("% MLA production", 0, 100, st.session_state.mla_percent)
    st.session_state.phev_percent = st.slider("% of cells for PHEV", 0, 100, 100 if st.session_state.selected_year > 2030 else st.session_state.phev_percent)

    st.subheader("Energy Sourcing")
    electricity_options = list(custom_uk_emissions.keys())
    st.session_state.electricity_mix = st.radio("Electricity Sourcing Strategy", electricity_options, index=electricity_options.index(st.session_state.electricity_mix))

    st.session_state.grid_cost = st.number_input("Grid Cost (€/kWh)", value=st.session_state.grid_cost)
    st.session_state.renew_cost = st.number_input("Renewable Cost (€/kWh)", value=st.session_state.renew_cost)
    st.session_state.gas_cost = st.number_input("Gas Cost (€/kWh)", value=st.session_state.gas_cost)

    st.subheader("Battery Pack & Materials")
    st.session_state.mla_pack_kwh = st.number_input("MLA Pack capacity (kWh)", value=st.session_state.mla_pack_kwh)
    st.session_state.ema_pack_kwh = st.number_input("EMA Pack capacity (kWh)", value=st.session_state.ema_pack_kwh)
    st.session_state.cells_per_pack = st.number_input("Cells per pack", value=st.session_state.cells_per_pack)
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

    # Fixed lines based on factory
    lines_by_factory = {"India": 3, "UK": 2, "Global Average": 2.5}
    num_lines = lines_by_factory.get(st.session_state.factory, 2)

    total_cells = num_lines * 4_150_000 * len(year_range)
    mla_cells = total_cells * (st.session_state.mla_percent / 100)
    ema_cells = total_cells - mla_cells

    phev_percent = st.session_state.phev_percent
    mhev_percent = 0 if st.session_state.selected_year > 2030 else 100 - phev_percent

    # Use fixed annual emissions from UK as base
    annual_emissions = []
    for y in year_range:
        uk_value = custom_uk_emissions[st.session_state.electricity_mix].get(y, 0.0)
        if st.session_state.factory == "UK":
            annual_emissions.append(uk_value)
        elif st.session_state.factory == "India":
            annual_emissions.append((uk_value / 2) * 3)
        else:
            annual_emissions.append((uk_value + ((uk_value / 2) * 3)) / 2)  # avg of UK and India

    scope2_emissions = sum(annual_emissions)

    total_energy_kwh = (mla_cells / st.session_state.cells_per_pack) * st.session_state.mla_pack_kwh + \
                       (ema_cells / st.session_state.cells_per_pack) * st.session_state.ema_pack_kwh

    scope1_emissions = total_energy_kwh * st.session_state.scope1_emission_factor * 0.05

    scope3_emissions = sum((total_cells * st.session_state.materials[mat] * (st.session_state.co2_per_kg[mat] / 1000)) for mat in st.session_state.materials)
    total_emissions = scope1_emissions + scope2_emissions + scope3_emissions

    energy_cost = 0.7 * st.session_state.grid_cost + 0.3 * st.session_state.renew_cost if st.session_state.electricity_mix == "PPA : Grid (70:30)" else \
                  0.7 * st.session_state.grid_cost + 0.3 * st.session_state.gas_cost if st.session_state.electricity_mix == "Grid + Gas (30% demand)" else \
                  st.session_state.grid_cost

    total_carbon_cost = total_emissions * st.session_state.carbon_price
    energy_cost_total = total_energy_kwh * energy_cost

    st.subheader("Emissions")
    st.metric("Scope 1 Emissions (tCO₂)", f"{scope1_emissions:,.0f}")
    st.metric("Scope 2 Emissions (tCO₂)", f"{scope2_emissions:,.0f}")
    st.metric("Scope 3 Emissions (tCO₂)", f"{scope3_emissions:,.0f}")
    st.metric("Total Emissions (tCO₂)", f"{total_emissions:,.0f}")

    st.subheader("Cost to Business")
    st.metric("Total Carbon Cost (€)", f"€{total_carbon_cost:,.0f}")
    st.metric("Total Energy Cost (€)", f"€{energy_cost_total:,.0f}")

    st.success("Adjust values on the Input Settings page to simulate scenarios.")

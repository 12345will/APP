import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Agratas Carbon & Cost Scenario Tool", layout="wide")

# ------------------ PAGE SELECTION ------------------
page = st.sidebar.radio("Navigate", ["Input Settings", "Scenario Outputs"])

# ------------------ FIXED ANNUAL ENERGY DEMAND FOR UK (GWh) ------------------
custom_uk_energy = {
    2026: 6,
    2027: 284,
    2028: 344,
    2029: 344,
    2030: 468,
    2031: 468,
    2032: 468,
    2033: 468,
    2034: 468,
    2035: 468,
}

# ------------------ FIXED EMISSION FACTORS FOR 100% GRID (tCO2/GWh) ------------------
custom_emission_factors = {
    2026: 94.59,
    2027: 70.49,
    2028: 61.10,
    2029: 51.62,
    2030: 47.62,
    2031: 40.01,
    2032: 31.51,
    2033: 25.01,
    2034: 20.12,
    2035: 20.00,
}

# ------------------ EVALUATED EMISSIONS TABLE FOR UK ------------------
def get_uk_emission_table():
    years = list(custom_uk_energy.keys())
    data = {
        "Year": years,
        "UK Energy Demand (GWh)": [custom_uk_energy[y] for y in years],
        "Emission Factor (tCO₂/GWh)": [custom_emission_factors[y] for y in years],
        "Evaluated Emissions (tCO₂)": [custom_uk_energy[y] * custom_emission_factors[y] for y in years],
    }
    return pd.DataFrame(data)

uk_emission_table = get_uk_emission_table()

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

# ------------------ INPUT PAGE ------------------
if page == "Input Settings":
    st.title("⚙️ Model Configuration")

    # ----- Factory & Timeline Selection -----
    st.selectbox("Factory Location", ["India", "UK", "Global Average"], key="factory")
    st.radio("Year Mode", ["Single Year", "Cumulative (2026–YYYY)"], key="year_mode")
    st.slider("Select Year", 2026, 2035, value=st.session_state.selected_year, key="selected_year")
    st.slider("% MLA production", 0, 100, value=st.session_state.mla_percent, key="mla_percent")

    phev_default = 100 if st.session_state.selected_year > 2030 else st.session_state.phev_percent
    st.slider("% of cells for PHEV", 0, 100, value=phev_default, key="phev_percent")

    # ----- Energy Sourcing -----
    st.subheader("Energy Sourcing")
    electricity_options = ["100% Grid", "PPA : Grid (70:30)", "Grid + Gas (30% demand)"]
    st.radio("Electricity Sourcing Strategy", electricity_options, key="electricity_mix")
    st.number_input("Grid Cost (€/kWh)", value=st.session_state.grid_cost, key="grid_cost")
    st.number_input("Renewable Cost (€/kWh)", value=st.session_state.renew_cost, key="renew_cost")
    st.number_input("Gas Cost (€/kWh)", value=st.session_state.gas_cost, key="gas_cost")
    st.number_input("Grid Emission Factor (tCO₂/GWh)", value=st.session_state.grid_emission_factor, key="grid_emission_factor")

    st.info("To override yearly emission factors for 100% Grid, edit the `custom_emission_factors` dictionary in code.")

    # ----- Battery Pack Configuration -----
    st.subheader("Battery Pack & Materials")
    st.number_input("MLA Pack capacity (kWh)", value=st.session_state.mla_pack_kwh, key="mla_pack_kwh")
    st.number_input("EMA Pack capacity (kWh)", value=st.session_state.ema_pack_kwh, key="ema_pack_kwh")
    st.number_input("MLA Cells per pack", value=st.session_state.mla_cells_per_pack, key="mla_cells_per_pack")
    st.number_input("EMA Cells per pack", value=st.session_state.ema_cells_per_pack, key="ema_cells_per_pack")
    st.selectbox("Battery Chemistry", ["LFP", "NMC 811", "NMC 622"], key="chemistry")

    # ----- Materials per Cell -----
    st.subheader("Cell Materials (kg per cell)")
    for mat in st.session_state.materials:
        key = f"mat_{mat}"
        default = st.session_state.materials[mat]
        st.number_input(f"{mat.capitalize()} per cell (kg)", value=default, key=key)

    # ----- CO₂ per Material -----
    st.subheader("Embedded CO₂ (tCO₂ per ton of material)")
    for mat in st.session_state.co2_per_kg:
        key = f"co2_{mat}"
        default = st.session_state.co2_per_kg[mat]
        st.number_input(f"tCO₂/ton - {mat.capitalize()}", value=default, key=key)

    # ----- Policy Parameters -----
    st.number_input("Scope 1 Emission Factor (tCO₂/kWh)", value=st.session_state.scope1_emission_factor, key="scope1_emission_factor")
    st.number_input("Carbon Price (€/tCO₂)", value=st.session_state.carbon_price, key="carbon_price")

# ------------------ OUTPUT PAGE ------------------
else:
    st.title("📊 Scenario Outputs")

    # Determine year range
    year_range = list(range(2026, st.session_state.selected_year + 1)) if st.session_state.year_mode.startswith("Cumulative") else [st.session_state.selected_year]

    # Total cells produced (used for Scope 3)
    lines_by_factory = {"India": 3, "UK": 2, "Global Average": 2.5}
    num_lines = lines_by_factory.get(st.session_state.factory, 2)
    total_cells = num_lines * 4_150_000 * len(year_range)
    mla_cells = total_cells * (st.session_state.mla_percent / 100)
    ema_cells = total_cells - mla_cells

    total_scope3_emissions = 0
    for mat in st.session_state.materials:
        kg_per_cell = st.session_state.get(f"mat_{mat}", 0.0)
        co2_per_ton = st.session_state.get(f"co2_{mat}", 0.0)
        tons_total = (kg_per_cell * total_cells) / 1000
        total_scope3_emissions += tons_total * co2_per_ton

    # Emissions from UK data only (Scope 1 + 2)
    annual_emissions = []
    annual_energy_kwh = []

    for y in year_range:
        uk_energy = custom_uk_energy.get(y, 0)
        emission_factor = custom_emission_factors.get(y, 0)

        # Adjust energy demand by factory
        if st.session_state.factory == "India":
            energy_gwh = (3 / 2) * uk_energy
        elif st.session_state.factory == "Global Average":
            india_energy = (3 / 2) * uk_energy
            energy_gwh = (uk_energy + india_energy) / 2
        else:  # UK
            energy_gwh = uk_energy

        # Step 1: Calculate baseline (100% Grid) emissions
        base_emissions = energy_gwh * emission_factor  # tCO₂

        # Step 2: Apply sourcing adjustment
        if st.session_state.electricity_mix == "100% Grid":
            emissions = base_emissions
        elif st.session_state.electricity_mix == "PPA : Grid (70:30)":
            emissions = -17009.953 + 2667.97408 * math.log(base_emissions)
        elif st.session_state.electricity_mix == "Grid + Gas (30% demand)":
            emissions = -65050.6557 + 10499.4225 * math.log(base_emissions)
        else:
            emissions = base_emissions  # fallback

        annual_emissions.append(emissions)
        annual_energy_kwh.append(energy_gwh * 1_000_000)


    total_scope1_scope2 = sum(annual_emissions)
    total_energy_kwh = sum(annual_energy_kwh)
    carbon_cost = total_scope1_scope2 * st.session_state.carbon_price
    energy_cost = total_energy_kwh * st.session_state.grid_cost
    total_emissions_all = total_scope1_scope2 + total_scope3_emissions

    # OUTPUT METRICS
    st.header("📌 Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Emissions (tCO₂)", f"{total_emissions_all:,.0f}")
    col2.metric("Carbon Cost (€)", f"{carbon_cost:,.0f}")
    col3.metric("Energy Cost (€)", f"{energy_cost:,.0f}")

    st.subheader("🔍 Emissions Breakdown")
    st.write(f"**Scope 1 & 2 (UK-based only):** {total_scope1_scope2:,.0f} tCO₂")
    st.write(f"**Scope 3 Materials:** {total_scope3_emissions:,.0f} tCO₂")

    st.subheader("⚡ Total Energy Demand")
    st.write(f"{total_energy_kwh / 1e6:.2f} GWh")

    # Emissions by year (if cumulative)
    if len(year_range) > 1:
        emissions_df = pd.DataFrame({
            "Year": year_range,
            "UK Energy Demand (GWh)": [custom_uk_energy[y] for y in year_range],
            "Emission Factor (tCO₂/GWh)": [custom_emission_factors[y] for y in year_range],
            "Scope 1 + 2 Emissions (tCO₂)": annual_emissions
        })
        st.line_chart(emissions_df.set_index("Year")["Scope 1 + 2 Emissions (tCO₂)"])

        st.subheader("📄 Detailed Annual Emissions")
        st.dataframe(emissions_df)


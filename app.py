import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Sidebar Inputs ---
st.sidebar.title("Factory Scenario Configuration")

# Factory and Year Settings
factory = st.sidebar.selectbox("Factory Location", ["India", "UK", "Global Average"])

timeline_mode = st.sidebar.radio("Select Time Mode", ["Yearly", "Cumulative (2026–2035)"])
if timeline_mode == "Yearly":
    year = st.sidebar.selectbox("Select Year", list(range(2026, 2036)))
    year_range = [year]
else:
    year_range = list(range(2026, 2036))

# Energy Mix Strategy
energy_mix = st.sidebar.radio("Energy Sourcing Strategy", ["100% Grid", "Grid + PPA (70:30)", "Grid + Gas Backup (70:30)"])

# Production Mix Inputs
total_cells_produced = st.sidebar.number_input("Total Cells Produced per Year", value=4150000, step=100000)
mla_pct = st.sidebar.slider("% MLA", 0, 100, 50)
ema_pct = 100 - mla_pct

phev_pct = st.sidebar.slider("% PHEV", 0, 100, 50)
mhev_pct = 100 - phev_pct
if timeline_mode == "Yearly" and year > 2030:
    mhev_pct = 0

# Chemistry and Pack Settings
battery_chemistry = st.sidebar.selectbox("Battery Chemistry", ["LFP", "NMC 622", "NMC 811"])
cells_per_pack = st.sidebar.number_input("Cells per Pack", value=100, step=10)
pack_kwh = st.sidebar.number_input("kWh per Pack", value=60.0, step=1.0)

# Carbon Pricing
carbon_price_scenario = st.sidebar.selectbox("Carbon Price Scenario", ["Low", "Medium", "High"])
carbon_price_paths = {
    "Low": {yr: 50 + (yr - 2026) * 5 for yr in range(2026, 2036)},
    "Medium": {yr: 75 + (yr - 2026) * 7.5 for yr in range(2026, 2036)},
    "High": {yr: 100 + (yr - 2026) * 10 for yr in range(2026, 2036)}
}

# --- Emissions and Cost Factors (Assumptions & Sources) ---
energy_demand_per_cell_kwh = 0.01  # GWh per cell

# Emission factors (Sources: IEA, NREL, supplier data)
emission_factors = {
    "Grid": {"India": 0.75, "UK": 0.25, "Global Average": 0.50},  # tCO₂/MWh
    "PPA": 0.05,
    "Gas": 0.20
}

# Chemistry emissions (Source: Transport & Environment 2022)
chemistry_emission_factors = {
    "LFP": 55,       # kg CO₂ per kWh
    "NMC 622": 75,
    "NMC 811": 85
}

# Energy costs (€/kWh) — rough assumptions
energy_costs = {
    "Grid": 0.10,
    "PPA": 0.07,
    "Gas": 0.09
}

# --- Simulation Function ---
def run_simulation(years):
    results = []
    for yr in years:
        grid_factor = emission_factors["Grid"][factory]
        ppa_factor = emission_factors["PPA"]
        gas_factor = emission_factors["Gas"]

        # Scope 1 (assume 0.1 tCO₂/GWh on-site fossil fuel use)
        energy_gwh = total_cells_produced * energy_demand_per_cell_kwh
        scope1 = energy_gwh * 0.1

        # Scope 2 (based on mix)
        if energy_mix == "100% Grid":
            scope2 = energy_gwh * grid_factor
            energy_cost = energy_gwh * 1000 * energy_costs["Grid"]
        elif energy_mix == "Grid + PPA (70:30)":
            scope2 = energy_gwh * (0.7 * grid_factor + 0.3 * ppa_factor)
            energy_cost = energy_gwh * 1000 * (0.7 * energy_costs["Grid"] + 0.3 * energy_costs["PPA"])
        else:  # Grid + Gas
            scope2 = energy_gwh * (0.7 * grid_factor + 0.3 * gas_factor)
            energy_cost = energy_gwh * 1000 * (0.7 * energy_costs["Grid"] + 0.3 * energy_costs["Gas"])

        # Scope 3: Material-related
        total_kwh = (total_cells_produced / cells_per_pack) * pack_kwh
        scope3 = (total_kwh * chemistry_emission_factors[battery_chemistry]) / 1000  # tCO₂

        total_emissions = scope1 + scope2 + scope3
        carbon_price = carbon_price_paths[carbon_price_scenario][yr]
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

# --- Run and Display ---
df_results = run_simulation(year_range)

st.title("🔋 Battery Manufacturing Carbon Scenario Tool")
st.subheader(f"Results for Factory: {factory}, Chemistry: {battery_chemistry}")

st.dataframe(df_results)

# --- Chart ---
if len(df_results) > 1:
    st.subheader("📈 Emissions and Carbon Cost Over Time")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_results["Year"], df_results["Total Emissions (tCO₂)"], marker='o', label="Total Emissions")
    ax.plot(df_results["Year"], df_results["Carbon Cost (€)"], marker='s', label="Carbon Cost")
    ax.set_xlabel("Year")
    ax.set_ylabel("tCO₂ / €")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
else:
    st.write("Switch to cumulative mode to view multi-year trends.")

# --- Footer ---
st.markdown("""
**Emission Factors Sources**:
- Grid: IEA (2023), UK BEIS (2022), India CEA reports
- Chemistry Scope 3: Transport & Environment (2022), Argonne GREET (2021)
- Carbon Price Paths: Assumed policy-based trajectories

**Energy Cost Assumptions**:
- Grid: €0.10/kWh, PPA: €0.07/kWh, Gas: €0.09/kWh (IEA + BNEF benchmarks)

*All assumptions can be configured for real-world deployment.*
""")

import streamlit as st
import yaml

CONFIG_FILE = "config.yaml"

st.title("⚙️ Edit Config: Numeric Settings Only")

# Load current config
with open(CONFIG_FILE, "r") as f:
    config = yaml.safe_load(f)

# --- UI: Energy Demand ---
st.subheader("🔋 Energy Demand")
config["energy_demand_per_cell_kwh"] = st.number_input(
    "Energy demand per cell (GWh)", value=config["energy_demand_per_cell_kwh"], step=0.001
)

# --- UI: Emission Factors ---
st.subheader("🌍 Emission Factors (tCO₂/kWh or per GWh)")
for loc in config["energy_emission_factors"]["Grid"]:
    config["energy_emission_factors"]["Grid"][loc] = st.number_input(
        f"Grid Emission Factor - {loc}",
        value=config["energy_emission_factors"]["Grid"][loc],
        step=0.01,
        key=f"grid_{loc}"
    )

config["energy_emission_factors"]["PPA"] = st.number_input(
    "PPA Emission Factor", value=config["energy_emission_factors"]["PPA"], step=0.01
)
config["energy_emission_factors"]["Gas"] = st.number_input(
    "Gas Emission Factor", value=config["energy_emission_factors"]["Gas"], step=0.01
)

config["scope1_emission_factor"] = st.number_input(
    "Scope 1 Emission Factor (tCO₂/GWh)", value=config["scope1_emission_factor"], step=0.01
)

# --- UI: Chemistry Emissions (kg CO₂/kWh) ---
st.subheader("⚗️ Battery Chemistry Emissions (kg CO₂ / kWh)")
for chem in config["battery_chemistry_emissions"]:
    val = float(config["battery_chemistry_emissions"][chem])
    config["battery_chemistry_emissions"][chem] = st.number_input(
        f"{chem} Emission Factor",
        value=val,
        step=1.0,
        key=f"chem_{chem}"
    )

# --- UI: Energy Costs (€/kWh) ---
st.subheader("💸 Energy Costs (€/kWh)")
for source in config["energy_costs_eur_per_kwh"]:
    config["energy_costs_eur_per_kwh"][source] = st.number_input(
        f"{source} Cost",
        value=config["energy_costs_eur_per_kwh"][source],
        step=0.01,
        key=f"cost_{source}"
    )

# --- UI: Carbon Price Paths ---
st.subheader("📈 Carbon Price Paths (€/tCO₂)")
for scenario in config["carbon_price_paths"]:
    st.markdown(f"**{scenario} Scenario**")
    for yr in config["carbon_price_paths"][scenario]:
        val = float(config["carbon_price_paths"][scenario][yr])
        config["carbon_price_paths"][scenario][yr] = st.number_input(
            f"{scenario} {yr}",
            value=val,
            step=5.0,
            key=f"{scenario}_{yr}"
        )

# --- Save Button ---
if st.button("💾 Save Config"):
    try:
        with open(CONFIG_FILE, "w") as f:
            yaml.safe_dump(config, f)
        st.success("✅ Config updated successfully. Return to the Home tab to rerun the simulation.")
    except Exception as e:
        st.error(f"❌ Failed to save config: {e}")

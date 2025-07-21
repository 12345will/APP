import streamlit as st
import yaml

CONFIG_FILE = "config.yaml"

st.title("⚙️ Edit Configuration Settings")

# Load current config
with open(CONFIG_FILE, "r") as f:
    config_text = f.read()

edited_text = st.text_area("Edit YAML Config", config_text, height=500)

if st.button("💾 Save Config"):
    try:
        config_dict = yaml.safe_load(edited_text)
        with open(CONFIG_FILE, "w") as f:
            yaml.safe_dump(config_dict, f)
        st.success("✅ Config updated successfully. You can now go back to 'Home' to run your simulation.")
    except Exception as e:
        st.error(f"❌ YAML syntax error: {e}")

st.markdown("ℹ️ This config controls emission factors, energy costs, and carbon pricing for all simulations.")

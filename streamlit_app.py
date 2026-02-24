import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import json
from scipy.interpolate import CubicSpline
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# --- 1. SELENIUM SCRAPER ENGINE ---
@st.cache_data(ttl=3600)
def get_bond_data_selenium():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://www.worldgovernmentbonds.com/country/czech-republic/')

        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        tables = driver.find_elements(By.TAG_NAME, "table")
        target_df = None

        for table in tables:
            html_content = table.get_attribute('outerHTML')
            # Fix: Wrap literal HTML in StringIO to avoid DeprecationWarning
            df_list = pd.read_html(io.StringIO(html_content))
            if df_list:
                df = df_list[0]
                if any("Maturity" in str(col) for col in df.columns):
                    target_df = df
                    break

        driver.quit()
        return target_df
    except Exception as e:
        return f"Error: {str(e)}"


# --- 2. DATA CLEANING & FINANCIAL MATH ---
def clean_bond_df(df):
    yield_col = [c for c in df.columns if 'Yield' in str(c)][0]
    maturity_col = [c for c in df.columns if 'Maturity' in str(c)][0]

    clean_df = df[[maturity_col, yield_col]].copy()
    clean_df.columns = ["Tenor", "Yield"]

    # Convert Yield string to numeric
    clean_df['Yield_Num'] = clean_df['Yield'].astype(str).str.replace('%', '').str.replace('+', '').str.strip()
    clean_df['Yield_Num'] = pd.to_numeric(clean_df['Yield_Num'], errors='coerce')

    # Map Tenor string to numeric years
    def map_tenor(t):
        t = str(t).upper().strip()
        val_str = "".join(filter(str.isdigit, t))
        if not val_str: return 0.0
        val = float(val_str)
        if 'MONTH' in t or (t.endswith('M') and 'Y' not in t):
            return val / 12
        return val

    clean_df['Years'] = clean_df['Tenor'].apply(map_tenor)

    # Financial calculations
    clean_df['Days'] = (clean_df['Years'] * 360).astype(int)
    # Discount Factor: exp(-r * t)
    clean_df['Discount_Rate'] = np.exp(-(clean_df['Yield_Num'] / 100) * clean_df['Years'])

    return clean_df.dropna().sort_values("Years")


# --- 3. UI LAYOUT ---
st.set_page_config(page_title="CZK Risk Terminal", layout="wide")

st.title("🇨🇿 CZK Sovereign Yield Curve")

# Source Code Expander
with st.expander("🛠️ View Scraper & Spline Source Code"):
    try:
        with open(__file__, "r") as f:
            st.code(f.read(), language="python")
    except:
        st.write("Source code file not readable.")

st.markdown("[Source: World Government Bonds](https://www.worldgovernmentbonds.com/country/czech-republic/)")

with st.spinner("Executing Selenium Scraper & Interpolation..."):
    raw_df = get_bond_data_selenium()

if isinstance(raw_df, pd.DataFrame):
    df = clean_bond_df(raw_df)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Benchmark Table")
        # Fix: width='stretch' for 2026 Streamlit compatibility
        st.dataframe(df[["Tenor", "Yield", "Days", "Discount_Rate"]], width="stretch", hide_index=True)

    with col2:
        st.subheader("Cubic Spline Yield Curve")

        # Cubic Spline Interpolation
        if len(df) >= 3:
            x = df['Years'].values
            y = df['Yield_Num'].values
            cs = CubicSpline(x, y)

            # Generate 100 points for a smooth line
            x_new = np.linspace(x.min(), x.max(), 100)
            y_new = cs(x_new)

            chart_data = pd.DataFrame({"Maturity (Years)": x_new, "Rate (%)": y_new}).set_index("Maturity (Years)")

            st.line_chart(chart_data, x_label="Maturity (Years)", y_label="Yield (%)")
        else:
            # Fallback to standard chart if not enough points
            st.line_chart(df.set_index("Years")["Yield_Num"], x_label="Years", y_label="Rate")

    # --- 4. QUANT JSON DATA ---
    st.divider()
    st.subheader("Quant-Ready JSON Output")

    json_output = {
        "curve_metadata": {
            "name": "CZK_GOVT_BOND_LIVE",
            "interpolation": "Cubic Spline",
            "convention": "ACT/360"
        },
        "data": df.rename(columns={
            "Tenor": "tenor",
            "Yield_Num": "rate_pct",
            "Days": "days",
            "Discount_Rate": "df"
        })[["tenor", "days", "rate_pct", "df"]].to_dict(orient="records")
    }

    st.json(json_output)

else:
    st.error(f"Scraper failed. {raw_df}")
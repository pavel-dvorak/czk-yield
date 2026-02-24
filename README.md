# CZK Government Yield Curve Tool

A lightweight Streamlit application that visualizes the Czech Government Bond yield curve using data from WorldGovernmentBonds.

## 🚀 Features
- **Data Visualization:** Interactive chart showing current yields for various maturities (from 3 months to 50 years).
- **Mathematical Modeling:** Uses **Cubic Spline Interpolation** to create a smooth yield curve from discrete data points.
- **Dual Versioning:** - **Production:** High-speed static version for instant loading.
    - **Development:** Selenium-based scraper for real-time data extraction.

## 🛠️ Tech Stack
- **Language:** Python
- **Frontend:** [Streamlit](https://streamlit.io/)
- **Data Processing:** Pandas, NumPy, SciPy
- **Scraping:** Selenium (Headless Chrome)

## 📁 Project Structure
- `streamlit_app.py`: The main application running on Streamlit Cloud.
- `scraper_logic.py`: The background logic for the Selenium scraper (viewable via the web UI).
- `requirements.txt`: Python dependencies.
- `packages.txt`: System-level packages for headless Chromium support.

## 📈 Mathematics
The yield curve is interpolated using the `CubicSpline` method from the `scipy.interpolate` library:
$$S(x) = a_i + b_i(x - x_i) + c_i(x - x_i)^2 + d_i(x - x_i)^3$$
This ensures a smooth transition between the observed market yields.

---
*Created as a financial risk management tool.*

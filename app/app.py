import streamlit as st
import pandas as pd
import altair as alt

st.title("Welcome to your Investment App")

st.write("""
This is your dashboard.  
Use the sidebar to navigate to different sections of the app.
""")

st.page_link("pages/Portfolio.py", label="Go to Portfolio")

## ---------------------------------------------------------------- ##
##               pie chart for the portfolio assets                 ##
## ---------------------------------------------------------------- ##

st.subheader("Portfolio Allocation")

# Load data
df = pd.read_csv("data/investments.csv")

# Compute total value per asset
df["total_value"] = df["price"] * df["quantity"]

# Group by asset
grouped = df.groupby("asset")["total_value"].sum().reset_index()

# Create pie chart
chart = alt.Chart(grouped).mark_arc().encode(
    theta="total_value",
    color="asset",
    tooltip=["asset", "total_value"]
)

st.altair_chart(chart, use_container_width=True)

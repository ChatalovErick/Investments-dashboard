import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(layout="wide", page_title="Investment App")

with st.container(border=True):
    st.title("Welcome to your Investment App")
    st.write("This is your dashboard. Use the sidebar to navigate.")

# -----------------------------------------------------------
# Load and Process Data
# -----------------------------------------------------------

if not os.path.exists("data"):
    os.makedirs("data")

def load_data():
    path = "data/investments.csv"
    cols = ["date", "asset", "ticker", "asset_type", "price", "quantity", "fees", "currency", "goal", "notes"]
    
    try:
        df = pd.read_csv(path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=cols)
    
    # --- FIX STARTS HERE ---
    # Ensure price and quantity are numbers, then calculate total_value
    df["price"] = pd.to_numeric(df["price"], errors='coerce').fillna(0)
    df["quantity"] = pd.to_numeric(df["quantity"], errors='coerce').fillna(0)
    
    # Create the missing column that caused your error
    df["total_value"] = df["price"] * df["quantity"]
    # --- FIX ENDS HERE ---
    
    return df

df = load_data()

# -----------------------------------------------------------
# Summary metrics
# -----------------------------------------------------------

# Check if we actually have data to avoid division by zero errors
if not df.empty and "total_value" in df.columns:
    total_balance = df["total_value"].sum()
    
    # Profit Calculation Logic
    # (Using 'price' as current price and assuming a 'buy_price' exists in CSV)
    if "buy_price" in df.columns:
        df["buy_price"] = pd.to_numeric(df["buy_price"], errors='coerce').fillna(0)
        initial_investment = (df["buy_price"] * df["quantity"]).sum()
        profit = total_balance - initial_investment
        profit_margin = (profit / initial_investment * 100) if initial_investment != 0 else 0
    else:
        profit_margin = 0
else:
    total_balance = 0.0
    profit_margin = 0.0

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.metric("Profit Margin", f"{profit_margin:.2f}%")

with col2:
    with st.container(border=True):
        st.metric("Total Balance", f"${total_balance:,.2f}")

# -----------------------------------------------------------
# Pie chart: Portfolio allocation
# -----------------------------------------------------------

if not df.empty:
    with st.container(border=True):
        st.subheader("Portfolio Allocation")

        grouped = df.groupby("asset")["total_value"].sum().reset_index()

        pie_chart = (
            alt.Chart(grouped)
            .mark_arc(innerRadius=50) # Turned it into a donut chart for style
            .encode(
                theta="total_value:Q",
                color="asset:N",
                tooltip=["asset", "total_value"]
            )
        )

        st.altair_chart(pie_chart, use_container_width=True)
else:
    st.info("No data found. Add some investments to the Portfolio to see the charts!")
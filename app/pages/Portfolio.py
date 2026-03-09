import streamlit as st
import pandas as pd
from datetime import date
import altair as alt

st.title("Portfolio")

## ---------------------------------------------------------------- ##
##               Load the investments data                          ##
## ---------------------------------------------------------------- ##

# Load or create data
try:
    df = pd.read_csv("data/investments.csv")
except FileNotFoundError:
    df = pd.DataFrame(columns=[
        "date", "asset", "ticker", "asset_type",
        "price", "quantity", "fees", "currency",
        "goal", "notes"
    ])

## ---------------------------------------------------------------- ##
##               enter new data to the investments                  ##
## ---------------------------------------------------------------- ##

# Input form
with st.form("entry_form"):
    entry_date = st.date_input("Purchase date", date.today())
    asset = st.text_input("Asset")  # User can enter any asset name
    ticker = st.text_input("Ticker (optional)")
    asset_type = st.selectbox("Asset Type", ["Stock", "Crypto", "ETF", "Bond", "Commodity", "Real Estate", "Other"])
    broker = st.text_input("Broker / Exchange (optional)")

    price = st.number_input("Price per unit", min_value=0.0)
    quantity = st.number_input("Quantity", min_value=0.0)
    fees = st.number_input("Fees / Commission", min_value=0.0)
    currency = st.selectbox("Currency", ["EUR", "USD", "GBP", "JPY", "Other"])
    
    goal = st.selectbox("Investment Goal", ["Long-term", "Short-term", "Dividend", "Speculation", "Hedge"])
    notes = st.text_area("Notes")

    submitted = st.form_submit_button("Add Entry")
    

if submitted:
    new_row = {
        "date": entry_date,
        "asset": asset,
        "ticker": ticker,
        "asset_type": asset_type,
        "price": price,
        "quantity": quantity,
        "fees": fees,
        "currency": currency,
        "goal": goal,
        "notes": notes
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv("data/investments.csv", index=False)
    st.success("Entry added!")


## ---------------------------------------------------------------- ##
##               delete data from the investments                   ##
## ---------------------------------------------------------------- ##

st.subheader("Remove an Entry")

if not df.empty:
    # Create a unique label for each row
    df["label"] = df.apply(
        lambda row: f"{row['date']} - {row['asset']} ({row['quantity']} @ {row['price']})",
        axis=1
    )

    # Dropdown to select which entry to delete
    to_delete = st.selectbox("Select a purchase to remove", df["label"])

    if st.button("Delete Entry"):
        df = df[df["label"] != to_delete]  # remove selected row
        df = df.drop(columns=["label"])    # clean up helper column
        df.to_csv("data/investments.csv", index=False)
        st.success("Entry removed!")
else:
    st.info("No entries to remove.")

## ---------------------------------------------------------------- ##
##               Table for the portfolio assets                     ##
## ---------------------------------------------------------------- ##

# Display table
st.subheader("Your Purchases")
st.dataframe(df)

## ---------------------------------------------------------------- ##
##               Pie chart for the portfolio assets                 ##
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
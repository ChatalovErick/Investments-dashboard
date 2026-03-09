import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import date
import altair as alt

st.set_page_config(layout="wide")

## ---------------------------------------------------------------- ##
##               Load the investments data                          ##
## ---------------------------------------------------------------- ##

if not os.path.exists("data"):
    os.makedirs("data")

def load_data():
    try:
        return pd.read_csv("data/investments.csv")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=[
            "date", "asset", "ticker", "asset_type",
            "price", "quantity", "fees", "currency",
            "goal", "notes"
        ])

df = load_data()

## ---------------------------------------------------------------- ##
##               Portfolio page content and layout                  ##
## ---------------------------------------------------------------- ##
with st.container(border=True): 
    st.markdown("<h1 style='text-align: center'>Portfolio</h1>", unsafe_allow_html=True)

# --- State Management ---
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "show_delete_form" not in st.session_state:
    st.session_state.show_delete_form = False

def toggle_add():
    st.session_state.show_add_form = not st.session_state.show_add_form
    st.session_state.show_delete_form = False # Close delete if add is opened

def toggle_delete():
    st.session_state.show_delete_form = not st.session_state.show_delete_form
    st.session_state.show_add_form = False # Close add if delete is opened

## ---------------------------------------------------------------- ##
##               Action Buttons for adding and                      ##
##              removing data to the investments                    ##
## ---------------------------------------------------------------- ##

# --- Action Buttons ---
with st.container(border=True):
    btn_col1, btn_col2, btn_spacer = st.columns([1, 1, 4])
    
    with btn_col1:
        st.button("Add asset", use_container_width=True, on_click=toggle_add)

    with btn_col2:
        st.button("Remove asset", use_container_width=True, on_click=toggle_delete)

## ---------------------------------------------------------------- ##
##               enter new data to the investments                  ##
## ---------------------------------------------------------------- ##

if st.session_state.show_add_form:
    with st.expander("Enter New Investment Data", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            entry_date = st.date_input("Purchase date", date.today())
            asset = st.text_input("Asset")
            ticker = st.text_input("Ticker (optional)")
            asset_type = st.selectbox("Asset Type", ["Stock", "Crypto", "ETF", "Bond", "Commodity", "Real Estate", "Other"])
            price = st.number_input("Price per unit", min_value=0.0)
            quantity = st.number_input("Quantity", min_value=0.0)
            fees = st.number_input("Fees / Commission", min_value=0.0)
            currency = st.selectbox("Currency", ["EUR", "USD", "GBP", "JPY", "Other"])
            goal = st.selectbox("Investment Goal", ["Long-term", "Short-term", "Dividend", "Speculation", "Hedge"])
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("Add Entry")

        if submitted:
            new_row = {"date": entry_date, "asset": asset, "ticker": ticker, "asset_type": asset_type, 
                       "price": price, "quantity": quantity, "fees": fees, "currency": currency, 
                       "goal": goal, "notes": notes}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv("data/investments.csv", index=False)
            st.success("Entry added!")
            st.session_state.show_add_form = False
            st.rerun()

# --- 2. DELETE DATA SECTION ---
if st.session_state.show_delete_form:
    with st.expander("Remove an Entry", expanded=True):
        if not df.empty:
            # Create a unique label for each row for the dropdown
            df["label"] = df.apply(
                lambda row: f"{row['date']} - {row['asset']} ({row['quantity']} @ {row['price']})",
                axis=1
            )

            to_delete = st.selectbox("Select a purchase to remove", df["label"])

            if st.button("Confirm Delete", type="primary"):
                # Filter out the selected row and drop the helper column
                df = df[df["label"] != to_delete]
                df = df.drop(columns=["label"])
                df.to_csv("data/investments.csv", index=False)
                
                st.success("Entry removed!")
                st.session_state.show_delete_form = False
                st.rerun()
        else:
            st.info("No entries to remove.")
            

## ---------------------------------------------------------------- ##
##               Filters for the portfolio assets                   ##
## ---------------------------------------------------------------- ##

with st.container(border=True):
    # Row 2: Global Filter
    # Get unique asset types and add "All" to the top
    asset_types = ["All"] + sorted(df["asset_type"].unique().tolist())
    
    filter_val = st.selectbox("Filter for the graphs and table", asset_types)

    # Logic to filter the dataframe
    if filter_val == "All":
        filtered_df = df.copy()
    else:
        filtered_df = df[df["asset_type"] == filter_val].copy()

## ---------------------------------------------------------------- ##
##               Charts for the portfolio assets                    ##
## ---------------------------------------------------------------- ##

with st.container(border=True):
    # Row 3: Two Graphs Side-by-Side
    graph_col1, graph_col2 = st.columns(2)

    ## --- Pie chart (Using filtered_df) ---
    with graph_col1:
        with st.container(border=True):
            st.subheader(f"Allocation: {filter_val}")

            if not filtered_df.empty:
                # Compute total value per asset on the filtered data
                filtered_df["total_value"] = filtered_df["price"] * filtered_df["quantity"]

                # Group by asset
                grouped = filtered_df.groupby("asset")["total_value"].sum().reset_index()

                # Create pie chart
                chart = alt.Chart(grouped).mark_arc().encode(
                    theta="total_value",
                    color="asset",
                    tooltip=["asset", "total_value"]
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No data available for this filter.")
    
    with graph_col2:
        with st.container(border=True):
            st.subheader("Asset Value Comparison")
            if not filtered_df.empty:
                # Example Bar Chart using filtered data
                bar_chart = alt.Chart(grouped).mark_bar().encode(
                    x=alt.X("asset", sort='-y'),
                    y="total_value",
                    color="asset"
                )
                st.altair_chart(bar_chart, use_container_width=True)
            else:
                st.info("No data to display.")


## ---------------------------------------------------------------- ##
##               Table for the portfolio assets                    ##
## ---------------------------------------------------------------- ##

with st.container(border=True):
    with st.container(border=True):
        st.subheader(f"Records for {filter_val}")
        # Display the filtered dataframe
        # We drop the helper columns like 'total_value' or 'label' if they exist for a cleaner look
        display_df = filtered_df.drop(columns=["total_value", "label"], errors="ignore")
        st.dataframe(display_df, use_container_width=True)

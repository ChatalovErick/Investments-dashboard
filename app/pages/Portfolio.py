import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import date
import plotly.express as px
from streamlit_plotly_events import plotly_events

# 1. Page Configuration
st.set_page_config(page_title="Investment Drill-Down", layout="wide")
st.title("Interactive Portfolio Dashboard 📊")

## ---------------------------------------------------------------- ##
##                Load the investments data                         ##
## ---------------------------------------------------------------- ##

if not os.path.exists("data"):
    os.makedirs("data")

def load_data():
    try:
        data = pd.read_csv("data/investments.csv")
        data['price'] = pd.to_numeric(data['price'], errors='coerce').fillna(0)
        data['quantity'] = pd.to_numeric(data['quantity'], errors='coerce').fillna(0)
        data['total_value'] = data['price'] * data['quantity']
        return data
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=[
            "date", "asset", "ticker", "asset_type",
            "price", "quantity", "fees", "currency",
            "goal", "notes", "total_value"
        ])

df = load_data()

if df.empty:
    st.warning("The dataset is empty. Please add some investments to see the charts.")
    st.stop()

## ---------------------------------------------------------------- ##
##                Investment Drill-Down Logic                       ##
## ---------------------------------------------------------------- ##

with st.container(border=True):

    st.subheader(f"Asset's Portfolio Overview")

    # Initialize Shared Drill-Down State
    if 'current_selection' not in st.session_state:
        st.session_state.current_selection = None

    graph_col1, graph_col2 = st.columns(2)

    # --- COLUMN 1: BAR CHART ---
    with graph_col1:
        with st.container(border=True):
            if st.session_state.current_selection is None:
                st.subheader("Allocation by Type (Bar)")
                df_type = df.groupby('asset_type')['total_value'].sum().reset_index()

                fig1 = px.bar(
                    df_type, x='asset_type', y='total_value', 
                    color='asset_type', text_auto='.2s',
                    labels={'asset_type': 'Category', 'total_value': 'Value ($)'},
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                
                selected_bar = plotly_events(fig1, click_event=True, key="bar_chart")
                if selected_bar:
                    st.session_state.current_selection = selected_bar[0]['x']
                    st.rerun()
            else:
                sel_type = st.session_state.current_selection
                st.markdown(f"📂 **Bar Detail**: {sel_type}")
                
                df_filtered = df[df['asset_type'] == sel_type].groupby('asset')['total_value'].sum().reset_index()
                fig2 = px.bar(df_filtered, x='asset', y='total_value', color='asset', text_auto='.2s')
                st.plotly_chart(fig2, use_container_width=True)

    # --- COLUMN 2: PIE CHART ---
    with graph_col2:
        with st.container(border=True):
            if st.session_state.current_selection is None:
                st.subheader("Allocation by Type (Pie)")
                df_type_pie = df.groupby('asset_type')['total_value'].sum().reset_index()

                fig_pie = px.pie(
                    df_type_pie, values='total_value', names='asset_type',
                    hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie.update_traces(textinfo='percent+label')

                selected_pie = plotly_events(fig_pie, click_event=True, key="pie_chart")
                if selected_pie:
                    idx = selected_pie[0]['pointNumber']
                    st.session_state.current_selection = df_type_pie.iloc[idx]['asset_type']
                    st.rerun()
            else:
                sel_type = st.session_state.current_selection
                st.markdown(f"📂 **Pie Detail**: {sel_type}")

                df_filtered_p = df[df['asset_type'] == sel_type].groupby('asset')['total_value'].sum().reset_index()
                fig_pie2 = px.pie(df_filtered_p, values='total_value', names='asset', hole=0.4)
                fig_pie2.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie2, use_container_width=True)

    # --- NEW: SINGLE RESET BUTTON ---
    # This button appears only when a selection is made
    if st.session_state.current_selection is not None:
        if st.button("⬅️ Back to All Asset Types (Reset All Graphs)", use_container_width=True):
            st.session_state.current_selection = None
            st.rerun()
        st.divider() # Visual separation

## ---------------------------------------------------------------- ##
##               Action Buttons for adding and                      ##
##              removing data to the investments                    ##
## ---------------------------------------------------------------- ##

with st.container(border=True):

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

    # --- Action Buttons ---
    with st.container(border=True):

        st.subheader(f"Asset Management")

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

    ## ---------------------------------------------------------------- ##
    ##               delete data from the investments dataset           ##
    ## ---------------------------------------------------------------- ##

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
    st.subheader(f"Filter & View Controls")
    asset_types = ["All"] + sorted(df["asset_type"].unique().tolist())
    filter_val = st.selectbox("Filter for the graphs and table", asset_types)

    if filter_val == "All":
        filtered_df = df.copy()
    else:
        filtered_df = df[df["asset_type"] == filter_val].copy()

## ---------------------------------------------------------------- ##
##               Full Portfolio assets barplot chart                ##
## ---------------------------------------------------------------- ##

with st.container(border=True):
    col, = st.columns(1)

    with col:
        with st.container(border=True):
            st.subheader("Allocation by Individual Asset")
            
            # CHANGE: Use filtered_df here instead of df
            df_assets = filtered_df.groupby('asset')['total_value'].sum().reset_index()
            
            # Sort by value
            df_assets = df_assets.sort_values(by='total_value', ascending=False)

            fig_assets = px.bar(
                df_assets, 
                x='asset', 
                y='total_value', 
                color='asset', 
                text_auto='.2s',
                labels={'asset': 'Asset Name', 'total_value': 'Total Value ($)'},
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            
            fig_assets.update_layout(showlegend=False)

            # Display the chart
            st.plotly_chart(fig_assets, use_container_width=True)

## ---------------------------------------------------------------- ##
##               Table for the portfolio assets                     ##
## ---------------------------------------------------------------- ##

with st.container(border=True):
    with st.container(border=True):
        st.subheader(f"Holdings Details: {filter_val}")
        # Display the filtered dataframe
        # We drop the helper columns like 'total_value' or 'label' if they exist for a cleaner look
        display_df = filtered_df.drop(columns=["total_value", "label"], errors="ignore")
        st.dataframe(display_df, use_container_width=True)
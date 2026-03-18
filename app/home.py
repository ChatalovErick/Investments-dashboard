import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from backend.asset_fetcher import get_current_price

st.set_page_config(layout="wide")

# ---------------------------------------------------------------- #
# Load investments data
# ---------------------------------------------------------------- #

if not os.path.exists("data"):
    os.makedirs("data")

def load_data():
    try:
        data = pd.read_csv("data/investments.csv")

        # Convert types safely
        data['price'] = pd.to_numeric(data['price'], errors='coerce').fillna(0)
        data['quantity'] = pd.to_numeric(data['quantity'], errors='coerce').fillna(0)
        data['date'] = pd.to_datetime(data['date'], errors='coerce')

        # Total value at purchase
        data['total_value'] = pd.to_numeric(data.get('total_value'), errors='coerce')
        data['total_value'] = data['total_value'].fillna(data['price'] * data['quantity'])

        data = data.sort_values('date')

        # Fetch current prices
        data["current_price"] = data.apply(
            lambda row: get_current_price(row["asset_type"], row["ticker"]),
            axis=1
        )

        # Current total value
        data['current_total_value'] = pd.to_numeric(
            data['current_price'] * data['quantity'], errors='coerce'
        ).fillna(0)

        # Current portfolio balance (cumulative)
        data['current_portfolio_balance'] = data['current_total_value'].cumsum()
        data['current_portfolio_balance'] = pd.to_numeric(
            data['current_portfolio_balance'], errors='coerce'
        ).fillna(0)

        # Invested portfolio balance (cost basis)
        data['invested_portfolio_balance'] = data['total_value'].cumsum()
        data['invested_portfolio_balance'] = pd.to_numeric(
            data['invested_portfolio_balance'], errors='coerce'
        ).fillna(0)

        return data

    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=[
            "date", "asset", "ticker", "asset_type",
            "price", "quantity", "fees", "currency",
            "goal", "notes", "total_value"
        ])

df = load_data()

if df.empty:
    st.warning("The dataset is empty. Please add some investments in the Portfolio page to see the charts.")
    st.stop()

# ---------------------------------------------------------------- #
# Portfolio history tracking (current + invested)
# ---------------------------------------------------------------- #

HISTORY_FILE = "data/portfolio_history.csv"

def load_history():
    if os.path.exists(HISTORY_FILE):
        hist = pd.read_csv(HISTORY_FILE, parse_dates=["date"])

        # Auto-migrate missing columns
        if "invested_portfolio_balance" not in hist.columns:
            hist["invested_portfolio_balance"] = None

        # Clean corrupted rows
        hist['current_portfolio_balance'] = pd.to_numeric(
            hist['current_portfolio_balance'], errors='coerce'
        )
        hist['invested_portfolio_balance'] = pd.to_numeric(
            hist['invested_portfolio_balance'], errors='coerce'
        )

        # Forward-fill and replace remaining NaN
        hist['current_portfolio_balance'] = hist['current_portfolio_balance'].ffill().fillna(0)
        hist['invested_portfolio_balance'] = hist['invested_portfolio_balance'].ffill().fillna(0)

        return hist

    return pd.DataFrame(columns=["date", "current_portfolio_balance", "invested_portfolio_balance"])

history = load_history()

today = pd.Timestamp.today().normalize()

today_current = float(df['current_portfolio_balance'].iloc[-1])
today_invested = float(df['invested_portfolio_balance'].iloc[-1])

# Append today's snapshot only (H1)
if not (history['date'] == today).any():
    new_row = pd.DataFrame({
        "date": [today],
        "current_portfolio_balance": [today_current],
        "invested_portfolio_balance": [today_invested]
    })
    history = pd.concat([history, new_row], ignore_index=True)
    history.to_csv(HISTORY_FILE, index=False)

# ---------------------------------------------------------------- #
# Timeframes (Line Chart Invested and Net Worth)
# ---------------------------------------------------------------- #
with st.container(border=True):

    df_history = history.sort_values("date")

    df_daily = df_history.set_index('date').resample('D').last().ffill().reset_index()
    df_weekly = df_history.set_index('date').resample('W').last().ffill().reset_index()
    df_monthly = df_history.set_index('date').resample('ME').last().ffill().reset_index()

    # ---------------------------------------------------------------- #
    # Profit margin calculations
    # ---------------------------------------------------------------- #

    def pct_change(series):
        if len(series) < 2:
            return 0
        prev = series.iloc[-2]
        curr = series.iloc[-1]
        if prev == 0:
            return 0
        return ((curr - prev) / prev) * 100

    # Current values
    daily_current = float(df_daily['current_portfolio_balance'].iloc[-1])
    weekly_current = float(df_weekly['current_portfolio_balance'].iloc[-1])
    monthly_current = float(df_monthly['current_portfolio_balance'].iloc[-1])

    # Invested values
    daily_invested = float(df_daily['invested_portfolio_balance'].iloc[-1])
    weekly_invested = float(df_weekly['invested_portfolio_balance'].iloc[-1])
    monthly_invested = float(df_monthly['invested_portfolio_balance'].iloc[-1])

    # Changes
    daily_change = pct_change(df_daily['current_portfolio_balance'])
    weekly_change = pct_change(df_weekly['current_portfolio_balance'])
    monthly_change = pct_change(df_monthly['current_portfolio_balance'])

    # ---------------------------------------------------------------- #
    # Layout
    # ---------------------------------------------------------------- #

    col1, col2 = st.columns([1, 1])

    with col1:
        st.title("Portfolio Overview")

    with col2:
        with st.container(border=True):

            selected_tf = st.radio(
                "Performance timeframe",
                ["Daily", "Weekly", "Monthly"],
                horizontal=True
            )

            if selected_tf == "Daily":
                metric_current = daily_current
                metric_invested = daily_invested
                metric_change = daily_change
                df_selected = df_daily
            elif selected_tf == "Weekly":
                metric_current = weekly_current
                metric_invested = weekly_invested
                metric_change = weekly_change
                df_selected = df_weekly
            else:
                metric_current = monthly_current
                metric_invested = monthly_invested
                metric_change = monthly_change
                df_selected = df_monthly

            # Calculate Total Profit (Current Value - Cost Basis)
            total_profit_amt = metric_current - metric_invested
            
            # Calculate ROI % (Profit / Cost Basis)
            roi_pct = (total_profit_amt / metric_invested * 100) if metric_invested != 0 else 0

            st.divider() # Optional: adds a thin line between selector and metrics

            # 2. Horizontal Metrics layout
            m_col1, m_col2, m_col3 = st.columns(3)

            with m_col1:
                st.metric(
                    label=f"Current Value",
                    value=f"${metric_current:,.2f}",
                    delta=f"{metric_change:+.2f}%"
                )

            with m_col2:
                st.metric(
                    label=f"Total Contributed",
                    value=f"${metric_invested:,.2f}"
                )

            with m_col3:
                # The 'delta' parameter handles the green/red coloring automatically.
                # If total_profit_amt is negative, it shows red. If positive, green.
                st.metric(
                    label="Total Profit",
                    value=f"${total_profit_amt:,.2f}",
                    delta=f"{roi_pct:+.2f}% ROI"
                )

    # ---------------------------------------------------------------- #
    # Combined chart (Invested vs Current)
    # ---------------------------------------------------------------- #
    with st.container(border=True):
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_selected['date'],
            y=df_selected['current_portfolio_balance'],
            mode='lines+markers',
            name="Current Portfolio Value",
            line=dict(color="#007BFF", width=2),
            hovertemplate="$%{y:,.2f}<extra></extra>"
        ))

        fig.add_trace(go.Scatter(
            x=df_selected['date'],
            y=df_selected['invested_portfolio_balance'],
            mode='lines+markers',
            name="Total Capital Contributed",
            line=dict(color="#00A676", width=2, dash="dot"),
            hovertemplate="$%{y:,.2f}<extra></extra>"
        ))

        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(t=40, l=40, r=40, b=40),
            hovermode="x unified",
            font=dict(family="Inter, sans-serif", color="#1F2937"),
            xaxis=dict(
                showgrid=False,
                linecolor='#E5E7EB',
                type="date",
                rangeslider=dict(visible=False)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#F0F0F0",
                tickprefix="$",
                tickformat=",.2f",
                tickfont=dict(color="#6B7280")
            )
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ---------------------------------------------------------------- #
# Pie chart: Portfolio allocation
# ---------------------------------------------------------------- #

if not df.empty:
    with st.container(border=True):
        st.title("Portfolio Allocation")

        grouped = df.groupby("asset")["total_value"].sum().reset_index()
        grouped = grouped.sort_values("total_value", ascending=False)

        top_n = 9
        if len(grouped) > top_n:
            top_df = grouped.head(top_n).copy()
            others_value = grouped.iloc[top_n:]["total_value"].sum()
            others_df = pd.DataFrame({"asset": ["OTHERS"], "total_value": [others_value]})
            chart_data = pd.concat([top_df, others_df], ignore_index=True)
        else:
            chart_data = grouped

        fig_pie = go.Figure(data=[go.Pie(
            labels=chart_data["asset"],
            values=chart_data["total_value"],
            hole=0.5,
            marker=dict(
                colors=['#00A676', '#007BFF', '#8A2BE2', '#FF8C00', '#FFD700',
                        '#FF1493', '#00CED1', '#7FFF00', '#FF4500', '#BDC3C7'],
                line=dict(color='#FFFFFF', width=2)
            ),
            textinfo='percent+label',
            hoverinfo='label+value+percent',
            textposition='outside',
            insidetextorientation='radial'
        )])

        fig_pie.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.1
            ),
            margin=dict(t=30, b=30, l=10, r=10),
            font=dict(family="Inter, sans-serif", color="#1F2937")
        )

        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("No data found.")

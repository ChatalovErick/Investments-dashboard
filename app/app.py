import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(layout="wide")

## ---------------------------------------------------------------- ##
##                Load the investments data                         ##
## ---------------------------------------------------------------- ##

if not os.path.exists("data"):
    os.makedirs("data")

def load_data():
    try:
        data = pd.read_csv("data/investments.csv")
        data['price'] = pd.to_numeric(data['price'], errors='coerce').fillna(0)
        data['date'] = pd.to_datetime(data['date'])

        data['quantity'] = pd.to_numeric(data['quantity'], errors='coerce').fillna(0)
        data['total_value'] = data['total_value'].fillna(data['price'] * data['quantity'])
        data = data.sort_values('date')
        data['portfolio_balance'] = data['total_value'].cumsum()

        return data
    
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=[
            "date", "asset", "ticker", "asset_type",
            "price", "quantity", "fees", "currency",
            "goal", "notes", "total_value"
        ])

df = load_data()

if df.empty:
    st.warning("The dataset is empty. Please add some investments in the Porfolio page to see the charts.")
    st.stop()

## ---------------------------------------------------------------- ##
##         Time line chart for the Portfolio Balance                ##
## ---------------------------------------------------------------- ##


with st.container(border=True):

    # Pre-calculate timeframes
    df_daily = df.set_index('date').resample('D').last().ffill().reset_index()
    df_weekly = df.set_index('date').resample('W').last().ffill().reset_index()
    df_monthly = df.set_index('date').resample('ME').last().ffill().reset_index()

    # 3. Create Figure
    fig = go.Figure()

    # Adjusted Colors for Light Background
    # Using slightly deeper saturations so they pop against white
    colors = {
        'daily': '#00A676',    # Emerald Green
        'weekly': '#007BFF',   # Royal Blue
        'monthly': '#8A2BE2'   # Blue Violet
    }

    # Add Area Traces
    fig.add_trace(go.Scatter(
        x=df_daily['date'], y=df_daily['portfolio_balance'],
        name="Daily", mode='lines', visible=True,
        line=dict(color=colors['daily'], width=2),
        fill='tozeroy', fillcolor='rgba(0, 166, 118, 0.1)' # Faint green tint
    ))

    fig.add_trace(go.Scatter(
        x=df_weekly['date'], y=df_weekly['portfolio_balance'],
        name="Weekly", mode='lines+markers', visible=False,
        line=dict(color=colors['weekly'], width=2),
        fill='tozeroy', fillcolor='rgba(0, 123, 255, 0.1)' # Faint blue tint
    ))

    fig.add_trace(go.Scatter(
        x=df_monthly['date'], y=df_monthly['portfolio_balance'],
        name="Monthly", mode='lines+markers', visible=False,
        line=dict(color=colors['monthly'], width=2),
        fill='tozeroy', fillcolor='rgba(138, 43, 226, 0.1)' # Faint purple tint
    ))

    # 4. Modern Light UI Styling
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF", 
        plot_bgcolor="#FFFFFF",
        margin=dict(t=100, l=40, r=40, b=40),
        hovermode="x unified",
        font=dict(family="Inter, sans-serif", color="#1F2937"), # Dark gray text for readability
        
        # Interval Selection Buttons
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.01, y=1.12,
                xanchor='left',
                bgcolor="#F3F4F6",     # Light gray button background
                font=dict(color="#374151", size=12),
                active=0,
                buttons=list([
                    dict(label="DAILY", method="update", args=[{"visible": [True, False, False]}]),
                    dict(label="WEEKLY", method="update", args=[{"visible": [False, True, False]}]),
                    dict(label="MONTHLY", method="update", args=[{"visible": [False, False, True]}]),
                ]),
            )
        ],
        
        # Range Selector
        xaxis=dict(
            showgrid=False,
            linecolor='#E5E7EB', # Light border
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(step="all", label="ALL")
                ]),
                bgcolor="#F3F4F6",
                activecolor="#DBEAFE", # Soft blue for active state
                font=dict(size=11, color="#374151")
            ),
            type="date"
        ),
        
        yaxis=dict(
            showgrid=True,
            gridcolor="#F0F0F0", # Very subtle grid lines
            position=1,
            side="right",
            tickprefix="$",
            tickformat=",",
            tickfont=dict(color="#6B7280") # Muted gray for axis labels
        )
    )

    # Custom Metric Header
    last_val = df['portfolio_balance'].iloc[-1]
    prev_val = df['portfolio_balance'].iloc[-2]
    change = ((last_val - prev_val) / prev_val) * 100

    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Portfolio Intelligence")
    with col2:
        st.metric("Net Worth", f"${last_val:,.0f}", f"{change:+.2f}% (Last Trade)")

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# -----------------------------------------------------------
# Pie chart: Portfolio allocation (Top 10 via Plotly)
# -----------------------------------------------------------

if not df.empty:
    with st.container(border=True):
        st.subheader("Portfolio Allocation")

        # 1. Group and Sort
        grouped = df.groupby("asset")["total_value"].sum().reset_index()
        grouped = grouped.sort_values("total_value", ascending=False)

        # 2. Logic for "Others"
        top_n = 9
        if len(grouped) > top_n:
            top_df = grouped.head(top_n).copy()
            others_value = grouped.iloc[top_n:]["total_value"].sum()
            others_df = pd.DataFrame({"asset": ["OTHERS"], "total_value": [others_value]})
            chart_data = pd.concat([top_df, others_df], ignore_index=True)
        else:
            chart_data = grouped

        # 3. Create Plotly Figure
        fig_pie = go.Figure(data=[go.Pie(
            labels=chart_data["asset"],
            values=chart_data["total_value"],
            hole=0.5, # Makes it a donut
            marker=dict(
                colors=['#00A676', '#007BFF', '#8A2BE2', '#FF8C00', '#FFD700', '#FF1493', '#00CED1', '#7FFF00', '#FF4500', '#BDC3C7'],
                line=dict(color='#FFFFFF', width=2) # Clean white borders
            ),
            textinfo='percent+label',
            hoverinfo='label+value+percent',
            textposition='outside',
            insidetextorientation='radial'
        )])

        # 4. Light Mode Layout
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



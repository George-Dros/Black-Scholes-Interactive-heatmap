import streamlit as st
import functions as f
import pandas as pd

st.set_page_config(layout="wide")

#Set up Streamlit app
st.title('Black Scholes Option Pricing')

#Major program mode selection
program_mode = st.sidebar.radio(
    'Select Program Mode:',
    ('Black-Scholes Pricer', 'Historical Ticker Data Pricer')
)

if program_mode == "Black-Scholes Pricer":
    # Add sidebar inputs
    st.sidebar.header('Black-Scholes Variables')

    # User Inputs
    current_price = st.sidebar.number_input('Current Price($)', value=100.00, format="%.2f")
    strike_price = st.sidebar.number_input('Strike Price($)', value=80.00, format="%.2f")
    volatility = st.sidebar.number_input('Volatility (σ)', value=0.20, format="%.2f")
    time_to_maturity = st.sidebar.number_input('Time to Maturity (in Years, days/365)', value=1.00, format="%.2f")
    risk_free_rate = st.sidebar.number_input('Risk-Free Rate', min_value=0.0, max_value=1.0, value=0.03, format="%.4f")
    dividend_yield = st.sidebar.number_input('Dividend Yield', min_value=0.0, max_value=1.0, value=0.0, format="%.4f")

    # Mode selection
    mode = st.sidebar.radio(
        'Select Mode:',
        ('Pricing', 'P&L')
    )

    # Conditionally display "Purchase Price" input or explanation text
    if mode == 'P&L':
        purchase_price = st.sidebar.number_input('Purchase Price', value=5.00, format="%.2f")
    else:
        purchase_price = 0
        st.sidebar.markdown("<i>Note: Switch to 'P&L' mode to set Purchase Price.</i>", unsafe_allow_html=True)

    # Separator for Heatmap Inputs
    st.sidebar.markdown("---")
    st.sidebar.subheader("Heatmap Inputs")

    # Set a default range within the dynamic range
    vol_min = 0.20
    vol_max = 0.50

    # Create the slider for strike price range percentages dynamically
    volatility_range_percentage = st.sidebar.slider(
        'Volatility Range',
        min_value=0.01,  # Minimum percentage allowed
        max_value=1.0,  # Maximum percentage allowed
        value=(vol_min, vol_max)  # Default range
    )

    vol_min_selected, vol_max_selected = volatility_range_percentage

    spot_min = st.sidebar.number_input('Min Spot Price($)', value=70.00, format="%.2f")
    spot_max = st.sidebar.number_input('Max Spot Price($)', value=120.00, format="%.2f")

    # Display Black Scholes Variables in a wide format using Streamlit columns
    colA, colB, colC, colD, colE, colF = st.columns([1, 1, 1, 1, 1, 1])

    with colA:
        st.markdown(f"**Current Price:** ${current_price:.2f}")
    with colB:
        st.markdown(f"**Strike Price:** ${strike_price:.2f}")
    with colC:
        st.markdown(f"**Volatility:** {volatility:.3f}")
    with colD:
        st.markdown(f"**Time to Maturity (Years):** {time_to_maturity:.2f}")
    with colE:
        st.markdown(f"**Risk-Free Rate:** {risk_free_rate:.4f}")
    with colF:
        st.markdown(f"**Dividend Yield:** {dividend_yield:.4f}")

    # Call and Put prices for given inputs
    call_price = f.Call_BS_Value(current_price, strike_price, risk_free_rate, time_to_maturity, volatility,
                                 q=dividend_yield)
    put_price = f.Put_BS_Value(current_price, strike_price, risk_free_rate, time_to_maturity, volatility,
                               q=dividend_yield)

    # Create two columns to display Call and Put prices
    col1, col2 = st.columns(2)

    # Display Call Price in the first column
    with col1:
        st.markdown("""
            <div style='display: flex; justify-content: center; align-items: center; padding: 10px; background-color: #e0f7fa; border-radius: 10px; font-size: 18px;'>
                <h3 style='color: #00796b; margin: 0;'>Call Price: ${:.2f}</h3>
            </div>
        """.format(call_price), unsafe_allow_html=True)

    # Display Put Price in the second column
    with col2:
        st.markdown("""
            <div style='display: flex; justify-content: center; align-items: center; padding: 10px; background-color: #ffe0b2; border-radius: 10px; font-size: 18px;'>
                <h3 style='color: #e65100; margin: 0;'>Put Price: ${:.2f}</h3>
            </div>
        """.format(put_price), unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

    call_df, put_df, call_pnl_df, put_pnl_df = f.calculate_option_values(spot_min, spot_max, vol_min_selected,
                                                                         vol_max_selected, strike_price, risk_free_rate,
                                                                         time_to_maturity,
                                                                         dividend_yield=dividend_yield,
                                                                         purchase_price=purchase_price)
    heatmap = f.plot_heatmaps(mode=mode, call_df=call_df, put_df=put_df, call_pnl_df=call_pnl_df, put_pnl_df=put_pnl_df)

elif program_mode == 'Historical Ticker Data Pricer':
    # Sidebar Inputs for Historical Ticker Data Pricer
    st.sidebar.header('Historical Ticker Data Variables')

    # User Inputs
    ticker_symbol = st.sidebar.text_input('Ticker Symbol', value='SPY')
    risk_free_rate = st.sidebar.number_input('Risk-Free Rate', min_value=0.0, max_value=1.0, value=0.03, format="%.4f")
    dividend_yield = st.sidebar.number_input('Dividend Yield', min_value=0.0, max_value=1.0, value=0.0, format="%.4f")


    #Get the Calls and Puts
    calls_all, puts_all, spot_price = f.get_option_chains_spot(ticker_symbol=ticker_symbol)

    calls_all["expiration"] = pd.to_datetime(calls_all["expiration"])

    call_unique_years = calls_all["expiration"].dt.year.unique()
    call_unique_months = calls_all["expiration"].dt.month.unique()
    call_unique_days = calls_all["expiration"].dt.day.unique()

    puts_all["expiration"] = pd.to_datetime(puts_all["expiration"])

    put_unique_years = puts_all["expiration"].dt.year.unique()
    put_unique_months = puts_all["expiration"].dt.month.unique()
    put_unique_days = puts_all["expiration"].dt.day.unique()


    # Date selection inputs
    st.sidebar.subheader('Option Maturity Date')
    year = st.sidebar.selectbox('Year', options=call_unique_years)  # Example years, replace with dynamic data
    month = st.sidebar.selectbox('Month', options=call_unique_months)
    day = st.sidebar.selectbox('Day', options=call_unique_days)

    # Call and Put prices for given inputs
    call_price = f.Call_BS_Value(spot_price, strike_price, risk_free_rate, time_to_maturity, volatility,
                                 q=dividend_yield)
    put_price = f.Put_BS_Value(spot_price, strike_price, risk_free_rate, time_to_maturity, volatility,
                               q=dividend_yield)


    # Spot price slider based on ticker data
    spot_price_slider = st.sidebar.slider(
        'Spot Price Range',
        min_value=0.1 * spot_price,
        max_value=1.0 * spot_price,
        value=(0.2 * spot_price, 0.8 * spot_price),
        format="%.2f"
    )

    # Display selected inputs
    st.markdown(f"**Ticker Symbol:** {ticker_symbol}")
    st.markdown(f"**Risk-Free Rate:** {risk_free_rate:.4f}")
    st.markdown(f"**Dividend Yield:** {dividend_yield:.4f}")
    st.markdown(f"**Selected Maturity Date:** {year}-{month:02d}-{day:02d}")
    st.markdown(f"**Spot Price Range:** ${spot_price_slider[0]:.2f} - ${spot_price_slider[1]:.2f}")

    # Placeholder for additional calculations based on ticker data
    st.markdown("### Pricing based on Historical Ticker Data will be implemented here.")




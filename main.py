import streamlit as st
import numpy as np
from scipy.interpolate import griddata
import plotly.graph_objects as go


#Set up Streamlit app
st.title('Black Scholes Option Pricing')

#Add sidebar inputs
st.sidebar.header('User Inputs')

#User Inputs
current_price = st.sidebar.number_input('Current Price', value=100.00, format="%.2f")
strike_price = st.sidebar.number_input('Strike Price', value=80.00, format="%.2f")
volatility = st.sidebar.number_input('Volatility', value=0.20, format="%.3f")
time_to_maturity = st.sidebar.number_input('Time to Maturity (in Years)', value=1.00, format="%.2f")
risk_free_rate = st.sidebar.number_input('Risk-Free Rate', min_value=0.0, max_value=1.0, value=0.03,  format="%.4f")


# Set a percentage range for the volatility slider
vol_min_range = 0.01
vol_max_range = 1.00

# Set a default range within the dynamic range
vol_min_percentage = 0.20
vol_max_percentage = 0.50

# Create the slider for strike price range percentages dynamically
volatility_range_percentage = st.sidebar.slider(
    'Volatility Range',
    min_value=vol_min_range,  # Minimum percentage allowed
    max_value=vol_max_range,  # Maximum percentage allowed
    value=(vol_min_percentage, vol_max_percentage)  # Default range
)


min_spot_price = st.sidebar.number_input('Min Spot Price', value=70.00, format="%.2f")
max_spot_price = st.sidebar.number_input('Max Spot Price', value=120.00, format="%.2f")


# Display Black Scholes Variables
st.markdown("<div style='padding: 15px; background-color: #4e5d6c; color: white; border-radius: 5px; margin-bottom: 20px;'>"
            "<h4>Variables</h4>"
            f"<table style='width: 100%;'>"
            f"<tr><td><strong>Current Price:</strong></td><td>${current_price:.2f}</td></tr>"
            f"<tr><td><strong>Strike Price:</strong></td><td>${strike_price:.2f}</td></tr>"
            f"<tr><td><strong>Volatility:</strong></td><td>{volatility:.3f}</td></tr>"
            f"<tr><td><strong>Time to Maturity (Years):</strong></td><td>{time_to_maturity:.2f}</td></tr>"
            f"<tr><td><strong>Risk-Free Rate:</strong></td><td>{risk_free_rate:.4f}</td></tr>"
            "</table>"
            "</div>", unsafe_allow_html=True)



# Call and Put Option Prices
call_price = 15.00
put_price = 10.00

# Create two columns to display Call and Put prices
col1, col2 = st.columns(2)

# Display Call Price in the first column
with col1:
    st.markdown("<div style='padding: 10px; background-color: #e0f7fa; border-radius: 5px;'>"
                f"<h3 style='color: #00796b;'>Call Price: ${call_price:.2f}</h3>"
                "</div>", unsafe_allow_html=True)

# Display Put Price in the second column
with col2:
    st.markdown("<div style='padding: 10px; background-color: #ffe0b2; border-radius: 5px;'>"
                f"<h3 style='color: #e65100;'>Put Price: ${put_price:.2f}</h3>"
                "</div>", unsafe_allow_html=True)




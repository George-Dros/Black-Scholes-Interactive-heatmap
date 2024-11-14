import yfinance as yf
from turtle import st
import numpy as np
from scipy.stats import norm
import scipy as sq
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
import streamlit as st
from datetime import datetime


def get_option_chains_spot(ticker_symbol):
    # Fetch the ticker data
    ticker = yf.Ticker(ticker_symbol)

    # Get dividends, spot price, and expiration dates
    dividends = ticker.dividends
    spot_price = ticker.history(period="1d")["Close"].iloc[0]
    expiration_dates = ticker.options  # Expiration dates

    # Fetch call and put options for each expiration date
    calls_dict = {date: ticker.option_chain(date).calls for date in expiration_dates}
    puts_dict = {date: ticker.option_chain(date).puts for date in expiration_dates}

    # Add expiration column to each DataFrame in calls_dict and puts_dict
    for date, df in calls_dict.items():
        df['expiration'] = date

    for date, df in puts_dict.items():
        df['expiration'] = date

    # Concatenate all DataFrames from calls_dict and puts_dict
    calls_all = pd.concat(calls_dict.values())
    puts_all = pd.concat(puts_dict.values())

    # For calls_all DataFrame
    calls_all = calls_all[["strike", "lastPrice", "impliedVolatility", "expiration"]]
    calls_all["time_to_expiration"] = calls_all["expiration"].apply(calculate_time_to_expiration)
    calls_all = calls_all[calls_all["time_to_expiration"] > 0.0]
    calls_all = calls_all.reset_index(drop=True)

    # For puts_all DataFrame
    puts_all = puts_all[["strike", "lastPrice", "impliedVolatility", "expiration"]]
    puts_all["time_to_expiration"] = puts_all["expiration"].apply(calculate_time_to_expiration)
    puts_all = puts_all[puts_all["time_to_expiration"] > 0.0]
    puts_all = puts_all.reset_index(drop=True)

    return calls_all, puts_all, spot_price


def Call_BS_Value(S, X, r, T, v, q):
    # Calculates the value of a call option (Black-Scholes formula for call options with dividends)
    # S is the share price at time T
    # X is the strike price
    # r is the risk-free interest rate
    # T is the time to maturity in years (days/365)
    # v is the volatility
    # q is the dividend yield
    d_1 = (np.log(S / X) + (r - q + v ** 2 * 0.5) * T) / (v * np.sqrt(T))
    d_2 = d_1 - v * np.sqrt(T)
    return S * np.exp(-q * T) * norm.cdf(d_1) - X * np.exp(-r * T) * norm.cdf(d_2)


def Call_IV_Obj_Function(S, X, r, T, v, q, Call_Price):
    # Objective function which sets market and model prices equal to zero (Function needed for Call_IV)
    # The parameters are explained in the Call_BS_Value function
    return Call_Price - Call_BS_Value(S, X, r, T, v, q)


def Call_IV(S, X, r, T, Call_Price, q, a=-2, b=2, xtol=0.000001):
    # Calculates the implied volatility for a call option with Brent's method
    # The first four parameters are explained in the Call_BS_Value function
    # Call_Price is the price of the call option
    # q is the dividend yield
    # Last three variables are needed for Brent's method
    _S, _X, _r, _t, _Call_Price, _q = S, X, r, T, Call_Price, q

    def fcn(v):
        return Call_IV_Obj_Function(_S, _X, _r, _t, v, _q, _Call_Price)

    try:
        result = sq.optimize.brentq(fcn, a=a, b=b, xtol=xtol)
        return np.nan if result <= xtol else result
    except ValueError:
        return np.nan


def Put_BS_Value(S, X, r, T, v, q):
    # Calculates the value of a put option (Black-Scholes formula for put options with dividends)
    # The parameters are explained in the Call_BS_Value function
    d_1 = (np.log(S / X) + (r - q + v ** 2 * 0.5) * T) / (v * np.sqrt(T))
    d_2 = d_1 - v * np.sqrt(T)
    return X * np.exp(-r * T) * norm.cdf(-d_2) - S * np.exp(-q * T) * norm.cdf(-d_1)


def Put_IV_Obj_Function(S, X, r, T, v, q, Put_Price):
    # Objective function which sets market and model prices equal to zero (Function needed for Put_IV)
    # The parameters are explained in the Call_BS_Value function
    return Put_Price - Put_BS_Value(S, X, r, T, v, q)


def Put_IV(S, X, r, T, Put_Price, q, a=-2, b=2, xtol=0.000001):
    # Calculates the implied volatility for a put option with Brent's method
    # The first four parameters are explained in the Call_BS_Value function
    # Put_Price is the price of the put option
    # q is the dividend yield
    # Last three variables are needed for Brent's method
    _S, _X, _r, _t, _Put_Price, _q = S, X, r, T, Put_Price, q

    def fcn(v):
        return Put_IV_Obj_Function(_S, _X, _r, _t, v, _q, _Put_Price)

    try:
        result = sq.optimize.brentq(fcn, a=a, b=b, xtol=xtol)
        return np.nan if result <= xtol else result
    except ValueError:
        return np.nan


def Calculate_IV_Call_Put(S, X, r, T, Option_Price, Put_or_Call, q):
    # This is a general function witch summarizes Call_IV and Put_IV (delivers the same results)
    # Can be used for a Lambda function within Pandas
    # The first four parameters are explained in the Call_BS_Value function
    # Put_or_Call:
    # 'C' returns the implied volatility of a call
    # 'P' returns the implied volatility of a put
    # Option_Price is the price of the option.
    # q is the dividend yield

    if Put_or_Call == 'C':
        return Call_IV(S, X, r, T, Option_Price, q)
    if Put_or_Call == 'P':
        return Put_IV(S, X, r, T, Option_Price, q)
    else:
        return 'Neither call or put'


def calculate_time_to_expiration(expiration_date_str: str) -> float:
    """
    Calculate the time to expiration in years from today.

    Parameters:
    expiration_date_str (str): Expiration date in the format 'YYYY-MM-DD'

    Returns:
    float: Time to expiration in years
    """
    # Parse the expiration date string to a datetime object
    expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")

    # Get today's date
    current_date = datetime.now()

    # Calculate the number of days to expiration
    days_to_expiration = (expiration_date - current_date).days

    # Convert days to years (use 365 for simplicity)
    T = days_to_expiration / 365.0

    return T


def calculate_option_values(min_spot, max_spot, min_vol, max_vol, strike_price, risk_free_rate, time_to_maturity, dividend_yield, purchase_price):
    spot_interval = np.round(np.linspace(min_spot, max_spot, 10), 2)
    vol_interval = np.round(np.linspace(min_vol, max_vol, 10), 2)

    call_values = np.zeros((len(vol_interval), len(spot_interval)))
    put_values = np.zeros((len(vol_interval), len(spot_interval)))

    call_pnl = np.zeros((len(vol_interval), len(spot_interval)))
    put_pnl = np.zeros((len(vol_interval), len(spot_interval)))

    for i, spot in enumerate(spot_interval):
        for j, vol in enumerate(vol_interval):
            call_values[j, i] = Call_BS_Value(spot, strike_price, risk_free_rate, time_to_maturity, vol, dividend_yield)
            put_values[j, i] = Put_BS_Value(spot, strike_price, risk_free_rate, time_to_maturity, vol, dividend_yield)

            call_pnl[j, i] = call_values[j, i] - purchase_price
            put_pnl[j, i] = put_values[j, i] - purchase_price

    call_df = pd.DataFrame(call_values, index=vol_interval, columns=spot_interval)
    put_df = pd.DataFrame(put_values, index=vol_interval, columns=spot_interval)

    call_pnl_df = pd.DataFrame(call_pnl, index=vol_interval, columns=spot_interval)
    put_pnl_df = pd.DataFrame(put_pnl, index=vol_interval, columns=spot_interval)

    call_df = call_df.round(2)
    put_df = put_df.round(2)

    call_pnl_df = call_pnl_df.round(2)
    put_pnl_df = put_pnl_df.round(2)

    return call_df, put_df, call_pnl_df, put_pnl_df


def calculate_market_prices(min_spot, max_spot, call_datapoints, put_datapoints, risk_free_rate, dividend_yield):
    spot_interval = np.round(np.linspace(min_spot, max_spot, 10), 2)

    call_vol_interval = call_datapoints["impliedVolatility"].round(2)
    put_vol_interval = put_datapoints["impliedVolatility"].round(2)

    call_values = np.zeros((len(call_vol_interval), len(spot_interval)))
    put_values = np.zeros((len(put_vol_interval), len(spot_interval)))

    for i, spot in enumerate(spot_interval):
        for row in call_datapoints.itertuples():
            call_values[row.Index, i] = Call_BS_Value(S=spot, X=row.strike, r=risk_free_rate, T=row.time_to_expiration,
                                                v=row.impliedVolatility, q=dividend_yield) - row.lastPrice

    for i, spot in enumerate(spot_interval):
        for row in put_datapoints.itertuples():
            put_values[row.Index, i] = Put_BS_Value(S=spot, X=row.strike, r=risk_free_rate, T=row.time_to_expiration,
                                                v=row.impliedVolatility, q=dividend_yield) - row.lastPrice

    call_df = pd.DataFrame(call_values, index=call_vol_interval, columns=spot_interval)
    put_df = pd.DataFrame(put_values, index=put_vol_interval, columns=spot_interval)

    return call_df, put_df


def market_heatmaps(call_df, put_df):
    fig, axs = plt.subplots(1, 2, figsize=(20, 10))

    # Plot Call Prices Heatmap
    sns.heatmap(call_df, ax=axs[0], cmap='RdBu', annot=True, cbar=True, fmt=".2f")
    axs[0].set_title('Call Option Mis-pricing (Theoretical - Market)')
    axs[0].set_xlabel('Spot Price')
    axs[0].set_ylabel('Volatility')

    # Plot Put Prices Heatmap
    sns.heatmap(put_df, ax=axs[1], cmap='RdBu', annot=True, cbar=True, fmt=".2f")
    axs[1].set_title('Put Option Mis-pricing (Theoretical - Market)')
    axs[1].set_xlabel('Spot Price')
    axs[1].set_ylabel('Volatility')

    plt.tight_layout()
    st.pyplot(fig)


def plot_heatmaps(mode, call_df, put_df, call_pnl_df, put_pnl_df):
    fig, axs = plt.subplots(1, 2, figsize=(20, 10))

    if mode == 'Pricing':
        # Plot Call and Put Prices
        sns.heatmap(call_df, ax=axs[0], cmap='viridis', annot=True, cbar=True, fmt=".2f")
        axs[0].set_title('CALL prices Heatmap')
        axs[0].set_xlabel('Spot Price')
        axs[0].set_ylabel('Volatility')

        sns.heatmap(put_df, ax=axs[1], cmap='viridis', annot=True, cbar=True, fmt=".2f")
        axs[1].set_title('PUT prices Heatmap')
        axs[1].set_xlabel('Spot Price')
        axs[1].set_ylabel('Volatility')
    elif mode == 'P&L':
        # Plot Call and Put PnLs
        sns.heatmap(call_pnl_df, ax=axs[0], cmap='RdYlGn', annot=True, cbar=True, fmt=".2f")
        axs[0].set_title('CALL P&Ls')
        axs[0].set_xlabel('Spot Price')
        axs[0].set_ylabel('Volatility')

        sns.heatmap(put_pnl_df, ax=axs[1], cmap='RdYlGn', annot=True, cbar=True, fmt=".2f")
        axs[1].set_title('PUT P&Ls')
        axs[1].set_xlabel('Spot Price')
        axs[1].set_ylabel('Volatility')

    plt.tight_layout()
    st.pyplot(fig)


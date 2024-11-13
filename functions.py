from turtle import st
import numpy as np
from scipy.stats import norm
import scipy as sq
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
import streamlit as st


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


# Function to plot either prices or PnL depending on user selection
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

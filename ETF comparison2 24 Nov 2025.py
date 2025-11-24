import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ----------- Helper Functions ------------

def validate_etf(ticker):
    try:
        info = yf.Ticker(ticker).info
        # Basic ETF detection heuristic
        if "category" in info and info.get("quoteType") == "ETF":
            return True
        if "fundFamily" in info or "category" in info:
            return True
    except Exception:
        return False
    return False

def get_etf_data(ticker):
    try:
        etf = yf.Ticker(ticker)
        hist = etf.history(period="5y")

        if hist.empty:
            raise ValueError("No historical data found.")

        daily_returns = hist["Close"].pct_change()
        volatility = np.sqrt(252) * daily_returns.std()

        cumulative = (1 + daily_returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()

        sharpe = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252))

        info = etf.info

        try:
            sector_data = etf.get_fund_sector_weightings()
            sector_str = ", ".join([f"{k}: {v}%" for k,v in sector_data.items()]) if sector_data else "N/A"
        except:
            sector_str = "N/A"

        weighting = "Market Cap Weighting"
        name = info.get("longName", "")
        if "Equal Weight" in name or "Equal-Weight" in name:
            weighting = "Equal Weighting"

        data = {
            "Ticker": ticker.upper(),
            "Fund Name": info.get("longName", "N/A"),
            "Expense Ratio": info.get("expenseRatio", "N/A"),
            "AUM (USD)": info.get("totalAssets", "N/A"),
            "Volatility (Annualized)": round(volatility, 4),
            "Max Drawdown (5Y)": round(max_drawdown, 4),
            "Sharpe Ratio": round(sharpe, 4),
            "Asset Type": info.get("category", "N/A"),
            "Index Weighting Strategy": weighting,
            "Top Sectors": sector_str
        }

        return data

    except Exception as e:
        st.error(f"Failed to fetch data for {ticker}: {e}")
        return None

def make_checklist_df(data):
    categories = [
        "Fund Name",
        "Asset Type",
        "Index Weighting Strategy",
        "Top Sectors",
        "Expense Ratio",
        "AUM (USD)",
        "Volatility (Annualized)",
        "Max Drawdown (5Y)",
        "Sharpe Ratio"
    ]
    checklist = { "Category": categories }
    values = []
    for c in categories:
        values.append(data.get(c, "N/A"))
    checklist[data["Ticker"]] = values
    return pd.DataFrame(checklist)

# ----------- Streamlit App ------------

st.title("📊 ETF Checklist & Comparison Tool")

st.markdown("""
Enter ETF ticker symbols to get a detailed checklist with key metrics.
You can compare up to two ETFs side-by-side.
""")

with st.form("etf_form"):
    ticker1 = st.text_input("Enter first ETF ticker (e.g. VOO):").strip().upper()
    compare_switch = st.checkbox("Compare with another ETF?")
    ticker2 = ""
    if compare_switch:
        ticker2 = st.text_input("Enter second ETF ticker:").strip().upper()

    submitted = st.form_submit_button("Fetch ETF Data")

if submitted:
    if not ticker1:
        st.error("Please enter the first ETF ticker.")
    elif not validate_etf(ticker1):
        st.error(f"Ticker '{ticker1}' does not appear to be a valid ETF.")
    else:
        data1 = get_etf_data(ticker1)
        if data1:
            df1 = make_checklist_df(data1)
            st.subheader(f"Checklist for {ticker1}")
            st.table(df1)

            if compare_switch:
                if not ticker2:
                    st.error("Please enter the second ETF ticker for comparison.")
                elif ticker2 == ticker1:
                    st.error("Please enter a different ticker for comparison.")
                elif not validate_etf(ticker2):
                    st.error(f"Ticker '{ticker2}' does not appear to be a valid ETF.")
                else:
                    data2 = get_etf_data(ticker2)
                    if data2:
                        df2 = make_checklist_df(data2)
                        # Merge two dataframes side by side for comparison
                        comparison_df = pd.merge(df1, df2, on="Category", suffixes=(f" ({ticker1})", f" ({ticker2})"))
                        st.subheader(f"Comparison: {ticker1} vs {ticker2}")
                        st.table(comparison_df)


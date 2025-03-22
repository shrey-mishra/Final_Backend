from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from ccxt import binance
import plotly.express as px
import pandas as pd
import json

router = APIRouter()

@router.get("/trending")
def get_trending_coins():
    exchange = binance()
    tickers = exchange.fetch_tickers()
    # Sort by 24h volume to find trending coins
    trending = sorted(tickers.items(), key=lambda x: x[1].get("quoteVolume", 0), reverse=True)[:10]
    return [{"symbol": symbol, "volume": data["quoteVolume"], "last": data["last"]} for symbol, data in trending]

@router.get("/block-orders")
def get_block_orders(symbol: str = "BTC/USDT"):
    exchange = binance()
    trades = exchange.fetch_trades(symbol, limit=100)
    # Filter for large trades (block orders)
    block_orders = [trade for trade in trades if trade["amount"] > 1.0]  # Example threshold
    return block_orders

@router.get("/charts")
def get_live_chart(symbol: str = "BTC/USDT"):
    exchange = binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1m", limit=60)  # Last 60 minutes
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    fig = px.line(df, x="timestamp", y="close", title=f"Live Chart for {symbol}")
    return json.loads(fig.to_json())
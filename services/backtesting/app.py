from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import uuid
import json
import os
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Strategy Backtesting Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# InfluxDB client
influx_client = influxdb_client.InfluxDBClient(
    url=os.getenv("INFLUXDB_URL", "http://localhost:8086"),
    token=os.getenv("INFLUXDB_TOKEN", "my-super-secret-token"),
    org=os.getenv("INFLUXDB_ORG", "crypto_trading")
)
query_api = influx_client.query_api()

class TradingStrategy:
    def __init__(self, params):
        self.params = params
    
    def generate_signals(self, df):
        strategy_type = self.params.get('strategy_type', 'sma_crossover')
        
        if strategy_type == 'sma_crossover':
            return self._sma_crossover_strategy(df)
        elif strategy_type == 'bollinger_bands':
            return self._bollinger_bands_strategy(df)
        elif strategy_type == 'rsi':
            return self._rsi_strategy(df)
        else:
            # Default to SMA crossover
            return self._sma_crossover_strategy(df)
    
    def _sma_crossover_strategy(self, df):
        # Simple moving average crossover strategy
        short_window = self.params.get('short_window', 10)
        long_window = self.params.get('long_window', 50)
        
        # Calculate moving averages
        df['short_ma'] = df['close'].rolling(window=short_window).mean()
        df['long_ma'] = df['close'].rolling(window=long_window).mean()
        
        # Generate signals
        df['signal'] = 0
        df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1  # Buy signal
        df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1  # Sell signal
        
        # Generate positions (1 for buy, -1 for sell, 0 for hold)
        df['position'] = df['signal'].diff()
        
        return df
    
    def _bollinger_bands_strategy(self, df):
        # Bollinger Bands strategy
        window = self.params.get('window', 20)
        num_std = self.params.get('num_std', 2)
        
        # Calculate rolling mean and standard deviation
        df['rolling_mean'] = df['close'].rolling(window=window).mean()
        df['rolling_std'] = df['close'].rolling(window=window).std()
        
        # Calculate Bollinger Bands
        df['upper_band'] = df['rolling_mean'] + (df['rolling_std'] * num_std)
        df['lower_band'] = df['rolling_mean'] - (df['rolling_std'] * num_std)
        
        # Generate signals
        df['signal'] = 0
        df.loc[df['close'] < df['lower_band'], 'signal'] = 1  # Buy signal when price crosses below lower band
        df.loc[df['close'] > df['upper_band'], 'signal'] = -1  # Sell signal when price crosses above upper band
        
        # Generate positions
        df['position'] = df['signal'].diff()
        
        return df
    
    def _rsi_strategy(self, df):
        # RSI strategy
        window = self.params.get('window', 14)
        oversold = self.params.get('oversold', 30)
        overbought = self.params.get('overbought', 70)
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Generate signals
        df['signal'] = 0
        df.loc[df['rsi'] < oversold, 'signal'] = 1  # Buy signal when RSI is oversold
        df.loc[df['rsi'] > overbought, 'signal'] = -1  # Sell signal when RSI is overbought
        
        # Generate positions
        df['position'] = df['signal'].diff()
        
        return df

class BacktestRequest(BaseModel):
    strategy_config: Dict[str, Any]
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 10000.0

class BacktestStatus(BaseModel):
    backtest_id: str
    status: str
    error: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    trades: Optional[List[Dict[str, Any]]] = None
    equity_curve: Optional[List[Dict[str, Any]]] = None

@app.get("/")
async def root():
    return {"message": "Backtesting Service is running"}

@app.post("/api/v1/backtest/run", response_model=BacktestStatus)
async def run_backtest(
    background_tasks: BackgroundTasks,
    request: BacktestRequest
):
    """Run a backtest with the specified strategy configuration"""
    # Generate a unique backtest ID
    backtest_id = str(uuid.uuid4())
    
    # Start backtest in background
    background_tasks.add_task(
        perform_backtest,
        backtest_id,
        request.strategy_config,
        request.symbol,
        request.start_date,
        request.end_date,
        request.initial_capital
    )
    
    return BacktestStatus(backtest_id=backtest_id, status="running")

@app.get("/api/v1/backtest/status/{backtest_id}", response_model=BacktestStatus)
async def get_backtest_status(backtest_id: str):
    """Get the status of a running or completed backtest"""
    # Check if results are available
    try:
        with open(f"results/{backtest_id}.json", "r") as f:
            results = json.load(f)
            return BacktestStatus(**results)
    except FileNotFoundError:
        return BacktestStatus(backtest_id=backtest_id, status="running")

@app.get("/api/v1/backtest/strategies")
async def get_available_strategies():
    """Get list of available trading strategies"""
    return {
        "strategies": [
            {
                "id": "sma_crossover",
                "name": "SMA Crossover",
                "description": "Simple Moving Average Crossover strategy",
                "parameters": [
                    {"name": "short_window", "type": "integer", "default": 10, "description": "Short window period"},
                    {"name": "long_window", "type": "integer", "default": 50, "description": "Long window period"}
                ]
            },
            {
                "id": "bollinger_bands",
                "name": "Bollinger Bands",
                "description": "Bollinger Bands strategy",
                "parameters": [
                    {"name": "window", "type": "integer", "default": 20, "description": "Window period"},
                    {"name": "num_std", "type": "float", "default": 2.0, "description": "Number of standard deviations"}
                ]
            },
            {
                "id": "rsi",
                "name": "RSI",
                "description": "Relative Strength Index strategy",
                "parameters": [
                    {"name": "window", "type": "integer", "default": 14, "description": "RSI period"},
                    {"name": "oversold", "type": "integer", "default": 30, "description": "Oversold threshold"},
                    {"name": "overbought", "type": "integer", "default": 70, "description": "Overbought threshold"}
                ]
            }
        ]
    }

def perform_backtest(
    backtest_id: str,
    strategy_config: Dict[str, Any],
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float
):
    """Perform the backtest in the background"""
    try:
        logger.info(f"Starting backtest {backtest_id} for {symbol}")
        
        # Fetch historical data from InfluxDB
        query = f'''
        from(bucket: "market_data")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "price" and r["symbol"] == "{symbol}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        result = query_api.query_data_frame(query)
        
        if result.empty:
            save_result(backtest_id, {
                "backtest_id": backtest_id,
                "status": "error",
                "error": "No data found for the specified period"
            })
            return
        
        # Convert to dataframe
        df = pd.DataFrame(result)
        df = df.sort_values('_time')
        df = df.rename(columns={'_time': 'time', 'price': 'close'})
        
        # Apply strategy
        strategy = TradingStrategy(strategy_config)
        df = strategy.generate_signals(df)
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['position'].shift(1) * df['returns']
        df['cumulative_returns'] = (1 + df['returns']).cumprod()
        df['strategy_cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
        
        # Calculate portfolio value
        df['portfolio_value'] = initial_capital * df['strategy_cumulative_returns']
        
        # Performance metrics
        total_return = df['portfolio_value'].iloc[-1] / initial_capital - 1
        annual_return = (1 + total_return) ** (252 / len(df)) - 1
        sharpe_ratio = np.sqrt(252) * df['strategy_returns'].mean() / df['strategy_returns'].std()
        max_drawdown = (df['portfolio_value'] / df['portfolio_value'].cummax() - 1).min()
        
        # Count trades
        buy_signals = df[df['position'] == 1]
        sell_signals = df[df['position'] == -1]
        total_trades = len(buy_signals) + len(sell_signals)
        
        # Save results
        results = {
            "backtest_id": backtest_id,
            "status": "completed",
            "metrics": {
                "total_return": total_return,
                "annual_return": annual_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "total_trades": total_trades
            },
            "trades": get_trades(df),
            "equity_curve": get_equity_curve(df)
        }
        
        save_result(backtest_id, results)
        logger.info(f"Completed backtest {backtest_id} for {symbol}")
        
    except Exception as e:
        logger.error(f"Error in backtest {backtest_id}: {e}")
        save_result(backtest_id, {
            "backtest_id": backtest_id,
            "status": "error",
            "error": str(e)
        })

def get_trades(df):
    """Extract buy and sell signals from the dataframe"""
    trades = []
    position = 0
    
    for i, row in df.iterrows():
        if row['position'] == 1:  # Buy signal
            trades.append({
                "type": "buy",
                "time": row['time'].isoformat() if isinstance(row['time'], datetime) else row['time'],
                "price": float(row['close']),
            })
            position = 1
        elif row['position'] == -1 and position == 1:  # Sell signal
            trades.append({
                "type": "sell",
                "time": row['time'].isoformat() if isinstance(row['time'], datetime) else row['time'],
                "price": float(row['close']),
            })
            position = 0
            
    return trades

def get_equity_curve(df):
    """Sample the equity curve (reduce data points for frontend)"""
    # Sample the equity curve (reduce data points for frontend)
    sample_size = min(100, len(df))
    indices = np.linspace(0, len(df) - 1, sample_size, dtype=int)
    sampled = df.iloc[indices]
    
    return [
        {
            "time": row['time'].isoformat() if isinstance(row['time'], datetime) else row['time'],
            "value": float(row['portfolio_value'])
        }
        for _, row in sampled.iterrows()
    ]

def save_result(backtest_id, result):
    """Save backtest result to a JSON file"""
    os.makedirs("results", exist_ok=True)
    with open(f"results/{backtest_id}.json", "w") as f:
        json.dump(result, f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
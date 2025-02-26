from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
import httpx
import asyncio
import json
import os
from kafka import KafkaProducer
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Market Data Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_SERVERS", "localhost:9092"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Models
class PriceData(BaseModel):
    symbol: str
    price: float
    timestamp: int

class SymbolInfo(BaseModel):
    symbol: str
    name: str
    base_asset: str
    quote_asset: str

class MarketOverview(BaseModel):
    prices: Dict[str, float]
    timestamp: int
    volume_24h: Dict[str, float]
    change_24h: Dict[str, float]

@app.get("/")
async def root():
    return {"message": "Market Data Service is running"}

@app.get("/api/v1/market-data/price/{symbol}", response_model=PriceData)
async def get_price(symbol: str):
    """Get the current price for a specific symbol"""
    try:
        # Try to get from cache first
        cached = redis_client.get(f"price:{symbol}")
        if cached:
            data = json.loads(cached)
            return PriceData(
                symbol=symbol,
                price=float(data["price"]),
                timestamp=data["timestamp"]
            )
        
        # If not in cache, fetch from Binance
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch price")
            
            data = response.json()
            price_data = {
                "symbol": symbol,
                "price": float(data["price"]),
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
            
            # Cache for 5 seconds
            redis_client.setex(f"price:{symbol}", 5, json.dumps(price_data))
            return PriceData(**price_data)
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/market-data/symbols", response_model=List[SymbolInfo])
async def get_symbols():
    """Get list of available trading symbols"""
    try:
        # Try to get from cache first
        cached = redis_client.get("symbols")
        if cached:
            return json.loads(cached)
        
        # If not in cache, fetch from Binance
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.binance.com/api/v3/exchangeInfo")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch symbols")
            
            data = response.json()
            symbols = []
            for symbol_data in data["symbols"]:
                if symbol_data["status"] == "TRADING":
                    symbols.append(SymbolInfo(
                        symbol=symbol_data["symbol"],
                        name=symbol_data["symbol"],
                        base_asset=symbol_data["baseAsset"],
                        quote_asset=symbol_data["quoteAsset"]
                    ))
            
            # Cache for 1 hour
            redis_client.setex("symbols", 3600, json.dumps([s.dict() for s in symbols]))
            return symbols
    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/market-data/overview", response_model=MarketOverview)
async def get_market_overview():
    """Get an overview of the market with prices, volumes, and 24h changes"""
    try:
        # Try to get from cache first
        cached = redis_client.get("market_overview")
        if cached:
            return json.loads(cached)
        
        # If not in cache, fetch from Binance
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT", "XRPUSDT"]
        prices = {}
        volume_24h = {}
        change_24h = {}
        
        async with httpx.AsyncClient() as client:
            # Get 24h ticker data
            response = await client.get("https://api.binance.com/api/v3/ticker/24hr")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch market data")
            
            data = response.json()
            for ticker in data:
                if ticker["symbol"] in symbols:
                    symbol = ticker["symbol"]
                    prices[symbol] = float(ticker["lastPrice"])
                    volume_24h[symbol] = float(ticker["volume"])
                    change_24h[symbol] = float(ticker["priceChangePercent"])
            
            overview = {
                "prices": prices,
                "timestamp": int(datetime.now().timestamp() * 1000),
                "volume_24h": volume_24h,
                "change_24h": change_24h
            }
            
            # Cache for 60 seconds
            redis_client.setex("market_overview", 60, json.dumps(overview))
            return overview
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task to fetch prices
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fetch_prices_continuously())

async def fetch_prices_continuously():
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT", "XRPUSDT"]
    async with httpx.AsyncClient() as client:
        while True:
            try:
                for symbol in symbols:
                    try:
                        response = await client.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")
                        if response.status_code == 200:
                            data = response.json()
                            price_data = {
                                "symbol": symbol,
                                "price": float(data["price"]),
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            }
                            
                            # Update Redis cache
                            redis_client.setex(f"price:{symbol}", 5, json.dumps(price_data))
                            
                            # Send to Kafka
                            producer.send('market-events', price_data)
                            logger.debug(f"Updated price for {symbol}: {price_data['price']}")
                    except Exception as e:
                        logger.error(f"Error fetching {symbol}: {e}")
                
                # Fetch market overview every minute
                if datetime.now().second == 0:
                    await get_market_overview()
                    
            except Exception as e:
                logger.error(f"Error in price fetching loop: {e}")
                
            await asyncio.sleep(1)  # Fetch every second

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
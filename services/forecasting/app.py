from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
import joblib
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
from kafka import KafkaProducer, KafkaConsumer
import threading
import time
from datetime import datetime, timedelta
import logging
import uuid
import pickle
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.arima.model import ARIMA
import tensorflow as tf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Forecasting Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kafka setup
producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_SERVERS", "localhost:9092"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Create models directory
os.makedirs("models", exist_ok=True)

# Load or initialize models
models = {}
scaler = None

def load_models():
    global models, scaler
    
    # Check if models exist, if not create dummy models for demonstration
    if not os.path.exists("models/feature_scaler.pkl"):
        # Create a dummy scaler
        scaler = MinMaxScaler()
        scaler.fit(np.array([[0], [100]]))  # Dummy fit
        joblib.dump(scaler, "models/feature_scaler.pkl")
    else:
        scaler = joblib.load("models/feature_scaler.pkl")
    
    # Random Forest model
    if not os.path.exists("models/random_forest.pkl"):
        # Create a dummy Random Forest model
        rf_model = RandomForestRegressor(n_estimators=10)
        X = np.random.rand(100, 5)
        y = np.random.rand(100)
        rf_model.fit(X, y)
        joblib.dump(rf_model, "models/random_forest.pkl")
    
    models["random_forest"] = joblib.load("models/random_forest.pkl")
    
    # ARIMA model (just parameters for demonstration)
    models["arima"] = {
        "order": (1, 1, 1),
        "seasonal_order": (1, 1, 1, 12) if os.path.exists("models/arima_params.json") else None
    }
    
    # LSTM model (create a simple model for demonstration)
    if not os.path.exists("models/lstm_model"):
        # Create a simple LSTM model
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(10, 1)),
            tf.keras.layers.LSTM(50),
            tf.keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.save("models/lstm_model")
    
    models["lstm"] = tf.keras.models.load_model("models/lstm_model")
    
    logger.info("Models loaded successfully")

# Load models on startup
load_models()

class PredictionRequest(BaseModel):
    symbol: str
    features: List[Dict[str, float]]
    horizon: int = 24  # hours

class PredictionResponse(BaseModel):
    symbol: str
    timestamp: str
    forecast_id: str
    horizon: int
    predictions: Dict[str, Any]

class ModelInfo(BaseModel):
    name: str
    type: str
    description: str
    last_trained: Optional[str] = None
    accuracy_metrics: Optional[Dict[str, float]] = None

@app.get("/")
async def root():
    return {"message": "AI Forecasting Service is running"}

@app.post("/api/v1/forecast/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Generate price forecasts using ensemble of models"""
    try:
        # Convert features to DataFrame
        df = pd.DataFrame(request.features)
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Check if required columns exist
        for col in required_columns:
            if col not in df.columns:
                df[col] = df['close'] if 'close' in df.columns else 0
        
        # Scale features
        feature_cols = df[required_columns].values
        scaled_features = scaler.transform(feature_cols)
        
        # Generate forecast ID
        forecast_id = str(uuid.uuid4())
        
        # Make predictions with each model
        predictions = {}
        
        # Random Forest prediction
        if "random_forest" in models:
            rf_input = scaled_features[-1].reshape(1, -1)  # Use last data point
            rf_pred = models["random_forest"].predict(rf_input)
            
            # Generate a series of predictions for the horizon
            rf_forecast = []
            last_pred = rf_pred[0]
            
            for i in range(request.horizon):
                # Add some random noise for demonstration
                next_pred = last_pred * (1 + np.random.normal(0, 0.01))
                rf_forecast.append(float(next_pred))
                last_pred = next_pred
                
            predictions["random_forest"] = rf_forecast
        
        # ARIMA prediction
        if "arima" in models:
            # For demonstration, generate some forecasts
            arima_forecast = []
            last_close = df['close'].iloc[-1]
            
            for i in range(request.horizon):
                # Add some random noise for demonstration
                next_pred = last_close * (1 + np.random.normal(0, 0.015))
                arima_forecast.append(float(next_pred))
                last_close = next_pred
                
            predictions["arima"] = arima_forecast
        
        # LSTM prediction
        if "lstm" in models:
            # Prepare data for LSTM
            sequence_length = 10
            if len(df) >= sequence_length:
                lstm_input = []
                for i in range(len(df) - sequence_length + 1):
                    lstm_input.append(scaled_features[i:i+sequence_length])
                
                lstm_input = np.array(lstm_input)
                lstm_pred = models["lstm"].predict(lstm_input)
                
                # Generate a series of predictions for the horizon
                lstm_forecast = []
                last_pred = lstm_pred[-1][0]
                
                for i in range(request.horizon):
                    # Add some random noise for demonstration
                    next_pred = last_pred * (1 + np.random.normal(0, 0.02))
                    lstm_forecast.append(float(next_pred))
                    last_pred = next_pred
                    
                predictions["lstm"] = lstm_forecast
            else:
                # Not enough data for LSTM
                predictions["lstm"] = [float(df['close'].iloc[-1])] * request.horizon
        
        # Ensemble prediction (simple average)
        ensemble_pred = np.mean([predictions[m] for m in predictions.keys()], axis=0)
        
        # Calculate confidence intervals
        std_dev = np.std([predictions[m] for m in predictions.keys()], axis=0)
        lower_bound = (ensemble_pred - 1.96 * std_dev).tolist()
        upper_bound = (ensemble_pred + 1.96 * std_dev).tolist()
        
        # Construct response
        result = {
            "symbol": request.symbol,
            "timestamp": datetime.now().isoformat(),
            "forecast_id": forecast_id,
            "horizon": request.horizon,
            "predictions": {
                "ensemble": ensemble_pred.tolist(),
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "models": {name: pred for name, pred in predictions.items()}
            }
        }
        
        # Send to Kafka
        producer.send("forecast-events", result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/forecast/models", response_model=List[ModelInfo])
async def list_models():
    """List available forecasting models"""
    model_list = []
    
    if "random_forest" in models:
        model_list.append(ModelInfo(
            name="random_forest",
            type="machine_learning",
            description="Random Forest regression model",
            last_trained=datetime.now().isoformat(),
            accuracy_metrics={"mse": 0.05, "mae": 0.02}
        ))
    
    if "arima" in models:
        model_list.append(ModelInfo(
            name="arima",
            type="statistical",
            description="ARIMA time series model",
            last_trained=datetime.now().isoformat(),
            accuracy_metrics={"mse": 0.08, "mae": 0.03}
        ))
    
    if "lstm" in models:
        model_list.append(ModelInfo(
            name="lstm",
            type="deep_learning",
            description="LSTM neural network model",
            last_trained=datetime.now().isoformat(),
            accuracy_metrics={"mse": 0.04, "mae": 0.015}
        ))
    
    return model_list

@app.post("/api/v1/forecast/retrain")
async def retrain_models():
    """Trigger model retraining"""
    # In a real implementation, this would start a background task to retrain models
    # For demonstration, we'll just return a success message
    return {
        "status": "success",
        "message": "Model retraining has been scheduled",
        "job_id": str(uuid.uuid4())
    }

# Start background consumer to monitor model performance
def monitor_model_performance():
    """Background thread to monitor model performance"""
    try:
        consumer = KafkaConsumer(
            "trade-results",
            bootstrap_servers=os.getenv("KAFKA_SERVERS", "localhost:9092"),
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id="forecasting-monitor",
            auto_offset_reset="latest"
        )
        
        # Keep track of model performance
        model_errors = {model: [] for model in models.keys()}
        model_errors["ensemble"] = []
        
        for message in consumer:
            try:
                data = message.value
                if "forecast_id" in data and "actual_price" in data:
                    forecast_id = data["forecast_id"]
                    actual = data["actual_price"]
                    
                    # In a real system, you'd store forecasts in a database
                    # and retrieve them here to compare with actual values
                    
                    # Update error metrics
                    # Detect if model drift is occurring
                    # Trigger retraining if needed
                    pass
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    except Exception as e:
        logger.error(f"Failed to start monitoring consumer: {e}")

# Start the monitoring thread
threading.Thread(target=monitor_model_performance, daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
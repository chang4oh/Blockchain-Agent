#!/bin/bash

# Kong API Gateway Configuration Script
# This script sets up Kong API Gateway with the necessary routes and services

echo "Configuring Kong API Gateway..."

# Check if Kong is running
kong_status=$(curl -s http://localhost:8001/status)
if [ $? -ne 0 ]; then
    echo "Error: Kong Admin API is not accessible. Make sure Kong is running."
    exit 1
fi

# Create Services
echo "Creating services..."

# Market Data Service
curl -s -X POST http://localhost:8001/services \
    --data name=market-data-service \
    --data url=http://market-data:8000

# Risk Management Service
curl -s -X POST http://localhost:8001/services \
    --data name=risk-management-service \
    --data url=http://risk-management:8080

# Backtesting Service
curl -s -X POST http://localhost:8001/services \
    --data name=backtesting-service \
    --data url=http://backtesting:8000

# AI Forecasting Service
curl -s -X POST http://localhost:8001/services \
    --data name=forecasting-service \
    --data url=http://forecasting:8000

# Create Routes
echo "Creating routes..."

# Market Data Routes
curl -s -X POST http://localhost:8001/services/market-data-service/routes \
    --data name=market-data-route \
    --data paths[]=/api/v1/market-data

# Risk Management Routes
curl -s -X POST http://localhost:8001/services/risk-management-service/routes \
    --data name=risk-management-route \
    --data paths[]=/api/v1/risk-management

# Backtesting Routes
curl -s -X POST http://localhost:8001/services/backtesting-service/routes \
    --data name=backtesting-route \
    --data paths[]=/api/v1/backtesting

# AI Forecasting Routes
curl -s -X POST http://localhost:8001/services/forecasting-service/routes \
    --data name=forecasting-route \
    --data paths[]=/api/v1/forecasting

# Enable Plugins
echo "Enabling plugins..."

# Rate Limiting
curl -s -X POST http://localhost:8001/plugins \
    --data name=rate-limiting \
    --data config.minute=100 \
    --data config.hour=1000

# JWT Authentication
curl -s -X POST http://localhost:8001/plugins \
    --data name=jwt \
    --data config.secret_is_base64=false

# CORS
curl -s -X POST http://localhost:8001/plugins \
    --data name=cors \
    --data config.origins=* \
    --data config.methods=GET,POST,PUT,DELETE,OPTIONS \
    --data config.headers=Content-Type,Authorization \
    --data config.exposed_headers=* \
    --data config.credentials=true \
    --data config.max_age=3600

echo "Kong configuration completed successfully!" 
const express = require('express');
const router = express.Router();

// Mock data for cryptocurrency prices
const cryptoData = [
  { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC', price: 51234.56, change24h: 2.34 },
  { id: 'ethereum', name: 'Ethereum', symbol: 'ETH', price: 2789.12, change24h: -1.45 },
  { id: 'cardano', name: 'Cardano', symbol: 'ADA', price: 1.23, change24h: 5.67 },
  { id: 'solana', name: 'Solana', symbol: 'SOL', price: 98.76, change24h: 3.21 },
  { id: 'ripple', name: 'Ripple', symbol: 'XRP', price: 0.54, change24h: -0.87 }
];

// Mock user settings - API keys are stored securely and never returned in full
let userSettings = {
  riskPercentage: 1,
  maxTradesPerDay: 5,
  defaultLeverage: 1,
  preferredMarket: 'SPOT',
  apiKeys: {
    blockchain: process.env.BLOCKCHAIN_API_KEY || '',
    exchange: process.env.EXCHANGE_API_KEY || ''
  }
};

// Helper function to mask API keys
const maskApiKey = (key) => {
  if (!key) return '';
  if (key.length <= 8) return '*'.repeat(key.length);
  return key.substring(0, 4) + '*'.repeat(key.length - 8) + key.substring(key.length - 4);
};

// Get all cryptocurrencies
router.get('/cryptocurrencies', (req, res) => {
  res.json({
    success: true,
    data: cryptoData
  });
});

// Get a specific cryptocurrency
router.get('/cryptocurrencies/:id', (req, res) => {
  const crypto = cryptoData.find(c => c.id === req.params.id);
  
  if (!crypto) {
    return res.status(404).json({
      success: false,
      message: 'Cryptocurrency not found'
    });
  }
  
  res.json({
    success: true,
    data: crypto
  });
});

// Get price prediction for a cryptocurrency
router.get('/predict/:id', (req, res) => {
  const crypto = cryptoData.find(c => c.id === req.params.id);
  
  if (!crypto) {
    return res.status(404).json({
      success: false,
      message: 'Cryptocurrency not found'
    });
  }
  
  // Mock prediction data
  const prediction = {
    currentPrice: crypto.price,
    prediction24h: crypto.price * (1 + (Math.random() * 0.1 - 0.05)),
    prediction7d: crypto.price * (1 + (Math.random() * 0.2 - 0.1)),
    confidence: Math.floor(Math.random() * 30) + 70
  };
  
  res.json({
    success: true,
    data: prediction
  });
});

// Get user settings - never return full API keys
router.get('/settings', (req, res) => {
  // Create a copy of settings with masked API keys
  const safeSettings = {
    ...userSettings,
    apiKeys: {
      blockchain: userSettings.apiKeys.blockchain ? {
        exists: true,
        maskedValue: maskApiKey(userSettings.apiKeys.blockchain)
      } : { exists: false },
      exchange: userSettings.apiKeys.exchange ? {
        exists: true,
        maskedValue: maskApiKey(userSettings.apiKeys.exchange)
      } : { exists: false }
    }
  };
  
  res.json({
    success: true,
    data: safeSettings
  });
});

// Update user settings
router.put('/settings', (req, res) => {
  const { riskPercentage, maxTradesPerDay, defaultLeverage, preferredMarket, apiKeys } = req.body;
  
  // Validate input
  if (riskPercentage !== undefined && (riskPercentage < 0.1 || riskPercentage > 100)) {
    return res.status(400).json({
      success: false,
      message: 'Risk percentage must be between 0.1 and 100'
    });
  }
  
  if (maxTradesPerDay !== undefined && (maxTradesPerDay < 1 || maxTradesPerDay > 100)) {
    return res.status(400).json({
      success: false,
      message: 'Max trades per day must be between 1 and 100'
    });
  }
  
  if (defaultLeverage !== undefined && (defaultLeverage < 1 || defaultLeverage > 100)) {
    return res.status(400).json({
      success: false,
      message: 'Default leverage must be between 1 and 100'
    });
  }
  
  if (preferredMarket !== undefined && !['SPOT', 'FUTURES'].includes(preferredMarket)) {
    return res.status(400).json({
      success: false,
      message: 'Preferred market must be either SPOT or FUTURES'
    });
  }
  
  // Update settings
  userSettings = {
    ...userSettings,
    ...(riskPercentage !== undefined && { riskPercentage }),
    ...(maxTradesPerDay !== undefined && { maxTradesPerDay }),
    ...(defaultLeverage !== undefined && { defaultLeverage }),
    ...(preferredMarket !== undefined && { preferredMarket })
  };
  
  // Handle API keys separately for security
  if (apiKeys) {
    // In a real app, you would encrypt these before storing
    if (apiKeys.blockchain) {
      userSettings.apiKeys.blockchain = apiKeys.blockchain;
      
      // In a production environment, you would update the actual API key in a secure storage
      // and potentially update environment variables
      // process.env.BLOCKCHAIN_API_KEY = apiKeys.blockchain;
    }
    
    if (apiKeys.exchange) {
      userSettings.apiKeys.exchange = apiKeys.exchange;
      
      // In a production environment, you would update the actual API key in a secure storage
      // and potentially update environment variables
      // process.env.EXCHANGE_API_KEY = apiKeys.exchange;
    }
  }
  
  // Return masked API keys in response
  const safeSettings = {
    ...userSettings,
    apiKeys: {
      blockchain: userSettings.apiKeys.blockchain ? {
        exists: true,
        maskedValue: maskApiKey(userSettings.apiKeys.blockchain)
      } : { exists: false },
      exchange: userSettings.apiKeys.exchange ? {
        exists: true,
        maskedValue: maskApiKey(userSettings.apiKeys.exchange)
      } : { exists: false }
    }
  };
  
  res.json({
    success: true,
    message: 'Settings updated successfully',
    data: safeSettings
  });
});

// Execute a trade
router.post('/trade', (req, res) => {
  const { cryptoId, action, amount } = req.body;
  
  // Validate input
  if (!cryptoId || !action || !amount) {
    return res.status(400).json({
      success: false,
      message: 'Missing required fields: cryptoId, action, amount'
    });
  }
  
  if (!['BUY', 'SELL'].includes(action.toUpperCase())) {
    return res.status(400).json({
      success: false,
      message: 'Action must be either BUY or SELL'
    });
  }
  
  if (isNaN(amount) || amount <= 0) {
    return res.status(400).json({
      success: false,
      message: 'Amount must be a positive number'
    });
  }
  
  const crypto = cryptoData.find(c => c.id === cryptoId);
  
  if (!crypto) {
    return res.status(404).json({
      success: false,
      message: 'Cryptocurrency not found'
    });
  }
  
  // Check if API keys are set before allowing trades
  if (!userSettings.apiKeys.exchange) {
    return res.status(403).json({
      success: false,
      message: 'Exchange API key is required to execute trades'
    });
  }
  
  // Mock trade execution
  const trade = {
    id: Math.random().toString(36).substring(2, 15),
    cryptoId,
    cryptoSymbol: crypto.symbol,
    action: action.toUpperCase(),
    amount: parseFloat(amount),
    price: crypto.price,
    total: crypto.price * parseFloat(amount),
    timestamp: new Date().toISOString()
  };
  
  res.json({
    success: true,
    message: `${action.toUpperCase()} order executed successfully`,
    data: trade
  });
});

module.exports = router; 
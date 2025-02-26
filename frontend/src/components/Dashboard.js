import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const API_BASE_URL = 'http://localhost:5000/api';

const Dashboard = () => {
  const [cryptoData, setCryptoData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCrypto, setSelectedCrypto] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [tradeAmount, setTradeAmount] = useState('');
  const [tradeStatus, setTradeStatus] = useState('');
  const [error, setError] = useState(null);
  const [apiKeyStatus, setApiKeyStatus] = useState({
    blockchain: false,
    exchange: false
  });

  // Fetch cryptocurrency data from backend
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch cryptocurrency data
        const response = await fetch(`${API_BASE_URL}/cryptocurrencies`);
        const result = await response.json();
        
        if (result.success) {
          setCryptoData(result.data);
        } else {
          setError(result.message || 'Failed to fetch cryptocurrency data');
        }
        
        // Check API key status
        const settingsResponse = await fetch(`${API_BASE_URL}/settings`);
        const settingsResult = await settingsResponse.json();
        
        if (settingsResult.success) {
          setApiKeyStatus({
            blockchain: settingsResult.data.apiKeys.blockchain.exists,
            exchange: settingsResult.data.apiKeys.exchange.exists
          });
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError('Network error. Please check your connection and try again.');
        setLoading(false);
        
        // Fallback to mock data if API is not available
        const mockData = [
          { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC', price: 51234.56, change24h: 2.34 },
          { id: 'ethereum', name: 'Ethereum', symbol: 'ETH', price: 2789.12, change24h: -1.45 },
          { id: 'cardano', name: 'Cardano', symbol: 'ADA', price: 1.23, change24h: 5.67 },
          { id: 'solana', name: 'Solana', symbol: 'SOL', price: 98.76, change24h: 3.21 },
          { id: 'ripple', name: 'Ripple', symbol: 'XRP', price: 0.54, change24h: -0.87 }
        ];
        setCryptoData(mockData);
      }
    };

    fetchData();
  }, []);

  const handleCryptoSelect = async (crypto) => {
    setSelectedCrypto(crypto);
    
    try {
      setError(null);
      
      // Fetch prediction data from backend if blockchain API key exists
      if (apiKeyStatus.blockchain) {
        const response = await fetch(`${API_BASE_URL}/predict/${crypto.id}`);
        const result = await response.json();
        
        if (result.success) {
          setPredictionData(result.data);
          return;
        }
      }
      
      // Fallback to mock prediction if API key is missing or request fails
      setPredictionData({
        currentPrice: crypto.price,
        prediction24h: crypto.price * (1 + (Math.random() * 0.1 - 0.05)),
        prediction7d: crypto.price * (1 + (Math.random() * 0.2 - 0.1)),
        confidence: Math.floor(Math.random() * 30) + 70
      });
      
    } catch (error) {
      console.error('Error fetching prediction:', error);
      // Fallback to mock prediction
      setPredictionData({
        currentPrice: crypto.price,
        prediction24h: crypto.price * (1 + (Math.random() * 0.1 - 0.05)),
        prediction7d: crypto.price * (1 + (Math.random() * 0.2 - 0.1)),
        confidence: Math.floor(Math.random() * 30) + 70
      });
    }
  };

  const handleTrade = async (action) => {
    if (!tradeAmount || isNaN(tradeAmount) || parseFloat(tradeAmount) <= 0) {
      setTradeStatus('Please enter a valid amount');
      return;
    }
    
    // Check if exchange API key is set
    if (!apiKeyStatus.exchange) {
      setTradeStatus('Exchange API key is required. Please set it in Settings.');
      setTimeout(() => setTradeStatus(''), 5000);
      return;
    }

    try {
      setError(null);
      
      // Call backend API to execute trade
      const response = await fetch(`${API_BASE_URL}/trade`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          cryptoId: selectedCrypto.id,
          action: action,
          amount: parseFloat(tradeAmount)
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        setTradeStatus(`${action} order for ${tradeAmount} ${selectedCrypto.symbol} placed successfully!`);
        setTradeAmount('');
      } else {
        setTradeStatus(`Error: ${result.message}`);
      }
      
    } catch (error) {
      console.error('Error executing trade:', error);
      setTradeStatus('Network error. Please try again.');
    }
    
    // Reset status after 3 seconds
    setTimeout(() => setTradeStatus(''), 3000);
  };

  return (
    <div className="dashboard-container">
      <h1>Cryptocurrency Dashboard</h1>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      {!apiKeyStatus.blockchain && (
        <div className="warning-message">
          <strong>Warning:</strong> Blockchain API key is not set. Predictions are using mock data. 
          <button 
            className="settings-link-button"
            onClick={() => window.location.hash = 'settings'}
          >
            Go to Settings
          </button>
        </div>
      )}
      
      <div className="dashboard-grid">
        <div className="crypto-list">
          <h2>Market Overview</h2>
          {loading ? (
            <p>Loading cryptocurrency data...</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Price (USD)</th>
                  <th>24h Change</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {cryptoData.map(crypto => (
                  <tr key={crypto.id}>
                    <td>{crypto.name} ({crypto.symbol})</td>
                    <td>${crypto.price.toLocaleString()}</td>
                    <td className={crypto.change24h >= 0 ? 'positive-change' : 'negative-change'}>
                      {crypto.change24h >= 0 ? '+' : ''}{crypto.change24h}%
                    </td>
                    <td>
                      <button onClick={() => handleCryptoSelect(crypto)}>
                        Select
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        
        <div className="crypto-detail">
          {selectedCrypto ? (
            <>
              <h2>{selectedCrypto.name} ({selectedCrypto.symbol}) Analysis</h2>
              
              <div className="price-card">
                <h3>Current Price</h3>
                <p className="price">${selectedCrypto.price.toLocaleString()}</p>
                <p className={selectedCrypto.change24h >= 0 ? 'positive-change' : 'negative-change'}>
                  24h Change: {selectedCrypto.change24h >= 0 ? '+' : ''}{selectedCrypto.change24h}%
                </p>
              </div>
              
              {predictionData && (
                <div className="prediction-card">
                  <h3>AI Price Prediction</h3>
                  {!apiKeyStatus.blockchain && (
                    <div className="prediction-notice">Using mock prediction data</div>
                  )}
                  <div className="prediction-grid">
                    <div>
                      <h4>24h Forecast</h4>
                      <p>${predictionData.prediction24h.toLocaleString()}</p>
                      <p className={predictionData.prediction24h > selectedCrypto.price ? 'positive-change' : 'negative-change'}>
                        {((predictionData.prediction24h / selectedCrypto.price - 1) * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <h4>7d Forecast</h4>
                      <p>${predictionData.prediction7d.toLocaleString()}</p>
                      <p className={predictionData.prediction7d > selectedCrypto.price ? 'positive-change' : 'negative-change'}>
                        {((predictionData.prediction7d / selectedCrypto.price - 1) * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <h4>Confidence</h4>
                      <p>{predictionData.confidence}%</p>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="trading-card">
                <h3>Trading</h3>
                {!apiKeyStatus.exchange && (
                  <div className="trading-notice">
                    Exchange API key is required for trading. 
                    <button 
                      className="settings-link-button"
                      onClick={() => window.location.hash = 'settings'}
                    >
                      Set API Key
                    </button>
                  </div>
                )}
                <div className="trading-form">
                  <input
                    type="number"
                    value={tradeAmount}
                    onChange={(e) => setTradeAmount(e.target.value)}
                    placeholder={`Amount in ${selectedCrypto.symbol}`}
                  />
                  <div className="trading-buttons">
                    <button 
                      className="buy-button" 
                      onClick={() => handleTrade('BUY')}
                      disabled={!apiKeyStatus.exchange}
                    >
                      Buy
                    </button>
                    <button 
                      className="sell-button" 
                      onClick={() => handleTrade('SELL')}
                      disabled={!apiKeyStatus.exchange}
                    >
                      Sell
                    </button>
                  </div>
                </div>
                {tradeStatus && <p className="trade-status">{tradeStatus}</p>}
              </div>
            </>
          ) : (
            <div className="select-crypto-message">
              <h2>Select a cryptocurrency to view details</h2>
              <p>Click on a cryptocurrency from the list to view detailed analysis and trading options.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 
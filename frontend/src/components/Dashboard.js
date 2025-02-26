import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const Dashboard = () => {
  const [cryptoData, setCryptoData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCrypto, setSelectedCrypto] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [tradeAmount, setTradeAmount] = useState('');
  const [tradeStatus, setTradeStatus] = useState('');

  // Mock data for demonstration
  useEffect(() => {
    // In a real app, this would be an API call to your backend
    const fetchData = async () => {
      try {
        // Simulating API call delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Mock cryptocurrency data
        const mockData = [
          { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC', price: 51234.56, change24h: 2.34 },
          { id: 'ethereum', name: 'Ethereum', symbol: 'ETH', price: 2789.12, change24h: -1.45 },
          { id: 'cardano', name: 'Cardano', symbol: 'ADA', price: 1.23, change24h: 5.67 },
          { id: 'solana', name: 'Solana', symbol: 'SOL', price: 98.76, change24h: 3.21 },
          { id: 'ripple', name: 'Ripple', symbol: 'XRP', price: 0.54, change24h: -0.87 }
        ];
        
        setCryptoData(mockData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleCryptoSelect = (crypto) => {
    setSelectedCrypto(crypto);
    
    // Mock prediction data
    setPredictionData({
      currentPrice: crypto.price,
      prediction24h: crypto.price * (1 + (Math.random() * 0.1 - 0.05)),
      prediction7d: crypto.price * (1 + (Math.random() * 0.2 - 0.1)),
      confidence: Math.floor(Math.random() * 30) + 70
    });
  };

  const handleTrade = (action) => {
    if (!tradeAmount || isNaN(tradeAmount) || parseFloat(tradeAmount) <= 0) {
      setTradeStatus('Please enter a valid amount');
      return;
    }

    // In a real app, this would call your backend API
    setTradeStatus(`${action} order for ${tradeAmount} ${selectedCrypto.symbol} placed successfully!`);
    setTradeAmount('');
    
    // Reset status after 3 seconds
    setTimeout(() => setTradeStatus(''), 3000);
  };

  return (
    <div className="dashboard-container">
      <h1>Cryptocurrency Dashboard</h1>
      
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
                <div className="trading-form">
                  <input
                    type="number"
                    value={tradeAmount}
                    onChange={(e) => setTradeAmount(e.target.value)}
                    placeholder={`Amount in ${selectedCrypto.symbol}`}
                  />
                  <div className="trading-buttons">
                    <button className="buy-button" onClick={() => handleTrade('Buy')}>
                      Buy
                    </button>
                    <button className="sell-button" onClick={() => handleTrade('Sell')}>
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
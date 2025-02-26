import React, { useState } from 'react';
import './Settings.css';

const Settings = () => {
  const [settings, setSettings] = useState({
    riskPercentage: 1,
    maxTradesPerDay: 5,
    defaultLeverage: 1,
    preferredMarket: 'SPOT',
    apiKeys: {
      blockchain: '',
      exchange: ''
    },
    notifications: {
      email: true,
      push: false,
      sms: false
    }
  });

  const [saved, setSaved] = useState(false);
  const [showApiKeys, setShowApiKeys] = useState({
    blockchain: false,
    exchange: false
  });

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (name.includes('.')) {
      const [category, key] = name.split('.');
      setSettings(prev => ({
        ...prev,
        [category]: {
          ...prev[category],
          [key]: type === 'checkbox' ? checked : value
        }
      }));
    } else {
      setSettings(prev => ({
        ...prev,
        [name]: type === 'number' ? parseFloat(value) : value
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // In a real app, this would call your backend API
    // Never log API keys to the console in production
    console.log('Saving settings:', {
      ...settings,
      apiKeys: {
        blockchain: settings.apiKeys.blockchain ? '********' : '',
        exchange: settings.apiKeys.exchange ? '********' : ''
      }
    });
    
    // Show saved message
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const toggleShowApiKey = (keyName) => {
    setShowApiKeys(prev => ({
      ...prev,
      [keyName]: !prev[keyName]
    }));
  };

  // Function to mask API keys for display
  const maskApiKey = (key) => {
    if (!key) return '';
    if (key.length <= 8) return '*'.repeat(key.length);
    return key.substring(0, 4) + '*'.repeat(key.length - 8) + key.substring(key.length - 4);
  };

  return (
    <div className="settings-container">
      <h1>Trading Settings</h1>
      
      {saved && (
        <div className="success-message">
          Settings saved successfully!
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="settings-section">
          <h2>Risk Management</h2>
          
          <div className="form-group">
            <label htmlFor="riskPercentage">Risk Percentage per Trade (%)</label>
            <input
              type="number"
              id="riskPercentage"
              name="riskPercentage"
              min="0.1"
              max="100"
              step="0.1"
              value={settings.riskPercentage}
              onChange={handleInputChange}
            />
            <p className="help-text">Percentage of your portfolio to risk on each trade</p>
          </div>
          
          <div className="form-group">
            <label htmlFor="maxTradesPerDay">Maximum Trades per Day</label>
            <input
              type="number"
              id="maxTradesPerDay"
              name="maxTradesPerDay"
              min="1"
              max="100"
              value={settings.maxTradesPerDay}
              onChange={handleInputChange}
            />
            <p className="help-text">Limit the number of trades per day to manage risk</p>
          </div>
          
          <div className="form-group">
            <label htmlFor="defaultLeverage">Default Leverage</label>
            <input
              type="number"
              id="defaultLeverage"
              name="defaultLeverage"
              min="1"
              max="100"
              value={settings.defaultLeverage}
              onChange={handleInputChange}
            />
            <p className="help-text">Default leverage for futures trading (1 = no leverage)</p>
          </div>
          
          <div className="form-group">
            <label htmlFor="preferredMarket">Preferred Market</label>
            <select
              id="preferredMarket"
              name="preferredMarket"
              value={settings.preferredMarket}
              onChange={handleInputChange}
            >
              <option value="SPOT">Spot</option>
              <option value="FUTURES">Futures</option>
            </select>
            <p className="help-text">Your preferred market type for trading</p>
          </div>
        </div>
        
        <div className="settings-section">
          <h2>API Keys</h2>
          <p className="security-notice">Your API keys are encrypted and securely stored. Never share your API keys with anyone.</p>
          
          <div className="form-group">
            <label htmlFor="blockchain-api">Blockchain API Key</label>
            <div className="api-key-input-group">
              <input
                type={showApiKeys.blockchain ? "text" : "password"}
                id="blockchain-api"
                name="apiKeys.blockchain"
                value={settings.apiKeys.blockchain}
                onChange={handleInputChange}
                placeholder="Enter your blockchain API key"
                autoComplete="off"
              />
              <button 
                type="button" 
                className="toggle-visibility-btn"
                onClick={() => toggleShowApiKey('blockchain')}
              >
                {showApiKeys.blockchain ? 'Hide' : 'Show'}
              </button>
            </div>
            {settings.apiKeys.blockchain && (
              <div className="key-display">
                <span>Stored key: {showApiKeys.blockchain ? settings.apiKeys.blockchain : maskApiKey(settings.apiKeys.blockchain)}</span>
              </div>
            )}
            <p className="help-text">API key for blockchain data provider</p>
          </div>
          
          <div className="form-group">
            <label htmlFor="exchange-api">Exchange API Key</label>
            <div className="api-key-input-group">
              <input
                type={showApiKeys.exchange ? "text" : "password"}
                id="exchange-api"
                name="apiKeys.exchange"
                value={settings.apiKeys.exchange}
                onChange={handleInputChange}
                placeholder="Enter your exchange API key"
                autoComplete="off"
              />
              <button 
                type="button" 
                className="toggle-visibility-btn"
                onClick={() => toggleShowApiKey('exchange')}
              >
                {showApiKeys.exchange ? 'Hide' : 'Show'}
              </button>
            </div>
            {settings.apiKeys.exchange && (
              <div className="key-display">
                <span>Stored key: {showApiKeys.exchange ? settings.apiKeys.exchange : maskApiKey(settings.apiKeys.exchange)}</span>
              </div>
            )}
            <p className="help-text">API key for your cryptocurrency exchange</p>
          </div>
        </div>
        
        <div className="settings-section">
          <h2>Notifications</h2>
          
          <div className="form-group checkbox-group">
            <input
              type="checkbox"
              id="email-notifications"
              name="notifications.email"
              checked={settings.notifications.email}
              onChange={handleInputChange}
            />
            <label htmlFor="email-notifications">Email Notifications</label>
          </div>
          
          <div className="form-group checkbox-group">
            <input
              type="checkbox"
              id="push-notifications"
              name="notifications.push"
              checked={settings.notifications.push}
              onChange={handleInputChange}
            />
            <label htmlFor="push-notifications">Push Notifications</label>
          </div>
          
          <div className="form-group checkbox-group">
            <input
              type="checkbox"
              id="sms-notifications"
              name="notifications.sms"
              checked={settings.notifications.sms}
              onChange={handleInputChange}
            />
            <label htmlFor="sms-notifications">SMS Notifications</label>
          </div>
        </div>
        
        <div className="form-actions">
          <button type="submit" className="save-button">Save Settings</button>
          <button type="button" className="reset-button" onClick={() => window.location.reload()}>
            Reset
          </button>
        </div>
      </form>
    </div>
  );
};

export default Settings; 
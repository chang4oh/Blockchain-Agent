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
    console.log('Saving settings:', settings);
    
    // Show saved message
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
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
          
          <div className="form-group">
            <label htmlFor="blockchain-api">Blockchain API Key</label>
            <input
              type="password"
              id="blockchain-api"
              name="apiKeys.blockchain"
              value={settings.apiKeys.blockchain}
              onChange={handleInputChange}
            />
            <p className="help-text">API key for blockchain data provider</p>
          </div>
          
          <div className="form-group">
            <label htmlFor="exchange-api">Exchange API Key</label>
            <input
              type="password"
              id="exchange-api"
              name="apiKeys.exchange"
              value={settings.apiKeys.exchange}
              onChange={handleInputChange}
            />
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
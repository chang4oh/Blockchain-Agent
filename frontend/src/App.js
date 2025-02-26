import React, { useState } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import Settings from './components/Settings';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  return (
    <div className="App">
      <nav className="app-nav">
        <div className="app-logo">
          <h1>Blockchain Agent</h1>
        </div>
        <ul className="nav-links">
          <li>
            <button 
              className={currentPage === 'dashboard' ? 'active' : ''} 
              onClick={() => setCurrentPage('dashboard')}
            >
              Dashboard
            </button>
          </li>
          <li>
            <button 
              className={currentPage === 'settings' ? 'active' : ''} 
              onClick={() => setCurrentPage('settings')}
            >
              Settings
            </button>
          </li>
        </ul>
      </nav>

      <main className="app-content">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'settings' && <Settings />}
      </main>

      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} Blockchain Agent. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;

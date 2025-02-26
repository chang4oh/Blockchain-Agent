import React, { useState, useEffect } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import Settings from './components/Settings';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  // Handle hash-based navigation
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash === 'settings') {
        setCurrentPage('settings');
      } else {
        setCurrentPage('dashboard');
      }
    };

    // Set initial page based on hash
    handleHashChange();

    // Listen for hash changes
    window.addEventListener('hashchange', handleHashChange);
    
    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);

  const navigateTo = (page) => {
    window.location.hash = page;
    setCurrentPage(page);
  };

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
              onClick={() => navigateTo('dashboard')}
            >
              Dashboard
            </button>
          </li>
          <li>
            <button 
              className={currentPage === 'settings' ? 'active' : ''} 
              onClick={() => navigateTo('settings')}
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

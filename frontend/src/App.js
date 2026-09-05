import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import TransactionForm from './components/TransactionForm';
import FraudCases from './components/FraudCases';
import ModelsPanel from './components/ModelsPanel';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [apiStats, setApiStats] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [transactions, setTransactions] = useState([]);
  
  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/fraud/stats`);
      setApiStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  }, []);

  const fetchHealth = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/health`);
      setHealthStatus(response.data);
    } catch (error) {
      console.error("Error fetching health:", error);
      setHealthStatus({ status: 'down' });
    }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchHealth();
    
    const statsInterval = setInterval(fetchStats, 15000);
    const healthInterval = setInterval(fetchHealth, 15000);
    
    return () => {
      clearInterval(statsInterval);
      clearInterval(healthInterval);
    };
  }, [fetchStats, fetchHealth]);

  const handleTransactionSubmit = (transaction) => {
    setTransactions((prev) => [transaction, ...prev].slice(0, 10));
    fetchStats();
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'Dashboard':
        return <Dashboard apiStats={apiStats} transactions={transactions} />;
      case 'Analyze Transaction':
        return <TransactionForm onSubmitSuccess={handleTransactionSubmit} />;
      case 'Fraud Cases':
        return <FraudCases />;
      case 'Models':
        return <ModelsPanel />;
      default:
        return <Dashboard apiStats={apiStats} transactions={transactions} />;
    }
  };

  return (
    <div className="App">
      <Header healthStatus={healthStatus} />
      <nav className="tab-navigation">
        {['Dashboard', 'Analyze Transaction', 'Fraud Cases', 'Models'].map(tab => (
          <button 
            key={tab}
            className={`tab-button ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;

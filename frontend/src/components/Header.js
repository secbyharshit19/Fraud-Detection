import React from 'react';
import './Header.css';

const Header = ({ healthStatus }) => {
  const isHealthy = healthStatus?.status === 'ok';

  return (
    <header className="app-header">
      <div className="header-title">
        <h1>Payment Processing & Fraud Detection Platform</h1>
      </div>
      <div className="header-info">
        {healthStatus && (
          <>
            <div className="info-badge">
              <span className="label">Models:</span>
              <span className="value">{healthStatus.model_count || 0}</span>
            </div>
            <div className="info-badge">
              <span className="label">Processed:</span>
              <span className="value">{healthStatus.transactions_processed?.toLocaleString() || 0}</span>
            </div>
          </>
        )}
        <div className={`status-indicator ${isHealthy ? 'healthy' : 'down'}`}>
          <div className="status-dot"></div>
          {isHealthy ? 'API Online' : 'API Offline'}
        </div>
      </div>
    </header>
  );
};

export default Header;

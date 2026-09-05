import React from 'react';
import './Dashboard.css';

const Dashboard = ({ apiStats, transactions }) => {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  };

  const getStatusColor = (decision) => {
    switch(decision) {
      case 'ALLOW':
      case 'APPROVED': return 'status-approved';
      case 'REVIEW': return 'status-review';
      case 'BLOCK':
      case 'BLOCKED': return 'status-blocked';
      default: return '';
    }
  };

  return (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Transactions</h3>
          <div className="stat-value">{apiStats?.total_transactions?.toLocaleString() || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Fraud Detected</h3>
          <div className="stat-value text-danger">{apiStats?.fraud_detected?.toLocaleString() || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Approval Rate</h3>
          <div className="stat-value text-success">
            {apiStats?.total_transactions 
              ? ((apiStats.approved / apiStats.total_transactions) * 100).toFixed(1)
              : 0}%
          </div>
        </div>
        <div className="stat-card">
          <h3>Avg Risk Score</h3>
          <div className="stat-value text-warning">{apiStats?.average_risk_score?.toFixed(1) || 0}</div>
        </div>
      </div>

      <div className="recent-transactions panel">
        <h2>Recent Transactions</h2>
        {transactions.length === 0 ? (
          <p className="no-data">No transactions analyzed yet.</p>
        ) : (
          <div className="table-responsive">
            <table className="transactions-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Amount</th>
                  <th>Category</th>
                  <th>Risk Score</th>
                  <th>Decision</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.transaction_id || Math.random()}>
                    <td className="tx-id">{tx.transaction_id?.substring(0,8) || 'N/A'}...</td>
                    <td>{formatCurrency(tx.amount || 0)}</td>
                    <td className="tx-category">{tx.merchant_category || 'unknown'}</td>
                    <td>
                      <div className="risk-bar-container">
                        <div 
                          className="risk-bar" 
                          style={{ width: `${tx.risk_score || 0}%`, backgroundColor: tx.risk_score > 70 ? 'var(--danger)' : tx.risk_score > 30 ? 'var(--warning)' : 'var(--success)' }}
                        ></div>
                        <span>{tx.risk_score || 0}/100</span>
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge ${getStatusColor(tx.decision)}`}>
                        {tx.decision || 'UNKNOWN'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

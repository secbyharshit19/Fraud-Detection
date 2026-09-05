import React, { useState } from 'react';
import axios from 'axios';
import './TransactionForm.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const CATEGORIES = ['grocery', 'gas_station', 'restaurant', 'electronics', 'entertainment', 'travel', 'healthcare', 'retail', 'jewelry', 'crypto_exchange', 'gaming'];
const PAYMENT_METHODS = ['credit_card', 'debit_card', 'digital_wallet', 'bank_transfer'];
const CHANNELS = ['online', 'in_store', 'mobile', 'phone'];
const COUNTRIES = ['US', 'UK', 'CA', 'DE', 'FR', 'BR', 'AU', 'IN', 'RU'];
const CARD_TYPES = ['visa', 'mastercard', 'amex', 'discover'];

const TransactionForm = ({ onSubmitSuccess }) => {
  const [formData, setFormData] = useState({
    transaction_id: '',
    customer_id: '',
    merchant_id: '',
    amount: '',
    currency: 'USD',
    timestamp: '',
    merchant_category: CATEGORIES[0],
    payment_method: PAYMENT_METHODS[0],
    channel: CHANNELS[0],
    country: COUNTRIES[0],
    card_type: CARD_TYPES[0],
    device_id: '',
    ip_address: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [predictionDetails, setPredictionDetails] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setPredictionDetails(null);

    const txRequest = {
      transaction_id: formData.transaction_id || undefined,
      customer_id: formData.customer_id,
      merchant_id: formData.merchant_id,
      amount: parseFloat(formData.amount),
      currency: formData.currency,
      timestamp: formData.timestamp ? new Date(formData.timestamp).toISOString() : undefined,
      merchant_category: formData.merchant_category,
      payment_method: formData.payment_method,
      channel: formData.channel,
      country: formData.country,
      card_type: formData.card_type,
      device_id: formData.device_id,
      ip_address: formData.ip_address
    };

    try {
      const response = await axios.post(`${API_URL}/payments`, txRequest);
      const data = response.data;
      setResult(data);
      onSubmitSuccess(data);
      
      try {
        const predRes = await axios.get(`${API_URL}/fraud/predictions/${data.transaction_id}`);
        setPredictionDetails(predRes.data);
      } catch (predErr) {
        console.warn("Prediction details fetch failed:", predErr);
      }

    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (decision) => {
    switch(decision) {
      case 'ALLOW':
      case 'APPROVED': return 'success';
      case 'REVIEW': return 'warning';
      case 'BLOCK':
      case 'BLOCKED': return 'danger';
      default: return '';
    }
  };

  return (
    <div className="transaction-form-container">
      <div className="form-panel panel">
        <h2>Simulate Transaction</h2>
        <form onSubmit={handleSubmit} className="tx-form">
          <div className="form-group">
            <label>Transaction ID (optional)</label>
            <input name="transaction_id" value={formData.transaction_id} onChange={handleChange} placeholder="TXN-HIGH-RISK-001" />
          </div>

          <div className="form-group">
            <label>Customer ID</label>
            <input name="customer_id" value={formData.customer_id} onChange={handleChange} placeholder="CUST-999" required />
          </div>

          <div className="form-group">
            <label>Merchant ID</label>
            <input name="merchant_id" value={formData.merchant_id} onChange={handleChange} placeholder="MERCH-CRYPTO-001" required />
          </div>

          <div className="form-group">
            <label>Amount (USD)</label>
            <input 
              type="number" 
              name="amount" 
              value={formData.amount} 
              onChange={handleChange} 
              min="0.01" 
              step="0.01" 
              required 
            />
          </div>

          <div className="form-group">
            <label>Currency</label>
            <input name="currency" value={formData.currency} onChange={handleChange} required />
          </div>

          <div className="form-group">
            <label>Timestamp (optional)</label>
            <input type="datetime-local" name="timestamp" value={formData.timestamp} onChange={handleChange} />
          </div>
          
          <div className="form-group">
            <label>Merchant Category</label>
            <select name="merchant_category" value={formData.merchant_category} onChange={handleChange}>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label>Payment Method</label>
            <select name="payment_method" value={formData.payment_method} onChange={handleChange}>
              {PAYMENT_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label>Channel</label>
            <select name="channel" value={formData.channel} onChange={handleChange}>
              {CHANNELS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label>Country</label>
            <select name="country" value={formData.country} onChange={handleChange}>
              {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label>Card Type</label>
            <select name="card_type" value={formData.card_type} onChange={handleChange}>
              {CARD_TYPES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label>Device ID</label>
            <input name="device_id" value={formData.device_id} onChange={handleChange} placeholder="DEV-UNKNOWN-001" required />
          </div>

          <div className="form-group">
            <label>IP Address</label>
            <input name="ip_address" value={formData.ip_address} onChange={handleChange} placeholder="185.220.101.1" required />
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Processing...' : 'Analyze Transaction'}
          </button>
          
          {error && <div className="error-msg">{error}</div>}
        </form>
      </div>

      {result && (
        <div className={`result-panel panel border-${getStatusColor(result.decision)}`}>
          <h2>Analysis Result</h2>
          <div className="result-grid">
            <div className="res-item">
              <span className="res-label">Transaction ID</span>
              <span className="res-value font-mono">{result.transaction_id}</span>
            </div>
            <div className="res-item">
              <span className="res-label">Decision</span>
              <span className={`status-badge status-${getStatusColor(result.decision).toLowerCase()}`}>
                {result.decision}
              </span>
            </div>
            <div className="res-item">
              <span className="res-label">Risk Score</span>
              <div className="gauge-container">
                <div className={`gauge-fill bg-${getStatusColor(result.decision)}`} style={{width: `${result.risk_score}%`}}></div>
              </div>
              <span className="res-value">{result.risk_score} / 100</span>
            </div>
          </div>

          {predictionDetails && predictionDetails.triggered_rules && predictionDetails.triggered_rules.length > 0 && (
            <div className="triggered-rules">
              <h3>Triggered Rules</h3>
              <ul>
                {predictionDetails.triggered_rules.map((rule, idx) => (
                  <li key={idx} className={`rule-item severity-${rule.severity?.toLowerCase() || 'medium'}`}>
                    <strong>{rule.name}</strong>: {rule.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TransactionForm;

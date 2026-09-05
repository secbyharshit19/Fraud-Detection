import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ModelsPanel.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ModelsPanel = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await axios.get(`${API_URL}/models`);
        setModels(res.data.models || []);
      } catch (err) {
        setError('Failed to fetch models');
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  return (
    <div className="models-panel panel">
      <h2>Active ML Models</h2>
      {loading ? (
        <p>Loading models...</p>
      ) : error ? (
        <p className="error-msg">{error}</p>
      ) : models.length === 0 ? (
        <p className="no-data">No models found.</p>
      ) : (
        <div className="models-grid">
          {models.map((model, idx) => (
            <div key={idx} className="model-card">
              <div className="model-header">
                <h3>{model.name}</h3>
                <span className={`status-badge status-${model.status?.toLowerCase() === 'active' ? 'approved' : 'review'}`}>
                  {model.status || 'UNKNOWN'}
                </span>
              </div>
              <div className="model-details">
                <div className="detail-item">
                  <span className="label">Version:</span>
                  <span className="value">{model.version}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Type:</span>
                  <span className="value">{model.type}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ModelsPanel;

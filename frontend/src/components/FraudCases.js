import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './FraudCases.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const FraudCases = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedCase, setExpandedCase] = useState(null);
  const [feedbackLabel, setFeedbackLabel] = useState('FRAUD');
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const fetchCases = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/fraud/cases`);
      setCases(res.data.cases || []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch fraud cases');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCases();
    const interval = setInterval(fetchCases, 30000);
    return () => clearInterval(interval);
  }, [fetchCases]);

  const handleUpdateStatus = async (caseId, status) => {
    try {
      await axios.patch(`${API_URL}/fraud/cases/${caseId}?status=${status}&analyst_id=ANALYST-WEB`);
      fetchCases();
    } catch (err) {
      alert('Failed to update case status');
    }
  };

  const handleFeedbackSubmit = async (caseId, e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/fraud/cases/${caseId}/feedback`, {
        label: feedbackLabel,
        analyst_id: 'ANALYST-WEB',
        notes: feedbackNotes
      });
      alert('Feedback submitted successfully');
      setFeedbackNotes('');
    } catch (err) {
      alert('Failed to submit feedback');
    }
  };

  const toggleExpand = (caseId) => {
    if (expandedCase === caseId) setExpandedCase(null);
    else setExpandedCase(caseId);
  };

  const filteredCases = statusFilter === 'ALL' ? cases : cases.filter(c => c.status === statusFilter);

  return (
    <div className="fraud-cases panel">
      <div className="cases-header">
        <h2>Fraud Cases Management</h2>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="ALL">All Statuses</option>
          <option value="UNDER_REVIEW">Under Review</option>
          <option value="APPROVED">Approved</option>
          <option value="BLOCKED">Blocked</option>
          <option value="ESCALATED">Escalated</option>
          <option value="RESOLVED">Resolved</option>
        </select>
      </div>

      {loading ? (
        <p>Loading cases...</p>
      ) : error ? (
        <p className="error-msg">{error}</p>
      ) : cases.length === 0 ? (
        <p className="no-data">No fraud cases found.</p>
      ) : (
        <div className="table-responsive">
          <table className="cases-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Transaction ID</th>
                <th>Risk Score</th>
                <th>Decision</th>
                <th>Status</th>
                <th>Created At</th>
              </tr>
            </thead>
            <tbody>
              {filteredCases.map(c => (
                <React.Fragment key={c.case_id}>
                  <tr className={`case-row ${expandedCase === c.case_id ? 'expanded-row-active' : ''}`} onClick={() => toggleExpand(c.case_id)}>
                    <td className="font-mono text-sm">{c.case_id.substring(0,8)}...</td>
                    <td className="font-mono text-sm">{c.transaction_id.substring(0,8)}...</td>
                    <td><span className={`risk-badge risk-${c.risk_score > 70 ? 'high' : c.risk_score > 30 ? 'medium' : 'low'}`}>{c.risk_score}</span></td>
                    <td>{c.decision}</td>
                    <td><span className={`status-badge status-${c.status?.toLowerCase()}`}>{c.status}</span></td>
                    <td>{new Date(c.created_at).toLocaleString()}</td>
                  </tr>
                  {expandedCase === c.case_id && (
                    <tr className="expanded-content">
                      <td colSpan="6">
                        <div className="expanded-details">
                          <div className="details-col">
                            <h4>Explanation</h4>
                            <p>{c.explanation || 'No explanation provided.'}</p>
                            
                            <h4>Triggered Rules</h4>
                            <ul className="rules-list">
                              {c.triggered_rules && c.triggered_rules.length > 0 ? (
                                c.triggered_rules.map((r, i) => <li key={i}>{r.name}</li>)
                              ) : (
                                <li>No rules triggered.</li>
                              )}
                            </ul>
                            
                            <div className="action-buttons">
                              <button className="btn btn-approve" onClick={() => handleUpdateStatus(c.case_id, 'APPROVED')}>Approve</button>
                              <button className="btn btn-block" onClick={() => handleUpdateStatus(c.case_id, 'BLOCKED')}>Block</button>
                              <button className="btn btn-escalate" onClick={() => handleUpdateStatus(c.case_id, 'ESCALATED')}>Escalate</button>
                            </div>
                          </div>
                          
                          <div className="details-col feedback-section">
                            <h4>Submit Feedback</h4>
                            <form onSubmit={(e) => handleFeedbackSubmit(c.case_id, e)}>
                              <select value={feedbackLabel} onChange={e => setFeedbackLabel(e.target.value)} required>
                                <option value="FRAUD">Fraud</option>
                                <option value="LEGITIMATE">Legitimate</option>
                                <option value="UNCERTAIN">Uncertain</option>
                              </select>
                              <textarea 
                                value={feedbackNotes} 
                                onChange={e => setFeedbackNotes(e.target.value)} 
                                placeholder="Analyst notes..." 
                                rows="3"
                                required
                              />
                              <button type="submit" className="btn btn-submit-feedback">Submit Feedback</button>
                            </form>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default FraudCases;

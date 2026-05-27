import React, { useState } from 'react';
import { UploadCloud, CheckCircle } from 'lucide-react';
import api from '../api';

const DataCollection = ({ onNext }) => {
  const [formData, setFormData] = useState({ name: '', address: '', emergency: '' });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const data = new FormData();
      data.append('full_name', formData.name);
      data.append('address', formData.address);
      data.append('emergency_contact', formData.emergency);
      if (file) {
        data.append('document', file);
      }

      await api.post('/data/submit', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setSubmitted(true);
      setTimeout(() => onNext(), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Submission failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
        <CheckCircle size={64} color="#10b981" />
        <h2 style={{ fontSize: '1.5rem' }}>Details Submitted!</h2>
        <p style={{ color: 'var(--text-muted)' }}>Your documents are under HR review. Please wait for approval.</p>
      </div>
    );
  }

  return (
    <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Data Collection</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>Please provide your details for HR compliance.</p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="form-group">
          <label>Full Name</label>
          <input
            type="text"
            className="form-control"
            value={formData.name}
            onChange={e => setFormData({ ...formData, name: e.target.value })}
            placeholder="As per ID"
          />
        </div>
        <div className="form-group">
          <label>Emergency Contact</label>
          <input
            type="text"
            className="form-control"
            value={formData.emergency}
            onChange={e => setFormData({ ...formData, emergency: e.target.value })}
            placeholder="+91 00000 00000"
          />
        </div>
        <div className="form-group" style={{ gridColumn: 'span 2' }}>
          <label>Residential Address</label>
          <input
            type="text"
            className="form-control"
            value={formData.address}
            onChange={e => setFormData({ ...formData, address: e.target.value })}
            placeholder="Full address"
          />
        </div>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
          Upload ID Document
        </label>
        <label style={{ border: '2px dashed var(--border)', borderRadius: '0.5rem', padding: '3rem 2rem', textAlign: 'center', background: 'rgba(255,255,255,0.02)', cursor: 'pointer', display: 'block' }}>
          <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={handleFileChange} style={{ display: 'none' }} />
          <UploadCloud size={48} color="var(--primary-color)" style={{ margin: '0 auto 1rem', opacity: 0.8 }} />
          {file ? (
            <p style={{ fontWeight: '500', color: '#10b981' }}>✓ {file.name}</p>
          ) : (
            <>
              <p style={{ fontWeight: '500', marginBottom: '0.25rem' }}>Click to select a file</p>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>PDF, JPG, PNG up to 10MB</p>
            </>
          )}
        </label>
      </div>

      {error && (
        <div style={{ color: '#ef4444', fontSize: '0.85rem', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'flex-end' }}>
        <button
          className="btn"
          style={{ width: 'auto' }}
          onClick={handleSubmit}
          disabled={!formData.name || !formData.address || !formData.emergency || loading}
        >
          {loading ? 'Submitting...' : 'Submit Details ➔'}
        </button>
      </div>
    </div>
  );
};

export default DataCollection;
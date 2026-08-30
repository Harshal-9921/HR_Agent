import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../api';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) { setStatus('error'); setMessage('Missing verification token.'); return; }
    api.post(`/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(res => { setStatus('success'); setMessage(res.data.message); })
      .catch(err => { setStatus('error'); setMessage(err.response?.data?.detail || 'Verification failed.'); });
  }, [searchParams]);

  return (
    <div className="auth-container">
      <div className="auth-card" style={{ maxWidth: '420px', textAlign: 'center' }}>
        {status === 'verifying' && <p>Verifying your email...</p>}
        {status === 'success' && (
          <>
            <h1 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>✅ Verified!</h1>
            <p>{message}</p>
            <p style={{ marginTop: '1.5rem' }}><Link to="/login">Back to Login</Link></p>
          </>
        )}
        {status === 'error' && (
          <>
            <h1 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#ef4444' }}>Verification Failed</h1>
            <p>{message}</p>
          </>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
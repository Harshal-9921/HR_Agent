import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, Settings, LogOut, Mail,
  ChevronDown, ChevronUp, CheckCircle, XCircle, Clock, Activity
} from 'lucide-react';
import api from '../api';

const EmployeesPage = () => {
  const [employees, setEmployees] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [emailLogs, setEmailLogs] = useState({});
const [loadingEmail, setLoadingEmail] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const res = await api.get('/employees/with-progress');
      setEmployees(res.data);
    } catch (err) {
      console.error(err);
    }
  };
const [showAlertModal, setShowAlertModal] = useState(false);
const [alertEmp, setAlertEmp] = useState(null);
const [alertContent, setAlertContent] = useState({ subject: '', html_body: '' });
const [alertMsg, setAlertMsg] = useState('');
const [loadingAlert, setLoadingAlert] = useState(false);

const openAlertModal = async (emp) => {
  setAlertEmp(emp);
  setShowAlertModal(true);
  setAlertMsg('');
  setLoadingAlert(true);
  try {
    const res = await api.get(`/employees/${emp.id}/alert-preview`);
    setAlertContent({ subject: res.data.subject, html_body: res.data.html_body });
  } catch (err) {
    setAlertMsg('Failed to load preview: ' + (err.response?.data?.detail || err.message));
  } finally {
    setLoadingAlert(false);
  }
};

const sendAlert = async () => {
  try {
    await api.post(`/employees/${alertEmp.id}/send-alert`, alertContent);
    setAlertMsg('Alert email sent!');
    setTimeout(() => { setShowAlertModal(false); setAlertMsg(''); }, 1500);
  } catch (err) {
    setAlertMsg('Failed to send: ' + (err.response?.data?.detail || err.message));
  }
};
  const fetchReport = async (empId) => {
    if (selectedReport === empId) {
      setSelectedReport(null);
      setReportData(null);
      return;
    }
    setSelectedReport(empId);
    setLoadingReport(true);
    fetchEmailLogs(empId); 
    try {
      const res = await api.get(`/employees/${empId}/report`);
      setReportData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingReport(false);
    }
  };
  const fetchEmailLogs = async (empId) => {
    setLoadingEmail(prev => ({ ...prev, [empId]: true }));
    try {
      const res = await api.get(`/employees/${empId}/email-logs`);
      setEmailLogs(prev => ({ ...prev, [empId]: res.data }));
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingEmail(prev => ({ ...prev, [empId]: false }));
    }
  };

  const getRatingColor = (rating) => {
    if (rating === 'Excellent') return '#22c55e';
    if (rating === 'Good') return '#3b82f6';
    if (rating === 'Needs Improvement') return '#f59e0b';
    return '#ef4444';
  };

  const formatTime = (seconds) => {
    if (!seconds) return 'N/A';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };
  const downloadCSV = async (url, filename) => {
  try {
    const res = await api.get(url, { responseType: 'blob' });
    const blob = new Blob([res.data], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(link.href);
  } catch (err) {
    alert('Download failed: ' + (err.response?.data?.detail || err.message));
  }
};

return (
  <>
    <div className="dashboard-layout">
      {/* Sidebar */}
      <div className="sidebar" style={{ width: '260px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2.5rem' }}>
          <div style={{ background: 'var(--primary-color)', padding: '0.5rem', borderRadius: '0.5rem' }}>
            <span style={{ fontSize: '1.25rem' }}>🚀</span>
          </div>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '700' }}>HR Portal</h2>
            <p style={{ fontSize: '0.65rem', letterSpacing: '0.1em', color: 'var(--text-muted)' }}>ONBOARDING SYSTEM</p>
          </div>
        </div>

        <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <button className="nav-item" onClick={() => navigate('/hr-dashboard')}>
            <LayoutDashboard size={20} /> HR Dashboard
          </button>
          <button className="nav-item active">
            <Users size={20} /> Employees
          </button>
          <button className="nav-item" onClick={() => navigate('/manage-content')}>
            <Settings size={20} /> Manage Content
          </button>
          <button className="nav-item" onClick={() => navigate('/activity-logs')}>
  <Activity size={20} /> Activity Logs
</button>
        </nav>

        <button onClick={() => { localStorage.removeItem('token'); navigate('/login'); }}
          className="nav-item" style={{ marginTop: 'auto', color: '#ef4444' }}>
          <LogOut size={20} /> Sign Out
        </button>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <header style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
  <div>
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <Users size={24} color="var(--primary-color)" />
      <h1 style={{ fontSize: '1.75rem', fontWeight: '700' }}>Employees</h1>
    </div>
    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
      Click on an employee to view their detailed onboarding report
    </p>
  </div>
  <button
    className="btn"
    style={{ width: 'auto' }}
    onClick={() => downloadCSV('/employees/reports/csv/all', 'all_employee_reports.csv')}
  >
    Download All Reports (CSV)
  </button>
</header>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {employees.map((emp) => {
            const isOpen = selectedReport === emp.id;
            const statusColor = emp.completion_pct === 100 ? '#22c55e' : emp.completion_pct > 0 ? '#3b82f6' : '#f59e0b';

            return (
              <div key={emp.id} className="card" style={{ padding: '0', overflow: 'hidden' }}>
                {/* Employee Row */}
                <div
                  onClick={() => fetchReport(emp.id)}
                  style={{
                    padding: '1.25rem 1.5rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    borderBottom: isOpen ? '1px solid var(--border)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                      width: '42px', height: '42px', borderRadius: '50%',
                      background: 'var(--primary-color)', display: 'flex',
                      alignItems: 'center', justifyContent: 'center',
                      fontWeight: '700', fontSize: '1.1rem', color: 'white'
                    }}>
                      {emp.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p style={{ fontWeight: '600', fontSize: '0.95rem' }}>{emp.name}</p>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{emp.email} · {emp.department || 'N/A'}</p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                    <div style={{ textAlign: 'center' }}>
                      <p style={{ fontSize: '1.2rem', fontWeight: '700', color: statusColor }}>{emp.completion_pct}%</p>
                      <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>COMPLETION</p>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <p style={{ fontSize: '1.2rem', fontWeight: '700' }}>{emp.modules_completed}/{emp.total_modules}</p>
                      <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>MODULES</p>
                    </div>
                    {isOpen ? <ChevronUp size={20} color="var(--text-muted)" /> : <ChevronDown size={20} color="var(--text-muted)" />}
                  </div>
                </div>

                {/* Report Dropdown */}
                {isOpen && (
                  <div style={{ padding: '1.5rem' }}>
                    {loadingReport ? (
                      <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>Loading report...</p>
                    ) : reportData ? (
                      <>
                        {/* Summary Cards */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '0.75rem', textAlign: 'center' }}>
                            <p style={{ fontSize: '1.5rem', fontWeight: '700', color: getRatingColor(reportData.summary.rating) }}>
                              {reportData.summary.overall_score_pct}%
                            </p>
                            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>OVERALL SCORE</p>
                          </div>
                          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '0.75rem', textAlign: 'center' }}>
                            <p style={{ fontSize: '1.5rem', fontWeight: '700', color: getRatingColor(reportData.summary.rating) }}>
                              {reportData.summary.rating}
                            </p>
                            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>RATING</p>
                          </div>
                          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '0.75rem', textAlign: 'center' }}>
                            <p style={{ fontSize: '1.5rem', fontWeight: '700' }}>
                              {reportData.summary.completed_modules}/{reportData.summary.total_modules}
                            </p>
                            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>MODULES DONE</p>
                          </div>
                          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '0.75rem', textAlign: 'center' }}>
                            <p style={{ fontSize: '1rem', fontWeight: '700' }}>
                              {reportData.summary.completion_date
                                ? new Date(reportData.summary.completion_date).toLocaleDateString()
                                : 'In Progress'}
                            </p>
                            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>COMPLETED ON</p>
                          </div>
                        </div>

                        {/* Download button — OUTSIDE table */}
                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem', gap: '0.75rem' }}>
  <button
    className="btn"
    style={{ width: 'auto', fontSize: '0.8rem', padding: '0.4rem 0.9rem', background: 'rgba(245,158,11,0.15)', border: '1px solid #f59e0b', color: '#f59e0b' }}
    onClick={() => openAlertModal(emp)}
  >
    Send Alert
  </button>
  <button
    className="btn"
    style={{ width: 'auto', fontSize: '0.8rem', padding: '0.4rem 0.9rem' }}
    onClick={() => downloadCSV(`/employees/${emp.id}/report/csv`, `report_${emp.name.replace(/\s+/g, '_')}.csv`)}
  >
    Download Report (CSV)
  </button>
</div>
{showAlertModal && (
  <div className="modal-overlay">
    <div className="auth-card" style={{ maxWidth: '600px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>Send Alert to {alertEmp?.name}</h2>
        <button onClick={() => setShowAlertModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
      </div>
      {loadingAlert ? (
        <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>Loading...</p>
      ) : (
        <>
          <div className="form-group">
            <label>Subject</label>
            <input type="text" className="form-control" value={alertContent.subject}
              onChange={e => setAlertContent({ ...alertContent, subject: e.target.value })} />
          </div>
          <div className="form-group">
            <label>Message</label>
            <textarea className="form-control" rows={10} style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}
              value={alertContent.html_body}
              onChange={e => setAlertContent({ ...alertContent, html_body: e.target.value })} />
          </div>
          {alertMsg && <p style={{ fontSize: '0.85rem', color: alertMsg.includes('sent') ? '#22c55e' : '#ef4444', marginBottom: '1rem' }}>{alertMsg}</p>}
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button type="button" className="btn" style={{ background: 'transparent', border: '1px solid var(--border)' }}
              onClick={() => { const win = window.open('', '_blank'); win.document.write(alertContent.html_body); win.document.close(); }}>
              Preview
            </button>
            <button className="btn" onClick={sendAlert}>Send Email</button>
          </div>
        </>
      )}
    </div>
  </div>
)}
                        

                        {/* Module Table */}
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                          <thead>
                            <tr style={{ borderBottom: '1px solid var(--border)' }}>
                              <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontWeight: '600', fontSize: '0.72rem', textTransform: 'uppercase' }}>Module</th>
                              <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontWeight: '600', fontSize: '0.72rem', textTransform: 'uppercase' }}>Quiz Score</th>
                              <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontWeight: '600', fontSize: '0.72rem', textTransform: 'uppercase' }}>Attempts</th>
                              <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontWeight: '600', fontSize: '0.72rem', textTransform: 'uppercase' }}>Module Score</th>
                              <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontWeight: '600', fontSize: '0.72rem', textTransform: 'uppercase' }}>Status</th>
                              <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontWeight: '600', fontSize: '0.72rem', textTransform: 'uppercase' }}>Completed On</th>
                            </tr>
                          </thead>
                          <tbody>
                            {reportData.modules.map((mod, idx) => (
                              <tr key={idx} style={{ borderBottom: '1px solid var(--border)' }}>
                                <td style={{ padding: '0.75rem' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    {mod.is_intro && <span style={{ fontSize: '0.65rem', background: 'rgba(245,158,11,0.15)', color: '#f59e0b', padding: '0.1rem 0.4rem', borderRadius: '0.3rem' }}>INTRO</span>}
                                    {mod.module_title}
                                  </div>
                                </td>
                                <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                                  {mod.total_questions > 0 ? `${mod.score}/${mod.total_questions}` : 'N/A'}
                                </td>
                                <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                                  {mod.completed ? (
                                    <span style={{ color: mod.attempt_count > 1 ? '#f59e0b' : '#22c55e' }}>
                                      {mod.attempt_count} {mod.attempt_count > 1 ? '(-25%)' : '✓'}
                                    </span>
                                  ) : '-'}
                                </td>
                                <td style={{ padding: '0.75rem', textAlign: 'center', fontWeight: '600', color: mod.module_score_pct >= 75 ? '#22c55e' : '#ef4444' }}>
                                  {mod.completed ? `${mod.module_score_pct}%` : '-'}
                                </td>
                                <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                                  {mod.completed
                                    ? <CheckCircle size={18} color="#22c55e" />
                                    : <XCircle size={18} color="#ef4444" />}
                                </td>
                                <td style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                                  {mod.completed_at ? new Date(mod.completed_at).toLocaleDateString() : '-'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {/* Email Delivery Status */}
<div style={{ marginTop: '1.5rem' }}>
  <h4 style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
    <Mail size={16} color="var(--primary-color)" /> Email Delivery Status
  </h4>
  {loadingEmail[emp.id] ? (
    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Loading email logs...</p>
  ) : emailLogs[emp.id] && emailLogs[emp.id].length > 0 ? (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
      <thead>
        <tr style={{ borderBottom: '1px solid var(--border)' }}>
          {['Email Type', 'Status', 'Sent At', 'Retries'].map(h => (
            <th key={h} style={{ padding: '0.6rem 0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontWeight: '600', fontSize: '0.7rem', textTransform: 'uppercase' }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {emailLogs[emp.id].map((log) => (
          <tr key={log.id} style={{ borderBottom: '1px solid var(--border)' }}>
            <td style={{ padding: '0.6rem 0.75rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Mail size={13} color="var(--primary-color)" />
                {log.email_type}
              </span>
            </td>
            <td style={{ padding: '0.6rem 0.75rem' }}>
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                padding: '0.2rem 0.6rem', borderRadius: '1rem', fontSize: '0.72rem', fontWeight: '600',
                background: log.status === 'sent' ? 'rgba(34,197,94,0.1)' : log.status === 'failed' ? 'rgba(239,68,68,0.1)' : 'rgba(245,158,11,0.1)',
                color: log.status === 'sent' ? '#22c55e' : log.status === 'failed' ? '#ef4444' : '#f59e0b',
              }}>
                {log.status === 'sent' ? <CheckCircle size={11} /> : log.status === 'failed' ? <XCircle size={11} /> : <Clock size={11} />}
                {log.status?.toUpperCase()}
              </span>
            </td>
            <td style={{ padding: '0.6rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
              {log.sent_at ? new Date(log.sent_at).toLocaleString() : '-'}
            </td>
            <td style={{ padding: '0.6rem 0.75rem', textAlign: 'center', color: log.retry_count > 0 ? '#f59e0b' : 'var(--text-muted)' }}>
              {log.retry_count || 0}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  ) : (
    <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', padding: '0.75rem', background: 'rgba(255,255,255,0.02)', borderRadius: '0.5rem', textAlign: 'center' }}>
      No emails sent to this employee yet.
    </p>
  )}
</div>
                      </>
                    ) : null}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>

    <style>{`
      .nav-item {
        display: flex; align-items: center; gap: 0.75rem; width: 100%;
        padding: 0.85rem 1rem; background: transparent; border: none;
        color: var(--text-muted); font-weight: 500; font-size: 0.95rem;
        border-radius: 0.75rem; cursor: pointer; transition: all 0.2s; text-align: left;
      }
      .nav-item:hover { background: rgba(255,255,255,0.05); color: var(--text-main); }
      .nav-item.active { background: var(--surface-card); color: var(--primary-color); border: 1px solid var(--border); }
    `}</style>
  </>
);
};

export default EmployeesPage;
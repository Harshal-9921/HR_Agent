import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, Settings, LogOut,
  BarChart3, UserPlus, Clock, AlertCircle, Eye, Activity, Edit2
} from 'lucide-react';
import api from '../api';

const HRDashboard = () => {
  const [employees, setEmployees] = useState([]);
  const [stats, setStats] = useState({ total: 0, completed: 0, inProgress: 0, notStarted: 0, avgPct: 0 });
  const [showAddModal, setShowAddModal] = useState(false);
  const [newEmployee, setNewEmployee] = useState({ name: '', email: '', personal_email: '', department: '', doj: '', role: 'full_time' });
  const [addMsg, setAddMsg] = useState('');
 const [showChangePassword, setShowChangePassword] = useState(false);
const [passwordData, setPasswordData] = useState({ newPass: '', confirm: '' });
const [passwordMsg, setPasswordMsg] = useState('');
const [showEmailSettings, setShowEmailSettings] = useState(false);
const [emailSettings, setEmailSettings] = useState({
  sender_name: '', sender_email: '', smtp_server: 'smtp.gmail.com',
  smtp_port: 587, smtp_user: '', smtp_password: ''
});
const [emailSettingsMsg, setEmailSettingsMsg] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [showEmailSettings, setShowEmailSettings] = useState(false);
  const [emailSettings, setEmailSettings] = useState({
    sender_name: '', sender_email: '', smtp_server: 'smtp.gmail.com',
    smtp_port: 587, smtp_user: '', smtp_password: ''
  });
  const [emailSettingsMsg, setEmailSettingsMsg] = useState('');
  const [editMsg, setEditMsg] = useState('');
  const navigate = useNavigate();

  const fetchData = async (includeArchived = false) => {
    try {
      const res = await api.get(`/employees/with-progress${includeArchived ? '?include_archived=true' : ''}`);
      const data = res.data;
      setEmployees(data);
      const total = data.length;
      const completed = data.filter(e => e.completion_pct === 100).length;
      const inProgress = data.filter(e => e.completion_pct > 0 && e.completion_pct < 100).length;
      const notStarted = data.filter(e => e.completion_pct === 0).length;
      const avgPct = total > 0 ? Math.round(data.reduce((sum, e) => sum + e.completion_pct, 0) / total) : 0;
      setStats({ total, completed, inProgress, notStarted, avgPct });
    } catch (err) {
      console.error('Failed to fetch employees:', err);
    }
  };

  useEffect(() => {
    fetchData(showArchived);
  }, [showArchived]);

  const loadEmailSettings = async () => {
    try {
      const res = await api.get('/settings/email');
      setEmailSettings(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handlePreview = async () => {
    try {
      const res = await api.get('/auth/preview-token');
      localStorage.setItem('hr_token', localStorage.getItem('token'));
      localStorage.setItem('token', res.data.preview_token);
      localStorage.setItem('is_preview', 'true');
      navigate('/onboarding');
    } catch (err) {
      alert('Failed to load preview: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    try {
      await api.post('/employees/', newEmployee);
      setAddMsg('Employee added successfully!');
      setNewEmployee({ name: '', email: '', personal_email: '', department: '', doj: '', role: 'full_time' });
      setTimeout(() => { setShowAddModal(false); setAddMsg(''); fetchData(); }, 1500);
    } catch (err) {
      setAddMsg(err.response?.data?.detail || 'Failed to add employee.');
    }
  };

  const getStatusBadge = (pct) => {
    if (pct === 100) return { label: 'Completed', color: '#22c55e', bg: 'rgba(34,197,94,0.1)' };
    if (pct > 0) return { label: 'In Progress', color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' };
    return { label: 'Not Started', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' };
  };

  return (
    <div className="dashboard-layout">

      {/* ── Change Password Modal ── */}
      {showChangePassword && (
        <div className="modal-overlay">
          <div className="auth-card" style={{ maxWidth: '400px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2>Change Password</h2>
              <button onClick={() => { setShowChangePassword(false); setPasswordMsg(''); }} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault();
              if (passwordData.newPass !== passwordData.confirm) { setPasswordMsg('Passwords do not match.'); return; }
              if (passwordData.newPass.length < 6) { setPasswordMsg('Password must be at least 6 characters.'); return; }
              try {
                await api.post('/auth/change-password', { new_password: passwordData.newPass });
                setPasswordMsg('Password changed successfully!');
                setPasswordData({ newPass: '', confirm: '' });
                setTimeout(() => { setShowChangePassword(false); setPasswordMsg(''); }, 1500);
              } catch (err) {
                setPasswordMsg(err.response?.data?.detail || 'Failed to change password.');
              }
            }}>
              <div className="form-group">
                <label>New Password</label>
                <input id="hr-new-pass" type="password" className="form-control" value={passwordData.newPass} onChange={e => setPasswordData({...passwordData, newPass: e.target.value})} placeholder="Enter new password"
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); document.getElementById('hr-confirm-pass').focus(); }}} />
              </div>
              <div className="form-group">
                <label>Confirm New Password</label>
                <input id="hr-confirm-pass" type="password" className="form-control" value={passwordData.confirm} onChange={e => setPasswordData({...passwordData, confirm: e.target.value})} placeholder="Confirm new password" />
              </div>
              {passwordMsg && <p style={{ fontSize: '0.85rem', color: passwordMsg.includes('success') ? '#22c55e' : '#ef4444', marginBottom: '1rem' }}>{passwordMsg}</p>}
              <button type="submit" className="btn">Change Password</button>
            </form>
          </div>
        </div>
      )}

      {/* ── Add Employee Modal ── */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="auth-card" style={{ maxWidth: '480px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2>Add New Employee</h2>
              <button onClick={() => { setShowAddModal(false); setAddMsg(''); }} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
            </div>
            <form onSubmit={handleAddEmployee}>
              <div className="form-group">
                <label>Full Name</label>
                <input type="text" className="form-control" required value={newEmployee.name} onChange={e => setNewEmployee({...newEmployee, name: e.target.value})} placeholder="John Doe" />
              </div>
              <div className="form-group">
                <label>Company Email</label>
                <input type="email" className="form-control" required value={newEmployee.email} onChange={e => setNewEmployee({...newEmployee, email: e.target.value})} placeholder="john.doe@accops.com" />
              </div>
              <div className="form-group">
                <label>Personal Email</label>
                <input type="email" className="form-control" required value={newEmployee.personal_email} onChange={e => setNewEmployee({...newEmployee, personal_email: e.target.value})} placeholder="john.doe@gmail.com" />
              </div>
              <div className="form-group">
                <label>Department</label>
                <select className="form-control" required value={newEmployee.department} onChange={e => setNewEmployee({...newEmployee, department: e.target.value})}>
                  <option value="">Select Department</option>
                  <option value="Engineering">Engineering</option>
                  <option value="Sales">Sales</option>
                  <option value="Pre-sales">Pre-sales</option>
                  <option value="Marketing">Marketing</option>
                  <option value="Product Management">Product Management</option>
                  <option value="HR">HR</option>
                  <option value="IT">IT</option>
                  <option value="Administration">Administration</option>
                  <option value="Finance and Accounts">Finance and Accounts</option>
                  <option value="Customer Success">Customer Success</option>
                </select>
              </div>
              <div className="form-group">
                <label>Date of Joining</label>
                <input type="date" className="form-control" required value={newEmployee.doj} onChange={e => setNewEmployee({...newEmployee, doj: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select className="form-control" value={newEmployee.role} onChange={e => setNewEmployee({...newEmployee, role: e.target.value})}>
                  <option value="full_time">Full Time</option>
                  <option value="intern">Intern</option>
                  <option value="consultant">Consultant</option>
                </select>
              </div>
              {addMsg && <p style={{ fontSize: '0.85rem', color: addMsg.includes('success') ? '#22c55e' : '#ef4444', marginBottom: '1rem' }}>{addMsg}</p>}
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="button" className="btn" style={{ background: 'transparent', border: '1px solid var(--border)' }} onClick={() => { setShowAddModal(false); setAddMsg(''); }}>Cancel</button>
                <button type="submit" className="btn">Add Employee</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingEmployee && (
  <div className="modal-overlay">
    <div className="auth-card" style={{ maxWidth: '480px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>Edit Employee</h2>
        <button onClick={() => { setEditingEmployee(null); setEditMsg(''); }} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
      </div>
      <form onSubmit={async (e) => {
        e.preventDefault();
        try {
          await api.put(`/employees/${editingEmployee.id}`, {
            name: editingEmployee.name,
            personal_email: editingEmployee.personal_email,
            department: editingEmployee.department,
            doj: editingEmployee.doj,
            role: editingEmployee.role,
          });
          setEditMsg('Employee updated successfully!');
          setTimeout(() => { setEditingEmployee(null); setEditMsg(''); fetchData(showArchived); }, 1500);
        } catch (err) {
          setEditMsg(err.response?.data?.detail || 'Failed to update employee.');
        }
      }}>
        <div className="form-group">
          <label>Full Name</label>
          <input type="text" className="form-control" value={editingEmployee.name} onChange={e => setEditingEmployee({...editingEmployee, name: e.target.value})} />
        </div>
        <div className="form-group">
          <label>Personal Email</label>
          <input type="email" className="form-control" value={editingEmployee.personal_email || ''} onChange={e => setEditingEmployee({...editingEmployee, personal_email: e.target.value})} placeholder="personal@gmail.com" />
        </div>
        <div className="form-group">
          <label>Department</label>
          <select className="form-control" value={editingEmployee.department || ''} onChange={e => setEditingEmployee({...editingEmployee, department: e.target.value})}>
            <option value="">Select Department</option>
            <option value="Engineering">Engineering</option>
            <option value="Sales">Sales</option>
            <option value="Pre-sales">Pre-sales</option>
            <option value="Marketing">Marketing</option>
            <option value="Product Management">Product Management</option>
            <option value="HR">HR</option>
            <option value="IT">IT</option>
            <option value="Administration">Administration</option>
            <option value="Finance and Accounts">Finance and Accounts</option>
            <option value="Customer Success">Customer Success</option>
          </select>
        </div>
        <div className="form-group">
          <label>Date of Joining</label>
          <input type="date" className="form-control" value={editingEmployee.doj || ''} onChange={e => setEditingEmployee({...editingEmployee, doj: e.target.value})} />
        </div>
        <div className="form-group">
          <label>Role</label>
          <select className="form-control" value={editingEmployee.role || 'full_time'} onChange={e => setEditingEmployee({...editingEmployee, role: e.target.value})}>
            <option value="full_time">Full Time</option>
            <option value="intern">Intern</option>
            <option value="consultant">Consultant</option>
          </select>
        </div>
        {editMsg && <p style={{ fontSize: '0.85rem', color: editMsg.includes('success') ? '#22c55e' : '#ef4444', marginBottom: '1rem' }}>{editMsg}</p>}
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button type="button" className="btn" style={{ background: 'transparent', border: '1px solid var(--border)' }} onClick={() => { setEditingEmployee(null); setEditMsg(''); }}>Cancel</button>
          <button type="submit" className="btn">Save Changes</button>
        </div>
      </form>
    </div>
  </div>
)}
{/* ── Email Settings Modal ── */}
      {showEmailSettings && (
        <div className="modal-overlay">
          <div className="auth-card" style={{ maxWidth: '500px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2>Email Settings</h2>
              <button onClick={() => { setShowEmailSettings(false); setEmailSettingsMsg(''); }}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api.put('/settings/email', emailSettings);
                setEmailSettingsMsg('Settings saved successfully!');
              } catch (err) {
                setEmailSettingsMsg('Failed to save settings.');
              }
            }}>
              <div className="form-group">
                <label>Sender Name</label>
                <input type="text" className="form-control" value={emailSettings.sender_name || ''} onChange={e => setEmailSettings({...emailSettings, sender_name: e.target.value})} placeholder="Accops HR Onboarding" />
              </div>
              <div className="form-group">
                <label>Sender Email</label>
                <input type="email" className="form-control" value={emailSettings.sender_email || ''} onChange={e => setEmailSettings({...emailSettings, sender_email: e.target.value})} placeholder="onboarding@accops.com" />
              </div>
              <div className="form-group">
                <label>SMTP Server</label>
                <input type="text" className="form-control" value={emailSettings.smtp_server || ''} onChange={e => setEmailSettings({...emailSettings, smtp_server: e.target.value})} placeholder="smtp.gmail.com" />
              </div>
              <div className="form-group">
                <label>SMTP Port</label>
                <input type="number" className="form-control" value={emailSettings.smtp_port || 587} onChange={e => setEmailSettings({...emailSettings, smtp_port: parseInt(e.target.value)})} />
              </div>
              <div className="form-group">
                <label>SMTP Username</label>
                <input type="email" className="form-control" value={emailSettings.smtp_user || ''} onChange={e => setEmailSettings({...emailSettings, smtp_user: e.target.value})} placeholder="your@gmail.com" />
              </div>
              <div className="form-group">
                <label>SMTP Password / App Password</label>
                <input type="password" className="form-control" value={emailSettings.smtp_password || ''} onChange={e => setEmailSettings({...emailSettings, smtp_password: e.target.value})} placeholder={emailSettings.smtp_password_set ? '••••••••••••••••' : 'Enter App Password'} />
                <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>For Gmail, use an App Password (not your Gmail login password)</small>
              </div>
              {emailSettingsMsg && (
                <p style={{ fontSize: '0.85rem', color: emailSettingsMsg.includes('success') ? '#22c55e' : '#ef4444', marginBottom: '1rem' }}>{emailSettingsMsg}</p>
              )}
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button type="button" className="btn" style={{ background: 'transparent', border: '1px solid var(--border)' }}
                  onClick={async () => {
                    try {
                      const res = await api.post('/settings/email/test');
                      setEmailSettingsMsg(res.data.message);
                    } catch (err) {
                      setEmailSettingsMsg('Test failed: ' + (err.response?.data?.detail || err.message));
                    }
                  }}>
                  Send Test Email
                </button>
                <button type="submit" className="btn">Save Settings</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Sidebar ── */}
      <div className="sidebar">
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
          <button className="nav-item active"><LayoutDashboard size={20} /> HR Dashboard</button>
          <button className="nav-item" onClick={() => navigate('/employees')}><Users size={20} /> Employees</button>
          <button className="nav-item" onClick={() => navigate('/manage-content')}><Settings size={20} /> Manage Content</button>
          <button className="nav-item" onClick={() => navigate('/activity-logs')}><Activity size={20} /> Activity Logs</button>
        </nav>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: 'auto' }}>
          <button className="nav-item" onClick={() => setShowChangePassword(true)} style={{ color: 'var(--text-muted)' }}>
            Change Password
          </button>
          <button className="nav-item" onClick={() => { setShowEmailSettings(true); loadEmailSettings(); }} style={{ color: 'var(--text-muted)' }}>
             Email Settings
          </button>
          <button className="nav-item" onClick={() => { setShowEmailSettings(true); loadEmailSettings(); }}>
  Email Settings
</button>
          <button className="nav-item" onClick={handleLogout} style={{ color: '#ef4444' }}>
            <LogOut size={20} /> Sign Out
          </button>
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="main-content">
        <header style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h1 style={{ fontSize: '1.75rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <BarChart3 size={28} color="var(--primary-color)" /> HR Dashboard
              </h1>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Live onboarding progress across all employees</p>
            </div>
            <button className="btn" style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(99,102,241,0.15)', border: '1px solid var(--primary-color)', color: 'var(--primary-color)' }} onClick={handlePreview}>
              <Eye size={18} /> Preview Employee Portal
            </button>
          </div>
        </header>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
          {[
            { label: 'Total Employees', value: stats.total, icon: <Users size={22} />, color: '#6366f1' },
            { label: 'Completed', value: stats.completed, icon: <BarChart3 size={22} />, color: '#22c55e' },
            { label: 'In Progress', value: stats.inProgress, icon: <Clock size={22} />, color: '#3b82f6' },
            { label: 'Not Started', value: stats.notStarted, icon: <AlertCircle size={22} />, color: '#f59e0b' },
            { label: 'Avg Completion', value: `${stats.avgPct}%`, icon: <BarChart3 size={22} />, color: '#a855f7' },
          ].map((s, i) => (
            <div key={i} className="card" style={{ padding: '1.25rem', textAlign: 'center' }}>
              <div style={{ color: s.color, marginBottom: '0.5rem', display: 'flex', justifyContent: 'center' }}>{s.icon}</div>
              <p style={{ fontSize: '1.75rem', fontWeight: '700', color: s.color }}>{s.value}</p>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</p>
            </div>
          ))}
        </div>

        {/* Employee Table */}
        <div className="card" style={{ padding: '0' }}>
          <div style={{ padding: '1.25rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Users size={20} color="var(--primary-color)" /> All Employees ({stats.total})
            </h3>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn" style={{ width: 'auto', fontSize: '0.8rem', background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
                onClick={() => setShowArchived(!showArchived)}>
                {showArchived ? 'Hide Archived' : 'Show Archived'}
              </button>
              <button className="btn" style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={() => setShowAddModal(true)}>
                <UserPlus size={18} /> Add Employee
              </button>
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['EMPLOYEE', 'DEPARTMENT', 'DOJ', 'MODULES', 'PROGRESS', 'STATUS', 'CONTROLS'].map(h => (
                    <th key={h} style={{ padding: '0.85rem 1rem', textAlign: 'left', color: 'var(--text-muted)', fontWeight: '600', fontSize: '0.72rem', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {employees.map(emp => {
                  const badge = getStatusBadge(emp.completion_pct);
                  return (
                    <tr key={emp.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ fontWeight: '600' }}>{emp.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{emp.email}</div>
                      </td>
                      <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>{emp.department || 'N/A'}</td>
                      <td style={{ padding: '1rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{emp.doj}</td>
                      <td style={{ padding: '1rem', textAlign: 'center' }}>{emp.modules_completed}/{emp.total_modules}</td>
                      <td style={{ padding: '1rem', minWidth: '140px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div style={{ flex: 1, height: '6px', background: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${emp.completion_pct}%`, height: '100%', background: badge.color, borderRadius: '3px', transition: 'width 0.3s' }} />
                          </div>
                          <span style={{ fontSize: '0.8rem', fontWeight: '600', color: badge.color, minWidth: '35px' }}>{emp.completion_pct}%</span>
                        </div>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span style={{ padding: '0.25rem 0.75rem', borderRadius: '1rem', fontSize: '0.75rem', fontWeight: '600', background: badge.bg, color: badge.color }}>
                          {badge.label}
                        </span>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <button
  onClick={() => setEditingEmployee(emp)}
  title="Edit Employee"
  style={{ padding: '0.3rem 0.5rem', background: 'rgba(99,102,241,0.1)', color: '#6366f1', border: '1px solid #6366f1', borderRadius: '0.4rem', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px' }}>
  <Edit2 size={14} />
</button>
                        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                          <button onClick={async () => { if (!window.confirm(`Move ${emp.name} to next module?`)) return; try { await api.post(`/employees/${emp.id}/control?action=next`); fetchData(); } catch (err) { alert('Failed: ' + (err.response?.data?.detail || err.message)); } }}
                            style={{ padding: '0.3rem 0.5rem', fontSize: '0.72rem', background: 'rgba(59,130,246,0.1)', color: '#3b82f6', border: '1px solid #3b82f6', borderRadius: '0.4rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>Next →</button>
                          <button onClick={async () => { if (!window.confirm(`Move ${emp.name} to previous module?`)) return; try { await api.post(`/employees/${emp.id}/control?action=prev`); fetchData(); } catch (err) { alert('Failed: ' + (err.response?.data?.detail || err.message)); } }}
                            style={{ padding: '0.3rem 0.5rem', fontSize: '0.72rem', background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid #f59e0b', borderRadius: '0.4rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>← Prev</button>
                          <button onClick={async () => { if (!window.confirm(`Reset ALL onboarding for ${emp.name}?`)) return; try { await api.post(`/employees/${emp.id}/control?action=reset_all`); fetchData(); } catch (err) { alert('Failed: ' + (err.response?.data?.detail || err.message)); } }}
                            style={{ padding: '0.3rem 0.5rem', fontSize: '0.72rem', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid #ef4444', borderRadius: '0.4rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>Reset All</button>
                          <button onClick={async () => {
                            if (!window.confirm(`${emp.is_archived ? 'Unarchive' : 'Archive'} ${emp.name}?`)) return;
                            try {
                              await api.put(`/employees/${emp.id}/archive`);
                              await fetchData(showArchived);
                            } catch (err) {
                              alert('Failed: ' + (err.response?.data?.detail || err.message));
                            }
                          }}
                            style={{ padding: '0.3rem 0.5rem', fontSize: '0.72rem', background: 'rgba(168,85,247,0.1)', color: '#a855f7', border: '1px solid #a855f7', borderRadius: '0.4rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                            {emp.is_archived ? 'Unarchive' : 'Archive'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <style>{`
        .nav-item { display: flex; align-items: center; gap: 0.75rem; width: 100%; padding: 0.85rem 1rem; background: transparent; border: none; color: var(--text-muted); font-weight: 500; font-size: 0.95rem; border-radius: 0.75rem; cursor: pointer; transition: all 0.2s; text-align: left; }
        .nav-item:hover { background: rgba(255,255,255,0.05); color: var(--text-main); }
        .nav-item.active { background: var(--surface-card); color: var(--primary-color); border: 1px solid var(--border); }
      `}</style>
    </div>
  );
};

export default HRDashboard;
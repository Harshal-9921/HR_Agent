import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2 } from 'lucide-react';
import OnboardingModule from '../components/OnboardingModule';
import AcknowledgementForm from '../components/DataCollection';
import CompletionScreen from '../components/CompletionScreen';
import api from '../api';


const OnboardingFlow = () => {
  const [contents, setContents] = useState([]);
  const [completedIds, setCompletedIds] = useState(new Set());
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const isPreview = localStorage.getItem('is_preview') === 'true';

  const handleBackToHR = () => {
    const hrToken = localStorage.getItem('hr_token');
    if (hrToken) {
      localStorage.setItem('token', hrToken);
      localStorage.removeItem('hr_token');
      localStorage.removeItem('is_preview');
    }
    navigate('/hr-dashboard');
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [contentRes, progressRes] = await Promise.all([
        api.get('/content/'),
        api.get('/content/my-progress'),
      ]);

      const allContents = contentRes.data.filter(c => c.is_enabled !== false);
      const completedSet = progressRes.data.filter(p => p.completed).map(p => p.content_id);
      const doneIds = new Set(completedSet);

      // Keka's completion is tracked separately (EmployeeSubmission), not ModuleProgress.
      // If a Keka item exists in this employee's (role-filtered) content list, check it independently.
      const kekaItem = allContents.find(c => c.is_keka);
      if (kekaItem) {
        try {
          await api.get('/data/my-acknowledgement');
          doneIds.add(kekaItem.id);
        } catch {
          // not acknowledged yet — leave it out of doneIds
        }
      }

      setContents(allContents);
      setCompletedIds(doneIds);

      // Resume at the first not-yet-completed item (Keka or module, whichever comes first in order)
      let resumeStep = allContents.length + 1; // default: everything done -> completion screen
      for (let i = 0; i < allContents.length; i++) {
        if (!doneIds.has(allContents[i].id)) {
          resumeStep = i + 1;
          break;
        }
      }
      setCurrentStep(resumeStep);
    } catch (err) {
      console.error('Failed to load onboarding data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    // Mark the item just completed (Keka or module, at currentStep) as done locally
    if (currentStep >= 1 && currentStep <= contents.length) {
      const justCompletedId = contents[currentStep - 1]?.id;
      if (justCompletedId) {
        setCompletedIds(prev => new Set(prev).add(justCompletedId));
      }
    }
    const totalSteps = contents.length + 1;
    setCurrentStep(prev => Math.min(prev + 1, totalSteps));
  };

  // Steps 1..N = contents (Keka included, wherever HR has positioned it), Step N+1 = Completion
  const dynamicSteps = [
    ...contents.map((c, i) => ({ id: i + 1, label: c.is_keka ? 'Acknowledgement' : c.title })),
    { id: contents.length + 1, label: 'Completion' },
  ];
  const totalSteps = dynamicSteps.length;

  const renderStepContent = () => {
    if (currentStep <= contents.length) {
      const content = contents[currentStep - 1];
      if (content.is_keka) {
        return <AcknowledgementForm content={content} onNext={handleNext} />;
      }
      return (
        <OnboardingModule
          key={content.id}
          content={content}
          alreadyCompleted={completedIds.has(content.id)}
          onNext={handleNext}
        />
      );
    } else {
      return <CompletionScreen onDashboard={() => {
        if (isPreview) {
          handleBackToHR();
        } else {
          navigate('/dashboard');
        }
      }} />;
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: '1rem' }}>
        <Loader2 size={48} color="var(--primary-color)" style={{ animation: 'spin 1s linear infinite' }} />
        <p style={{ color: 'var(--text-muted)' }}>Loading your onboarding programme…</p>
      </div>
    );
  }

  const realModules = contents.filter(c => !c.is_keka);
  const completedRealModules = realModules.filter(c => completedIds.has(c.id)).length;
  const completionPct = realModules.length > 0 ? Math.round((completedRealModules / realModules.length) * 100) : 0;

  return (
    <div className="dashboard-layout" style={{ flexDirection: 'column' }}>
      {isPreview && (
        <div style={{
          background: 'rgba(99,102,241,0.15)',
          border: '1px solid var(--primary-color)',
          padding: '0.75rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.9rem',
          color: 'var(--primary-color)',
          width: '100%',
          boxSizing: 'border-box'
        }}>
          <span>👁 You are previewing the Employee Portal as a demo user</span>
          <button
            onClick={handleBackToHR}
            style={{
              background: 'var(--primary-color)',
              color: 'white',
              border: 'none',
              padding: '0.4rem 1rem',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.85rem'
            }}
          >
            ← Back to HR Dashboard
          </button>
        </div>
      )}
      <div className="dashboard-layout" style={{ flex: 1 }}>
      {/* ── Sidebar ── */}
      <div className="sidebar" style={{ width: '300px' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '2rem' }}>Your Progress</h2>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {dynamicSteps.map((step) => {
            const isActive = step.id === currentStep;
            const isCompleted =
              step.id < currentStep ||
              (step.id >= 1 && step.id <= contents.length &&
                completedIds.has(contents[step.id - 1]?.id));

            return (
              <div key={step.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', marginBottom: '1.5rem' }}>
                <div style={{
                  width: '32px', height: '32px', borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  background: isCompleted ? 'var(--success)' : isActive ? 'var(--primary-color)' : 'transparent',
                  border: `2px solid ${isCompleted ? 'var(--success)' : isActive ? 'var(--primary-color)' : 'var(--border)'}`,
                  color: isCompleted || isActive ? 'white' : 'var(--text-muted)',
                  fontSize: '0.85rem', fontWeight: 'bold',
                }}>
                  {isCompleted ? <Check size={16} /> : step.id}
                </div>
                <div>
                  <p style={{ fontWeight: isActive ? '600' : '500', color: isActive || isCompleted ? 'var(--text-main)' : 'var(--text-muted)', fontSize: '0.9rem' }}>
                    {step.label}
                  </p>
                  {isActive && <p style={{ fontSize: '0.75rem', color: 'var(--primary-color)', marginTop: '0.2rem' }}>In Progress…</p>}
                  {isCompleted && <p style={{ fontSize: '0.75rem', color: 'var(--success)', marginTop: '0.2rem' }}>✔ Completed</p>}
                </div>
              </div>
            );
          })}
        </div>

        <div className="card" style={{ padding: '1.25rem', marginTop: '1rem' }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Overall Completion</p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{completionPct}%</span>
            <span style={{ fontSize: '0.8rem', color: '#f59e0b' }}>
              {completedRealModules}/{realModules.length} modules
            </span>
          </div>
          <div style={{ width: '100%', height: '8px', background: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{
              width: `${completionPct}%`, height: '100%',
              background: 'linear-gradient(90deg, var(--primary-color), var(--success))',
              borderRadius: '4px', transition: 'width 0.4s ease',
            }} />
          </div>
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="main-content" style={{ display: 'flex', flexDirection: 'column' }}>
        {/* Horizontal stepper */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0', marginBottom: '2rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
          {dynamicSteps.map((step, index) => {
            const isActive = step.id === currentStep;
            const isCompleted =
              step.id < currentStep ||
              (step.id >= 1 && step.id <= contents.length &&
                completedIds.has(contents[step.id - 1]?.id));

            return (
              <React.Fragment key={step.id}>
                <div className={`step-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`} style={{ whiteSpace: 'nowrap' }}>
                  <div className="step-circle">
                    {isCompleted ? <Check size={16} /> : step.id}
                  </div>
                  <span className="step-label">{step.label}</span>
                </div>
                {index < totalSteps - 1 && (
                  <div style={{
                    flex: 1, height: '2px', minWidth: '30px',
                    background: isCompleted ? 'var(--success)' : 'var(--border)',
                    margin: '0 4px', marginBottom: '1.2rem',
                  }} />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Step content */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {renderStepContent()}
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
    </div>
  );
};

export default OnboardingFlow;
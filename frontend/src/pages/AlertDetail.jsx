import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

function AlertDetail() {
    const { id } = useParams()
    const navigate = useNavigate()
    const [alert, setAlert] = useState(null)
    const [loading, setLoading] = useState(true)
    const [showDeAnon, setShowDeAnon] = useState(false)
    const [justification, setJustification] = useState('')

    useEffect(() => {
        // Simulated alert detail
        setTimeout(() => {
            setAlert({
                id: parseInt(id),
                level: 'high',
                type: 'Aggressive Posture',
                camera: 'Entrance-01',
                location: 'Main Building Entrance',
                time: '2024-01-30 11:42:15',
                status: 'active',
                score: 0.72,
                confidence: 0.68,
                description: 'Aggressive body posture detected between 2 individuals',
                factors: [
                    { name: 'Body Posture Analysis', weight: 0.4, description: 'Aggressive stance detected - raised arms, forward lean' },
                    { name: 'Rapid Approach', weight: 0.2, description: 'Quick movement toward another person' },
                    { name: 'Close Proximity', weight: 0.12, description: '2 persons within 1m radius' },
                ],
                limitations: [
                    'Cannot determine intent or context',
                    'May be normal greeting/interaction',
                    'Accuracy varies with camera angle',
                    'Requires human verification before action'
                ]
            })
            setLoading(false)
        }, 300)
    }, [id])

    const handleAction = (action) => {
        setAlert({ ...alert, status: action })
        // In production, call API
    }

    const handleDeAnonRequest = () => {
        if (justification.length < 10) {
            alert('Please provide a detailed justification (at least 10 characters)')
            return
        }
        // In production, call API
        setShowDeAnon(false)
        setJustification('')
        // Show success message
    }

    if (loading) return <div className="text-center mt-lg">Loading alert details...</div>
    if (!alert) return <div className="text-center mt-lg">Alert not found</div>

    return (
        <div>
            <button
                className="btn btn-secondary mb-lg"
                onClick={() => navigate('/alerts')}
            >
                ← Back to Alerts
            </button>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--spacing-lg)' }}>
                {/* Left Column - Video and Actions */}
                <div>
                    <div className="card mb-lg">
                        <div className="card-header">
                            <h2 className="card-title">Anonymized Video Clip</h2>
                            <span className={`risk-badge ${alert.level}`}>{alert.level}</span>
                        </div>
                        <div className="card-body">
                            <div style={{
                                aspectRatio: '16/9',
                                background: 'var(--bg-tertiary)',
                                borderRadius: 'var(--border-radius)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexDirection: 'column',
                                gap: '16px'
                            }}>
                                <span style={{ fontSize: '4rem' }}>🎬</span>
                                <span style={{ color: 'var(--text-muted)' }}>
                                    Anonymized clip (faces blurred)
                                </span>
                                <div className="flex gap-sm">
                                    <span className="risk-badge low">Privacy Protected</span>
                                </div>
                            </div>

                            <div className="mt-lg flex gap-md" style={{ justifyContent: 'center' }}>
                                <button className="btn btn-secondary">▶ Play</button>
                                <button className="btn btn-secondary">⏪ -5s</button>
                                <button className="btn btn-secondary">⏩ +5s</button>
                                <button className="btn btn-secondary">🔁 Loop</button>
                            </div>
                        </div>
                    </div>

                    {/* Operator Actions */}
                    <div className="card">
                        <div className="card-header">
                            <h2 className="card-title">Operator Actions</h2>
                        </div>
                        <div className="card-body">
                            <div className="flex gap-md" style={{ flexWrap: 'wrap' }}>
                                <button
                                    className="btn btn-primary"
                                    onClick={() => handleAction('acknowledged')}
                                    disabled={alert.status !== 'active'}
                                >
                                    ✓ Acknowledge Alert
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => handleAction('false_positive')}
                                >
                                    ✗ Mark False Positive
                                </button>
                                <button
                                    className="btn btn-danger"
                                    onClick={() => handleAction('escalated')}
                                >
                                    ⬆ Escalate to Supervisor
                                </button>
                            </div>

                            <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: 'var(--spacing-lg) 0' }} />

                            <button
                                className="btn btn-secondary"
                                onClick={() => setShowDeAnon(true)}
                                style={{ width: '100%' }}
                            >
                                🔓 Request De-anonymization (requires justification)
                            </button>
                        </div>
                    </div>
                </div>

                {/* Right Column - Risk Assessment */}
                <div>
                    <div className="card mb-lg">
                        <div className="card-header">
                            <h2 className="card-title">Risk Assessment</h2>
                        </div>
                        <div className="card-body">
                            <div className="mb-lg">
                                <div className="stat-label">Risk Level</div>
                                <div className={`stat-value ${alert.level}`} style={{ fontSize: 'var(--font-size-2xl)' }}>
                                    {alert.level.toUpperCase()}
                                </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)' }}>
                                <div>
                                    <div className="stat-label">Score</div>
                                    <div className="stat-value" style={{ fontSize: 'var(--font-size-xl)' }}>
                                        {(alert.score * 100).toFixed(0)}%
                                    </div>
                                </div>
                                <div>
                                    <div className="stat-label">Confidence</div>
                                    <div className="stat-value" style={{ fontSize: 'var(--font-size-xl)' }}>
                                        {(alert.confidence * 100).toFixed(0)}%
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="card mb-lg">
                        <div className="card-header">
                            <h2 className="card-title">Explanation</h2>
                        </div>
                        <div className="card-body">
                            <p style={{ marginBottom: 'var(--spacing-md)' }}>{alert.description}</p>

                            <div className="stat-label mb-sm">Contributing Factors:</div>
                            {alert.factors.map((factor, i) => (
                                <div key={i} style={{
                                    padding: 'var(--spacing-sm)',
                                    background: 'var(--bg-tertiary)',
                                    borderRadius: 'var(--border-radius-sm)',
                                    marginBottom: 'var(--spacing-sm)'
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span style={{ fontWeight: 500 }}>{factor.name}</span>
                                        <span style={{ color: 'var(--text-muted)' }}>
                                            weight: {(factor.weight * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
                                        {factor.description}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="card" style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                        <div className="card-header">
                            <h2 className="card-title">⚠️ Limitations</h2>
                        </div>
                        <div className="card-body">
                            <ul style={{ margin: 0, paddingLeft: 'var(--spacing-lg)' }}>
                                {alert.limitations.map((l, i) => (
                                    <li key={i} style={{
                                        color: 'var(--text-secondary)',
                                        fontSize: 'var(--font-size-sm)',
                                        marginBottom: 'var(--spacing-xs)'
                                    }}>
                                        {l}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* De-anonymization Modal */}
            {showDeAnon && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0,0,0,0.8)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                }}>
                    <div className="card" style={{ width: '100%', maxWidth: '500px', margin: 'var(--spacing-lg)' }}>
                        <div className="card-header">
                            <h2 className="card-title">🔓 De-anonymization Request</h2>
                        </div>
                        <div className="card-body">
                            <div className="disclaimer-banner" style={{ marginBottom: 'var(--spacing-lg)' }}>
                                <span className="disclaimer-icon">⚠️</span>
                                <div className="disclaimer-text">
                                    This action is logged and audited. De-anonymization is time-limited
                                    and requires documented justification.
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-label">Justification (required)</label>
                                <textarea
                                    className="form-input"
                                    rows="4"
                                    placeholder="Explain why de-anonymization is necessary..."
                                    value={justification}
                                    onChange={(e) => setJustification(e.target.value)}
                                    style={{ resize: 'vertical' }}
                                />
                            </div>

                            <div className="flex gap-md" style={{ justifyContent: 'flex-end' }}>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => setShowDeAnon(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="btn btn-danger"
                                    onClick={handleDeAnonRequest}
                                >
                                    Submit Request
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default AlertDetail

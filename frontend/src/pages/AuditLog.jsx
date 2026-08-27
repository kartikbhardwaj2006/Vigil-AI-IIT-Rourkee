import { useState, useEffect } from 'react'

function AuditLog({ user }) {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('all')

    useEffect(() => {
        // Simulated audit logs
        setTimeout(() => {
            setLogs([
                {
                    id: 1,
                    action: 'DE_ANONYMIZATION_REQUEST',
                    user: 'operator_12',
                    resource: 'Camera: Entrance-01',
                    justification: 'Verify suspicious behavior for alert #42',
                    status: 'approved',
                    approvedBy: 'supervisor_3',
                    timestamp: '2024-01-30 11:45:00'
                },
                {
                    id: 2,
                    action: 'ALERT_ACKNOWLEDGED',
                    user: 'operator_7',
                    resource: 'Alert #38',
                    justification: null,
                    status: 'completed',
                    approvedBy: null,
                    timestamp: '2024-01-30 11:30:22'
                },
                {
                    id: 3,
                    action: 'FALSE_POSITIVE_MARKED',
                    user: 'operator_12',
                    resource: 'Alert #35',
                    justification: null,
                    status: 'completed',
                    approvedBy: null,
                    timestamp: '2024-01-30 11:15:45'
                },
                {
                    id: 4,
                    action: 'DE_ANONYMIZATION_REQUEST',
                    user: 'operator_5',
                    resource: 'Camera: Parking-03',
                    justification: 'Investigate loitering individual',
                    status: 'pending',
                    approvedBy: null,
                    timestamp: '2024-01-30 11:10:00'
                },
                {
                    id: 5,
                    action: 'USER_LOGIN',
                    user: 'supervisor_3',
                    resource: 'System',
                    justification: null,
                    status: 'completed',
                    approvedBy: null,
                    timestamp: '2024-01-30 10:00:00'
                }
            ])
            setLoading(false)
        }, 300)
    }, [])

    const handleApprove = (logId) => {
        setLogs(logs.map(log =>
            log.id === logId
                ? { ...log, status: 'approved', approvedBy: user?.username || 'supervisor' }
                : log
        ))
    }

    const handleDeny = (logId) => {
        setLogs(logs.map(log =>
            log.id === logId ? { ...log, status: 'denied' } : log
        ))
    }

    const filteredLogs = logs.filter(log => {
        if (filter === 'all') return true
        if (filter === 'pending') return log.status === 'pending'
        if (filter === 'deanon') return log.action.includes('DE_ANONYMIZATION')
        return true
    })

    if (user?.role !== 'supervisor' && user?.role !== 'auditor') {
        return (
            <div className="card" style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                <span style={{ fontSize: '4rem' }}>🔒</span>
                <h2 style={{ marginTop: 'var(--spacing-lg)' }}>Access Restricted</h2>
                <p style={{ color: 'var(--text-secondary)' }}>
                    Audit logs are only accessible to supervisors and auditors.
                </p>
            </div>
        )
    }

    if (loading) return <div className="text-center mt-lg">Loading audit logs...</div>

    return (
        <div>
            <div className="disclaimer-banner">
                <span className="disclaimer-icon">📋</span>
                <div className="disclaimer-text">
                    <strong>Accountability Log:</strong> All sensitive actions are recorded here for transparency
                    and compliance. This log is immutable and tamper-evident.
                </div>
            </div>

            <div className="page-header flex justify-between items-center">
                <div>
                    <h1 className="page-title">Audit Log</h1>
                    <p className="page-subtitle">Complete record of all system actions</p>
                </div>
                <div className="flex gap-sm">
                    {['all', 'pending', 'deanon'].map(f => (
                        <button
                            key={f}
                            className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                            onClick={() => setFilter(f)}
                        >
                            {f === 'deanon' ? 'De-anon Requests' : f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            <div className="card">
                <div className="table-container">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Action</th>
                                <th>User</th>
                                <th>Resource</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredLogs.map(log => (
                                <tr key={log.id}>
                                    <td style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>
                                        {log.timestamp}
                                    </td>
                                    <td>
                                        <span style={{
                                            fontWeight: 500,
                                            color: log.action.includes('DE_ANONYMIZATION') ? 'var(--status-warning)' : 'inherit'
                                        }}>
                                            {log.action.replace(/_/g, ' ')}
                                        </span>
                                        {log.justification && (
                                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                                                "{log.justification}"
                                            </div>
                                        )}
                                    </td>
                                    <td>{log.user}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{log.resource}</td>
                                    <td>
                                        <span style={{
                                            color: log.status === 'approved' ? 'var(--status-success)' :
                                                log.status === 'pending' ? 'var(--status-warning)' :
                                                    log.status === 'denied' ? 'var(--status-danger)' :
                                                        'var(--text-muted)'
                                        }}>
                                            {log.status}
                                        </span>
                                        {log.approvedBy && (
                                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                                                by {log.approvedBy}
                                            </div>
                                        )}
                                    </td>
                                    <td>
                                        {log.status === 'pending' && user?.role === 'supervisor' && (
                                            <div className="flex gap-sm">
                                                <button
                                                    className="btn btn-sm btn-primary"
                                                    onClick={() => handleApprove(log.id)}
                                                >
                                                    ✓ Approve
                                                </button>
                                                <button
                                                    className="btn btn-sm btn-danger"
                                                    onClick={() => handleDeny(log.id)}
                                                >
                                                    ✗ Deny
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="stats-grid mt-lg">
                <div className="card stat-card">
                    <div className="stat-label">Total Actions (24h)</div>
                    <div className="stat-value info">{logs.length}</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">De-anon Requests</div>
                    <div className="stat-value medium">
                        {logs.filter(l => l.action.includes('DE_ANONYMIZATION')).length}
                    </div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">Pending Approvals</div>
                    <div className="stat-value" style={{ color: logs.some(l => l.status === 'pending') ? 'var(--status-warning)' : 'var(--status-success)' }}>
                        {logs.filter(l => l.status === 'pending').length}
                    </div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">Unique Users</div>
                    <div className="stat-value info">
                        {new Set(logs.map(l => l.user)).size}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default AuditLog

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

function Alerts() {
    const [alerts, setAlerts] = useState([])
    const [filter, setFilter] = useState('all')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Simulated data
        setTimeout(() => {
            setAlerts([
                {
                    id: 1,
                    level: 'high',
                    type: 'Aggressive Posture',
                    camera: 'Entrance-01',
                    location: 'Main Building Entrance',
                    time: '2 min ago',
                    status: 'active',
                    description: 'Aggressive body posture detected between 2 individuals'
                },
                {
                    id: 2,
                    level: 'high',
                    type: 'Crowd Density',
                    camera: 'Main-Hall-02',
                    location: 'Central Hall',
                    time: '5 min ago',
                    status: 'active',
                    description: 'Elevated crowd density: 23 persons detected'
                },
                {
                    id: 3,
                    level: 'medium',
                    type: 'Loitering',
                    camera: 'Parking-03',
                    location: 'Parking Lot A',
                    time: '12 min ago',
                    status: 'active',
                    description: 'Person stationary for 7+ minutes in sensitive area'
                },
                {
                    id: 4,
                    level: 'medium',
                    type: 'Unusual Motion',
                    camera: 'Corridor-05',
                    location: 'West Wing Corridor',
                    time: '18 min ago',
                    status: 'acknowledged',
                    description: 'Running detected in restricted zone'
                },
                {
                    id: 5,
                    level: 'low',
                    type: 'Crowd Density',
                    camera: 'Cafeteria-01',
                    location: 'Staff Cafeteria',
                    time: '25 min ago',
                    status: 'active',
                    description: 'Moderate crowd gathering: 12 persons'
                },
                {
                    id: 6,
                    level: 'medium',
                    type: 'Abandoned Object',
                    camera: 'Lobby-Main',
                    location: 'Main Lobby',
                    time: '32 min ago',
                    status: 'false_positive',
                    description: 'Stationary bag detected for 60+ seconds'
                }
            ])
            setLoading(false)
        }, 300)
    }, [])

    const filteredAlerts = alerts.filter(alert => {
        if (filter === 'all') return true
        if (filter === 'active') return alert.status === 'active'
        return alert.level === filter
    })

    const handleAction = (alertId, action) => {
        setAlerts(alerts.map(a => {
            if (a.id === alertId) {
                return { ...a, status: action === 'acknowledge' ? 'acknowledged' : 'false_positive' }
            }
            return a
        }))
    }

    if (loading) return <div className="text-center mt-lg">Loading alerts...</div>

    return (
        <div>
            <div className="disclaimer-banner">
                <span className="disclaimer-icon">⚠️</span>
                <div className="disclaimer-text">
                    <strong>Human Review Required:</strong> All alerts are automated indicators.
                    Please review carefully before taking any action. Mark false positives to improve system accuracy.
                </div>
            </div>

            <div className="page-header flex justify-between items-center">
                <div>
                    <h1 className="page-title">Alert Management</h1>
                    <p className="page-subtitle">Review and respond to detected risk indicators</p>
                </div>
                <div className="flex gap-sm">
                    {['all', 'active', 'high', 'medium', 'low'].map(f => (
                        <button
                            key={f}
                            className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                            onClick={() => setFilter(f)}
                        >
                            {f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            <div className="card">
                <div className="table-container">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Level</th>
                                <th>Type</th>
                                <th>Camera</th>
                                <th>Time</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredAlerts.map(alert => (
                                <tr key={alert.id}>
                                    <td>
                                        <span className={`risk-badge ${alert.level}`}>
                                            {alert.level}
                                        </span>
                                    </td>
                                    <td>
                                        <Link to={`/alerts/${alert.id}`} style={{ fontWeight: 500 }}>
                                            {alert.type}
                                        </Link>
                                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                                            {alert.description.substring(0, 50)}...
                                        </div>
                                    </td>
                                    <td>
                                        <div>{alert.camera}</div>
                                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                                            {alert.location}
                                        </div>
                                    </td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{alert.time}</td>
                                    <td>
                                        <span style={{
                                            color: alert.status === 'active' ? 'var(--status-warning)' :
                                                alert.status === 'acknowledged' ? 'var(--status-success)' :
                                                    'var(--text-muted)'
                                        }}>
                                            {alert.status.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="flex gap-sm">
                                            <Link to={`/alerts/${alert.id}`} className="btn btn-sm btn-primary">
                                                View
                                            </Link>
                                            {alert.status === 'active' && (
                                                <>
                                                    <button
                                                        className="btn btn-sm btn-secondary"
                                                        onClick={() => handleAction(alert.id, 'acknowledge')}
                                                    >
                                                        ✓
                                                    </button>
                                                    <button
                                                        className="btn btn-sm btn-secondary"
                                                        onClick={() => handleAction(alert.id, 'false_positive')}
                                                        title="Mark as False Positive"
                                                    >
                                                        ✗
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

export default Alerts

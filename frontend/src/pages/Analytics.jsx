import { useState } from 'react'

function Analytics() {
    const [timeRange, setTimeRange] = useState('24h')

    // Demo data
    const detectionTypes = [
        { type: 'Crowd Density', count: 45, percentage: 35 },
        { type: 'Loitering', count: 32, percentage: 25 },
        { type: 'Aggressive Posture', count: 18, percentage: 14 },
        { type: 'Unusual Motion', count: 20, percentage: 16 },
        { type: 'Abandoned Object', count: 13, percentage: 10 },
    ]

    const cameraStats = [
        { name: 'Main-Hall-02', alerts: 28, level: 'high' },
        { name: 'Entrance-01', alerts: 22, level: 'high' },
        { name: 'Parking-03', alerts: 15, level: 'medium' },
        { name: 'Cafeteria-01', alerts: 12, level: 'medium' },
        { name: 'Corridor-05', alerts: 8, level: 'low' },
        { name: 'Lobby-Main', alerts: 6, level: 'low' },
    ]

    return (
        <div>
            <div className="page-header flex justify-between items-center">
                <div>
                    <h1 className="page-title">Analytics</h1>
                    <p className="page-subtitle">Historical analysis and system performance metrics</p>
                </div>
                <div className="flex gap-sm">
                    {['24h', '7d', '30d'].map(range => (
                        <button
                            key={range}
                            className={`btn ${timeRange === range ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                            onClick={() => setTimeRange(range)}
                        >
                            {range}
                        </button>
                    ))}
                </div>
            </div>

            {/* Summary Stats */}
            <div className="stats-grid">
                <div className="card stat-card">
                    <div className="stat-label">Total Alerts</div>
                    <div className="stat-value info">128</div>
                    <div className="stat-trend">↑ 12% from previous period</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">False Positive Rate</div>
                    <div className="stat-value low">18%</div>
                    <div className="stat-trend">↓ 3% improvement</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">Avg Response Time</div>
                    <div className="stat-value info">4.2 min</div>
                    <div className="stat-trend">Within target</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">System Uptime</div>
                    <div className="stat-value low">99.7%</div>
                    <div className="stat-trend">Last 30 days</div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-lg)' }}>
                {/* Detection Types */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Detection Types</h2>
                    </div>
                    <div className="card-body">
                        {detectionTypes.map(dt => (
                            <div key={dt.type} style={{ marginBottom: 'var(--spacing-md)' }}>
                                <div className="flex justify-between mb-sm">
                                    <span>{dt.type}</span>
                                    <span style={{ color: 'var(--text-muted)' }}>{dt.count} alerts</span>
                                </div>
                                <div style={{
                                    height: '8px',
                                    background: 'var(--bg-tertiary)',
                                    borderRadius: '4px',
                                    overflow: 'hidden'
                                }}>
                                    <div style={{
                                        width: `${dt.percentage}%`,
                                        height: '100%',
                                        background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))',
                                        borderRadius: '4px'
                                    }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Camera Activity */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Camera Activity</h2>
                    </div>
                    <div className="card-body">
                        {cameraStats.map(cam => (
                            <div
                                key={cam.name}
                                className="flex justify-between items-center"
                                style={{
                                    padding: 'var(--spacing-sm) var(--spacing-md)',
                                    background: 'var(--bg-tertiary)',
                                    borderRadius: 'var(--border-radius-sm)',
                                    marginBottom: 'var(--spacing-sm)'
                                }}
                            >
                                <span style={{ fontWeight: 500 }}>{cam.name}</span>
                                <div className="flex gap-sm items-center">
                                    <span style={{ color: 'var(--text-muted)' }}>{cam.alerts} alerts</span>
                                    <span className={`risk-badge ${cam.level}`}>{cam.level}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Timeline Chart Placeholder */}
            <div className="card mt-lg">
                <div className="card-header">
                    <h2 className="card-title">Alert Timeline</h2>
                </div>
                <div className="card-body">
                    <div style={{
                        height: '200px',
                        background: 'var(--bg-tertiary)',
                        borderRadius: 'var(--border-radius)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--text-muted)'
                    }}>
                        📊 Timeline chart visualization would appear here
                    </div>
                </div>
            </div>

            {/* System Performance */}
            <div className="card mt-lg">
                <div className="card-header">
                    <h2 className="card-title">System Performance</h2>
                </div>
                <div className="card-body">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--spacing-md)' }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--status-success)' }}>
                                12 FPS
                            </div>
                            <div style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
                                Processing Rate
                            </div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--status-success)' }}>
                                85ms
                            </div>
                            <div style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
                                Avg Latency
                            </div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--status-info)' }}>
                                8/8
                            </div>
                            <div style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
                                Cameras Online
                            </div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--status-success)' }}>
                                Healthy
                            </div>
                            <div style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
                                ML Pipeline
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Analytics

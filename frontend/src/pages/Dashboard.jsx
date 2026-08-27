import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { decreaseBlur, getPrivacyStatus, increaseBlur, setAnonymizationEnabled } from '../services/api'

// API base URL
const API_BASE = 'http://localhost:8000'
const WS_BASE = 'ws://localhost:8000'

function Dashboard() {
    const [stats, setStats] = useState({
        alerts: { total: 0, high: 0, medium: 0, low: 0, active: 0 },
        cameras: { total: 5, active: 5 }
    })
    const [recentAlerts, setRecentAlerts] = useState([])
    const [loading, setLoading] = useState(true)
    const [cameraStats, setCameraStats] = useState({})
    const [systemMetrics, setSystemMetrics] = useState(null)
    const [privacy, setPrivacy] = useState(null)
    const [privacyError, setPrivacyError] = useState(null)
    const [events, setEvents] = useState([])

    const lastRiskRef = useRef({})
    const lastSeenRef = useRef({})

    // ALL 5 demo cameras
    const cameras = [
        { id: 'video1', name: 'Video Feed 1', location: 'Entrance Area' },
        { id: 'video2', name: 'Video Feed 2', location: 'Main Hall' },
        { id: 'video3', name: 'Video Feed 3', location: 'Corridor' },
        { id: 'video4', name: 'Video Feed 4', location: 'Parking Area' },
        { id: 'video5', name: 'Video Feed 5', location: 'Side Entrance' },
    ]

    useEffect(() => {
        // Simulated data for demo
        setTimeout(() => {
            setStats({
                alerts: { total: 19, high: 2, medium: 5, low: 12, active: 7 },
                cameras: { total: 5, active: 5 }
            })
            setRecentAlerts([])
            setLoading(false)
        }, 500)
    }, [])

    // Fetch privacy + runtime status (blur level, anonymization, metrics)
    useEffect(() => {
        let cancelled = false

        const load = async () => {
            try {
                const data = await getPrivacyStatus()
                if (!cancelled) {
                    setPrivacy(data)
                    setPrivacyError(null)
                }
            } catch (e) {
                if (!cancelled) setPrivacyError(e?.message || 'Failed to load privacy status')
            }
        }

        load()
        const id = setInterval(load, 5000)
        return () => {
            cancelled = true
            clearInterval(id)
        }
    }, [])

    // WebSocket connections for real-time stats
    useEffect(() => {
        const connections = {}

        cameras.forEach(camera => {
            const ws = new WebSocket(`${WS_BASE}/ws/camera/${camera.id}/stats`)

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    if (data.person_count !== undefined) {
                        lastSeenRef.current[camera.id] = Date.now()

                        setCameraStats(prev => ({
                            ...prev,
                            [camera.id]: {
                                personCount: data.person_count,
                                bagCount: data.bag_count || 0,
                                riskLevel: data.risk_level || 'low',
                                metrics: data.metrics || {},
                            }
                        }))

                        // System-wide metrics (use latest frame metrics from any camera)
                        if (data.metrics && data.metrics.fps !== undefined) {
                            setSystemMetrics(data.metrics)
                        }

                        // Recent events timeline: log risk level transitions (debounced backend already)
                        const prevLevel = lastRiskRef.current[camera.id]
                        const nextLevel = data.risk_level || 'low'
                        if (prevLevel && prevLevel !== nextLevel) {
                            setEvents((ev) => [
                                {
                                    id: `${camera.id}-${Date.now()}`,
                                    cameraId: camera.id,
                                    cameraName: camera.name,
                                    level: nextLevel,
                                    ts: new Date().toISOString(),
                                    message: `Risk changed ${prevLevel.toUpperCase()} → ${nextLevel.toUpperCase()}`,
                                },
                                ...ev,
                            ].slice(0, 20))
                        }
                        lastRiskRef.current[camera.id] = nextLevel
                    }
                } catch (e) {
                    console.error('Error parsing stats:', e)
                }
            }

            connections[camera.id] = ws
        })

        // Cleanup on unmount
        return () => {
            Object.values(connections).forEach(ws => ws.close())
        }
    }, [])

    const overallRisk = useMemo(() => {
        const levels = Object.values(cameraStats).map((s) => s?.riskLevel || 'low')
        if (levels.includes('high')) return 'high'
        if (levels.includes('medium')) return 'medium'
        return 'low'
    }, [cameraStats])

    const systemHealth = useMemo(() => {
        const pipelineLoaded = privacy?.pipeline_loaded ?? true
        const now = Date.now()
        const recent = cameras.some((c) => {
            const t = lastSeenRef.current[c.id]
            return t && now - t < 8000
        })

        if (!pipelineLoaded) return 'down'
        if (!recent) return 'degraded'
        return 'healthy'
    }, [privacy, cameras])

    const alertStatus = useMemo(() => {
        if (overallRisk === 'high') return { label: 'ALERT', level: 'high' }
        if (overallRisk === 'medium') return { label: 'WATCH', level: 'medium' }
        return { label: 'NORMAL', level: 'low' }
    }, [overallRisk])

    const handleIncreaseBlur = async () => {
        try {
            await increaseBlur(10)
            const data = await getPrivacyStatus()
            setPrivacy(data)
        } catch (e) {
            setPrivacyError(e?.message || 'Failed to increase blur')
        }
    }

    const handleDecreaseBlur = async () => {
        try {
            await decreaseBlur(10)
            const data = await getPrivacyStatus()
            setPrivacy(data)
        } catch (e) {
            setPrivacyError(e?.message || 'Failed to decrease blur')
        }
    }

    const handleToggleAnonymization = async () => {
        try {
            const next = !(privacy?.anonymization_enabled ?? true)
            await setAnonymizationEnabled(next)
            const data = await getPrivacyStatus()
            setPrivacy(data)
            setPrivacyError(null)
        } catch (e) {
            setPrivacyError(e?.message || 'Failed to toggle anonymization')
        }
    }

    // Generate stream URL for a camera
    const getStreamUrl = (cameraId) => {
        return `${API_BASE}/api/stream/video/${cameraId}?detections=true&fps=10`
    }

    if (loading) {
        return <div className="text-center mt-lg">Loading dashboard...</div>
    }

    return (
        <div>
            {/* Disclaimer Banner */}
            <div className="disclaimer-banner">
                <span className="disclaimer-icon">!</span>
                <div className="disclaimer-text">
                    <strong>Decision-Support Tool:</strong> All alerts are automated indicators that require
                    human verification. This system cannot determine intent and should not be used as the
                    sole basis for any enforcement action.
                </div>
            </div>

            {/* Page Header */}
            <div className="page-header">
                <h1 className="page-title">Dashboard</h1>
                <p className="page-subtitle">Real-time overview of surveillance system status - 5 Active Cameras</p>
            </div>

            {/* Live System Panel */}
            <div className="card" style={{ marginBottom: 'var(--spacing-xl)' }}>
                <div className="card-header">
                    <h2 className="card-title">Live System Panel</h2>
                    <span className={`risk-badge ${overallRisk}`}>RISK: {overallRisk}</span>
                </div>
                <div className="card-body">
                    <div className="system-panel-grid" style={{ marginBottom: 'var(--spacing-md)' }}>
                        <div className="stat-card card">
                            <div className="stat-label">System Health</div>
                            <div className="status-pill" style={{ marginTop: '8px' }}>
                                <span className={`health-dot ${systemHealth === 'healthy' ? '' : systemHealth}`}></span>
                                {systemHealth.toUpperCase()}
                            </div>
                        </div>
                        <div className="stat-card card">
                            <div className="stat-label">FPS</div>
                            <div className="stat-value info">
                                {systemMetrics?.fps ? systemMetrics.fps.toFixed(1) : '—'}
                            </div>
                            <div className="stat-trend">Rolling estimate</div>
                        </div>
                        <div className="stat-card card">
                            <div className="stat-label">Alert Status</div>
                            <div className={`stat-value ${alertStatus.level}`}>{alertStatus.label}</div>
                            <div className="stat-trend">Derived from live risk</div>
                        </div>
                        <div className="stat-card card">
                            <div className="stat-label">Anonymization</div>
                            <div className="stat-value info">
                                {(privacy?.anonymization_enabled ?? true) ? 'ON' : 'OFF'}
                            </div>
                            <div className="stat-trend">
                                Blur: {privacy?.blur_level || '—'} ({privacy?.blur_intensity ?? '—'})
                            </div>
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--spacing-sm)', alignItems: 'center' }}>
                        <button className="btn btn-secondary" onClick={handleDecreaseBlur} type="button">
                            Decrease blur
                        </button>
                        <button className="btn btn-secondary" onClick={handleIncreaseBlur} type="button">
                            Increase blur
                        </button>
                        <button className="btn btn-danger" onClick={handleToggleAnonymization} type="button">
                            Toggle anonymization
                        </button>

                        {privacy?.allow_demo_privacy_override === false && (
                            <span className="risk-badge low">Demo/admin override disabled</span>
                        )}
                        {privacyError && (
                            <span className="risk-badge medium">{privacyError}</span>
                        )}
                    </div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="card stat-card">
                    <div className="stat-label">High Priority</div>
                    <div className="stat-value high">{stats.alerts.high}</div>
                    <div className="stat-trend">Requires immediate review</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">Medium Priority</div>
                    <div className="stat-value medium">{stats.alerts.medium}</div>
                    <div className="stat-trend">Review at earliest convenience</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">Low Priority</div>
                    <div className="stat-value low">{stats.alerts.low}</div>
                    <div className="stat-trend">Routine monitoring</div>
                </div>
                <div className="card stat-card">
                    <div className="stat-label">Active Cameras</div>
                    <div className="stat-value info">{stats.cameras.active}/{stats.cameras.total}</div>
                    <div className="stat-trend">All systems operational</div>
                </div>
            </div>

            {/* Two Column Layout */}
            <div className="two-col-grid">
                {/* Recent Events */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Recent Events</h2>
                        <Link to="/alerts" className="btn btn-sm btn-secondary">View All</Link>
                    </div>
                    <div className="card-body">
                        <div className="alert-list">
                            {events.length === 0 ? (
                                <div className="text-center text-muted">Waiting for live events…</div>
                            ) : events.map((ev) => (
                                <div key={ev.id} className="alert-item">
                                    <div className={`alert-indicator ${ev.level}`}></div>
                                    <div className="alert-content">
                                        <div className="alert-title">{ev.message}</div>
                                        <div className="alert-meta">
                                            <span>Camera: {ev.cameraName}</span>
                                            <span>{new Date(ev.ts).toLocaleTimeString()}</span>
                                        </div>
                                    </div>
                                    <span className={`risk-badge ${ev.level}`}>{ev.level}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Camera Preview with ACTUAL VIDEO FEEDS - All 5 cameras */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Live Camera Feeds (5)</h2>
                        <Link to="/live" className="btn btn-sm btn-secondary">Full View</Link>
                    </div>
                    <div className="card-body">
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(3, 1fr)',
                            gap: 'var(--spacing-sm)',
                            maxHeight: '400px',
                            overflowY: 'auto'
                        }}>
                            {cameras.map((camera) => {
                                const stats = cameraStats[camera.id] || { personCount: 0, bagCount: 0, riskLevel: 'low' }
                                return (
                                    <Link key={camera.id} to="/live" className="camera-card" style={{ textDecoration: 'none' }}>
                                        <div className="camera-feed" style={{ position: 'relative' }}>
                                            {/* MJPEG Stream Image */}
                                            <img
                                                src={getStreamUrl(camera.id)}
                                                alt={`${camera.name} live feed`}
                                                style={{
                                                    width: '100%',
                                                    height: '100%',
                                                    objectFit: 'cover'
                                                }}
                                                onError={(e) => {
                                                    e.target.style.display = 'none'
                                                    e.target.nextSibling.style.display = 'flex'
                                                }}
                                            />
                                            {/* Fallback */}
                                            <div style={{
                                                display: 'none',
                                                width: '100%',
                                                height: '100%',
                                                background: 'var(--bg-tertiary)',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                color: 'var(--text-muted)',
                                                fontSize: 'var(--font-size-sm)'
                                            }}>
                                                Connecting...
                                            </div>

                                            {/* Stats overlay */}
                                            <div style={{
                                                position: 'absolute',
                                                top: '4px',
                                                right: '4px',
                                                background: 'var(--overlay-bg)',
                                                padding: '4px 6px',
                                                borderRadius: '4px',
                                                fontSize: '10px',
                                                fontWeight: '600',
                                                display: 'flex',
                                                gap: '6px'
                                            }}>
                                                <span>P: {stats.personCount}</span>
                                                <span>B: {stats.bagCount}</span>
                                            </div>
                                        </div>
                                        <div className="camera-status">
                                            <span className="status-dot"></span>
                                            <span>Live</span>
                                        </div>
                                        <div className="camera-overlay">
                                            <div className="camera-name">{camera.name}</div>
                                            <div className="camera-location">{camera.location}</div>
                                        </div>
                                    </Link>
                                )
                            })}
                        </div>
                    </div>
                </div>
            </div>

            {/* System Disclaimer Footer */}
            <div className="card mt-lg" style={{ background: 'rgba(37, 99, 235, 0.05)', borderColor: 'rgba(37, 99, 235, 0.2)' }}>
                <div className="card-body" style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                        <strong>System Limitations:</strong> AI models may exhibit detection bias.
                        All video feeds are anonymized by default.
                        Risk scores are probabilistic indicators, not determinations.
                        <Link to="/about" style={{ marginLeft: '8px' }}>Learn more</Link>
                    </p>
                </div>
            </div>
        </div>
    )
}

export default Dashboard

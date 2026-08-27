import { useEffect, useState } from 'react'
import { decreaseBlur, getPrivacyStatus, increaseBlur, setAnonymizationEnabled } from '../services/api'

// API base URL for stream endpoints
const API_BASE = 'http://localhost:8000'
const WS_BASE = 'ws://localhost:8000'

function LiveView() {
    const [selectedCamera, setSelectedCamera] = useState(null)
    const [streamError, setStreamError] = useState({})
    const [showDetections, setShowDetections] = useState(true)
    const [cameraStats, setCameraStats] = useState({})
    const [privacy, setPrivacy] = useState(null)
    const [privacyError, setPrivacyError] = useState(null)

    // ALL 5 demo cameras
    const cameras = [
        { id: 'video1', name: 'Video Feed 1', location: 'Entrance Area', status: 'active' },
        { id: 'video2', name: 'Video Feed 2', location: 'Main Hall', status: 'active' },
        { id: 'video3', name: 'Video Feed 3', location: 'Corridor', status: 'active' },
        { id: 'video4', name: 'Video Feed 4', location: 'Parking Area', status: 'active' },
        { id: 'video5', name: 'Video Feed 5', location: 'Side Entrance', status: 'active' },
    ]

    // WebSocket connections for real-time stats
    useEffect(() => {
        const connections = {}

        cameras.forEach(camera => {
            const ws = new WebSocket(`${WS_BASE}/ws/camera/${camera.id}/stats`)

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    if (data.person_count !== undefined) {
                        setCameraStats(prev => ({
                            ...prev,
                            [camera.id]: {
                                personCount: data.person_count,
                                bagCount: data.bag_count || 0,
                                riskLevel: data.risk_level || 'low'
                            }
                        }))
                    }
                } catch (e) {
                    console.error('Error parsing stats:', e)
                }
            }

            ws.onerror = (error) => {
                console.log(`WebSocket error for ${camera.id}:`, error)
            }

            connections[camera.id] = ws
        })

        // Cleanup on unmount
        return () => {
            Object.values(connections).forEach(ws => ws.close())
        }
    }, [])

    // Privacy status for anonymization controls
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

    const handleIncreaseBlur = async () => {
        try {
            await increaseBlur(10)
            setPrivacy(await getPrivacyStatus())
        } catch (e) {
            setPrivacyError(e?.message || 'Failed to increase blur')
        }
    }

    const handleDecreaseBlur = async () => {
        try {
            await decreaseBlur(10)
            setPrivacy(await getPrivacyStatus())
        } catch (e) {
            setPrivacyError(e?.message || 'Failed to decrease blur')
        }
    }

    const handleToggleAnonymization = async () => {
        try {
            const next = !(privacy?.anonymization_enabled ?? true)
            await setAnonymizationEnabled(next)
            setPrivacy(await getPrivacyStatus())
            setPrivacyError(null)
        } catch (e) {
            setPrivacyError(e?.message || 'Failed to toggle anonymization')
        }
    }

    // Generate stream URL for a camera
    const getStreamUrl = (cameraId, detections = true) => {
        return `${API_BASE}/api/stream/video/${cameraId}?detections=${detections}&fps=15`
    }

    // Handle stream error
    const handleStreamError = (cameraId) => {
        setStreamError(prev => ({ ...prev, [cameraId]: true }))
    }

    // Handle stream load
    const handleStreamLoad = (cameraId) => {
        setStreamError(prev => ({ ...prev, [cameraId]: false }))
    }

    return (
        <div>
            {/* Disclaimer */}
            <div className="disclaimer-banner">
                <span className="disclaimer-icon">!</span>
                <div className="disclaimer-text">
                    <strong>Privacy Notice:</strong> All video feeds are anonymized by default.
                    Faces are blurred to protect privacy. De-anonymization requires supervisor approval
                    and is fully logged.
                </div>
            </div>

            <div className="page-header">
                <h1 className="page-title">Live Camera View</h1>
                <p className="page-subtitle">Real-time monitoring with privacy-preserving anonymization - 5 Active Cameras</p>
            </div>

            {/* Controls */}
            <div className="card" style={{ marginBottom: 'var(--spacing-lg)', padding: 'var(--spacing-md)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={showDetections}
                            onChange={(e) => setShowDetections(e.target.checked)}
                        />
                        Show Detection Overlays
                    </label>
                    <span className="risk-badge low">Demo Mode Active - 5 Cameras</span>

                    <span className="status-pill">
                        <span className="health-dot"></span>
                        Anonymization: {(privacy?.anonymization_enabled ?? true) ? 'ON' : 'OFF'}
                    </span>
                    <span className="status-pill">
                        Blur: {privacy?.blur_level || '—'} ({privacy?.blur_intensity ?? '—'})
                    </span>

                    <button className="btn btn-secondary btn-sm" onClick={handleDecreaseBlur} type="button">
                        Blur -
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={handleIncreaseBlur} type="button">
                        Blur +
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={handleToggleAnonymization} type="button">
                        Toggle Anonymization
                    </button>
                    {privacy?.allow_demo_privacy_override === false && (
                        <span className="risk-badge low">Override disabled</span>
                    )}
                    {privacyError && <span className="risk-badge medium">{privacyError}</span>}
                </div>
            </div>

            {/* Camera Grid - Updated for 5 cameras */}
            <div className="camera-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
                {cameras.map((camera) => {
                    const stats = cameraStats[camera.id] || { personCount: 0, bagCount: 0, riskLevel: 'low' }

                    return (
                        <div
                            key={camera.id}
                            className="camera-card card"
                            onClick={() => setSelectedCamera(camera)}
                            style={{ cursor: 'pointer' }}
                        >
                            <div className="camera-feed" style={{ position: 'relative', overflow: 'hidden' }}>
                                {/* MJPEG Stream Image */}
                                <img
                                    src={getStreamUrl(camera.id, showDetections)}
                                    alt={`${camera.name} anonymized feed`}
                                    onError={() => handleStreamError(camera.id)}
                                    onLoad={() => handleStreamLoad(camera.id)}
                                    style={{
                                        width: '100%',
                                        height: '100%',
                                        objectFit: 'cover',
                                        display: streamError[camera.id] ? 'none' : 'block'
                                    }}
                                />

                                {/* Fallback for stream errors */}
                                {streamError[camera.id] && (
                                    <div style={{
                                        width: '100%',
                                        height: '100%',
                                        background: '#e5e7eb',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexDirection: 'column',
                                        color: 'var(--text-muted)',
                                        gap: '8px'
                                    }}>
                                        <span style={{ fontSize: '2rem', fontWeight: 'bold' }}>CAM</span>
                                        <span style={{ fontSize: 'var(--font-size-xs)' }}>
                                            Connecting to stream...
                                        </span>
                                    </div>
                                )}

                                {/* Anonymized badge */}
                                <div style={{
                                    position: 'absolute',
                                    top: '8px',
                                    right: '8px',
                                    background: 'rgba(5, 150, 105, 0.9)',
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    fontSize: 'var(--font-size-xs)',
                                    color: 'white',
                                    fontWeight: 'bold'
                                }}>
                                    ANONYMIZED
                                </div>

                                {/* Real-time stats overlay */}
                                <div style={{
                                    position: 'absolute',
                                    bottom: '50px',
                                    left: '8px',
                                    right: '8px',
                                    background: 'var(--overlay-bg)',
                                    padding: '8px',
                                    borderRadius: '6px',
                                    fontSize: 'var(--font-size-xs)',
                                    fontWeight: '500',
                                    boxShadow: 'var(--shadow-sm)'
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                        <span>People:</span>
                                        <strong>{stats.personCount}</strong>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                        <span>Bags:</span>
                                        <strong>{stats.bagCount}</strong>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span>Risk:</span>
                                        <span className={`risk-badge ${stats.riskLevel}`}>{stats.riskLevel}</span>
                                    </div>
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
                        </div>
                    )
                })}
            </div>

            {/* Camera Detail Modal */}
            {selectedCamera && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0,0,0,0.5)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                        padding: 'var(--spacing-lg)'
                    }}
                    onClick={() => setSelectedCamera(null)}
                >
                    <div
                        className="card"
                        style={{ width: '100%', maxWidth: '900px' }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="card-header">
                            <div>
                                <h2 className="card-title">{selectedCamera.name}</h2>
                                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                                    {selectedCamera.location}
                                </p>
                            </div>
                            <button
                                className="btn btn-secondary"
                                onClick={() => setSelectedCamera(null)}
                            >
                                Close
                            </button>
                        </div>
                        <div className="card-body">
                            {/* Full-size MJPEG stream */}
                            <div style={{
                                aspectRatio: '16/9',
                                background: 'var(--bg-tertiary)',
                                borderRadius: 'var(--border-radius)',
                                overflow: 'hidden',
                                marginBottom: 'var(--spacing-lg)',
                                position: 'relative'
                            }}>
                                <img
                                    src={getStreamUrl(selectedCamera.id, showDetections)}
                                    alt={`${selectedCamera.name} live anonymized feed`}
                                    style={{
                                        width: '100%',
                                        height: '100%',
                                        objectFit: 'contain'
                                    }}
                                    onError={(e) => {
                                        e.target.style.display = 'none'
                                    }}
                                />

                                {/* Privacy badges */}
                                <div style={{
                                    position: 'absolute',
                                    top: '12px',
                                    right: '12px',
                                    display: 'flex',
                                    gap: '8px'
                                }}>
                                    <span className="risk-badge low">Faces Blurred</span>
                                    <span className="risk-badge low">Privacy Protected</span>
                                </div>
                            </div>

                            {(() => {
                                const stats = cameraStats[selectedCamera.id] || { personCount: 0, bagCount: 0, riskLevel: 'low' }
                                return (
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--spacing-md)' }}>
                                        <div className="stat-card card">
                                            <div className="stat-label">Person Count</div>
                                            <div className="stat-value info">{stats.personCount}</div>
                                        </div>
                                        <div className="stat-card card">
                                            <div className="stat-label">Bag Count</div>
                                            <div className="stat-value">{stats.bagCount}</div>
                                        </div>
                                        <div className="stat-card card">
                                            <div className="stat-label">Risk Level</div>
                                            <div className={`stat-value ${stats.riskLevel}`}>{stats.riskLevel}</div>
                                        </div>
                                        <div className="stat-card card">
                                            <div className="stat-label">Feed Status</div>
                                            <div className="stat-value" style={{ color: 'var(--status-success)' }}>Live</div>
                                        </div>
                                    </div>
                                )
                            })()}

                            {/* Stream controls */}
                            <div style={{
                                display: 'flex',
                                gap: 'var(--spacing-md)',
                                marginTop: 'var(--spacing-lg)',
                                marginBottom: 'var(--spacing-lg)'
                            }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                    <input
                                        type="checkbox"
                                        checked={showDetections}
                                        onChange={(e) => setShowDetections(e.target.checked)}
                                    />
                                    Show Detection Overlays
                                </label>
                            </div>

                            <div className="disclaimer-banner mt-lg" style={{ marginBottom: 0 }}>
                                <span className="disclaimer-icon">i</span>
                                <div className="disclaimer-text">
                                    Detection overlays can be toggled. All analysis is performed locally.
                                    No raw footage leaves this system.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default LiveView

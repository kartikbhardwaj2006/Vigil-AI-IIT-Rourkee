function Settings() {
    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">Settings</h1>
                <p className="page-subtitle">System configuration and preferences</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-lg)' }}>
                {/* Detection Thresholds */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Detection Thresholds</h2>
                    </div>
                    <div className="card-body">
                        <div className="form-group">
                            <label className="form-label">Crowd Density Threshold</label>
                            <input type="number" className="form-input" defaultValue={15} />
                            <small style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-xs)' }}>
                                Person count to trigger crowd alert
                            </small>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Loitering Duration (minutes)</label>
                            <input type="number" className="form-input" defaultValue={5} />
                            <small style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-xs)' }}>
                                Time before loitering alert triggers
                            </small>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Confidence Threshold (%)</label>
                            <input type="number" className="form-input" defaultValue={50} />
                            <small style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-xs)' }}>
                                Minimum confidence for detections
                            </small>
                        </div>
                        <button className="btn btn-primary">Save Thresholds</button>
                    </div>
                </div>

                {/* Privacy Settings */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Privacy Settings</h2>
                    </div>
                    <div className="card-body">
                        <div className="form-group">
                            <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', cursor: 'pointer' }}>
                                <input type="checkbox" defaultChecked />
                                <span>Enable face anonymization by default</span>
                            </label>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Blur Intensity</label>
                            <input type="range" min="11" max="99" step="2" defaultValue={51} className="form-input" style={{ padding: 0 }} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">De-anonymization Duration (minutes)</label>
                            <input type="number" className="form-input" defaultValue={5} />
                            <small style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-xs)' }}>
                                Maximum time for de-anonymized access
                            </small>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Data Retention (days)</label>
                            <input type="number" className="form-input" defaultValue={7} />
                            <small style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-xs)' }}>
                                Anonymized clips auto-delete after this period
                            </small>
                        </div>
                        <button className="btn btn-primary">Save Privacy Settings</button>
                    </div>
                </div>

                {/* Alert Settings */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Alert Settings</h2>
                    </div>
                    <div className="card-body">
                        <div className="form-group">
                            <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', cursor: 'pointer' }}>
                                <input type="checkbox" defaultChecked />
                                <span>Enable audio notifications</span>
                            </label>
                        </div>
                        <div className="form-group">
                            <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', cursor: 'pointer' }}>
                                <input type="checkbox" defaultChecked />
                                <span>Show desktop notifications</span>
                            </label>
                        </div>
                        <div className="form-group">
                            <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', cursor: 'pointer' }}>
                                <input type="checkbox" />
                                <span>Auto-escalate HIGH alerts after 2 minutes</span>
                            </label>
                        </div>
                        <button className="btn btn-primary">Save Alert Settings</button>
                    </div>
                </div>

                {/* System Info */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">System Information</h2>
                    </div>
                    <div className="card-body">
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-sm)' }}>
                            <span style={{ color: 'var(--text-muted)' }}>Version:</span>
                            <span>1.0.0 (Demo)</span>
                            <span style={{ color: 'var(--text-muted)' }}>Backend Status:</span>
                            <span style={{ color: 'var(--status-success)' }}>Connected</span>
                            <span style={{ color: 'var(--text-muted)' }}>ML Models:</span>
                            <span>YOLOv8n, MediaPipe</span>
                            <span style={{ color: 'var(--text-muted)' }}>Database:</span>
                            <span style={{ color: 'var(--status-success)' }}>Healthy</span>
                            <span style={{ color: 'var(--text-muted)' }}>Active Cameras:</span>
                            <span>8 / 8</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Settings

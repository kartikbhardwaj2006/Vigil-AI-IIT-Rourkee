function About() {
    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">About VIGIL</h1>
                <p className="page-subtitle">System information, ethics, and limitations</p>
            </div>

            {/* Purpose */}
            <div className="card mb-lg">
                <div className="card-header">
                    <h2 className="card-title">🎯 System Purpose</h2>
                </div>
                <div className="card-body">
                    <p style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-md)' }}>
                        VIGIL is a <strong>decision-support tool</strong> designed to assist human surveillance
                        operators by reducing cognitive fatigue and highlighting potential risk indicators.
                    </p>
                    <div className="disclaimer-banner" style={{ marginBottom: 0 }}>
                        <span className="disclaimer-icon">⚠️</span>
                        <div className="disclaimer-text">
                            <strong>This is NOT:</strong>
                            <ul style={{ margin: 'var(--spacing-sm) 0 0 var(--spacing-lg)', padding: 0 }}>
                                <li>A crime prediction system</li>
                                <li>A law enforcement tool</li>
                                <li>An automated decision maker</li>
                                <li>A facial recognition system</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-lg)' }}>
                {/* Ethical Principles */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">⚖️ Ethical Principles</h2>
                    </div>
                    <div className="card-body">
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                            {[
                                { icon: '🔒', title: 'Privacy by Default', desc: 'All video is anonymized. De-anonymization requires justification.' },
                                { icon: '👁️', title: 'Human-in-the-Loop', desc: 'No automated enforcement. All actions require human approval.' },
                                { icon: '📝', title: 'Full Explainability', desc: 'Every alert includes transparent reasoning.' },
                                { icon: '📋', title: 'Complete Audit Trail', desc: 'All actions are logged and reviewable.' },
                                { icon: '⚠️', title: 'Conservative Detection', desc: 'System errs on the side of caution and false positives.' }
                            ].map((item, i) => (
                                <li key={i} style={{
                                    display: 'flex',
                                    gap: 'var(--spacing-sm)',
                                    marginBottom: 'var(--spacing-md)',
                                    padding: 'var(--spacing-sm)',
                                    background: 'var(--bg-tertiary)',
                                    borderRadius: 'var(--border-radius-sm)'
                                }}>
                                    <span style={{ fontSize: '1.5rem' }}>{item.icon}</span>
                                    <div>
                                        <div style={{ fontWeight: 500 }}>{item.title}</div>
                                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                                            {item.desc}
                                        </div>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Known Limitations */}
                <div className="card" style={{ background: 'rgba(239, 68, 68, 0.05)', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
                    <div className="card-header">
                        <h2 className="card-title">⚠️ Known Limitations</h2>
                    </div>
                    <div className="card-body">
                        <ul style={{ margin: 0, paddingLeft: 'var(--spacing-lg)' }}>
                            {[
                                'Cannot determine intent or context of behaviors',
                                'May produce false positives (expected and by design)',
                                'Detection accuracy varies with lighting conditions',
                                'Performance degrades with camera distance',
                                'Pose estimation less accurate for partially occluded subjects',
                                'Crowd density calculation is approximate',
                                'Motion detection can be triggered by environmental factors',
                                'AI models may exhibit demographic bias',
                                'System requires calibration for accurate zone monitoring',
                                'Real-time performance depends on hardware capabilities'
                            ].map((limit, i) => (
                                <li key={i} style={{
                                    marginBottom: 'var(--spacing-sm)',
                                    color: 'var(--text-secondary)',
                                    fontSize: 'var(--font-size-sm)'
                                }}>
                                    {limit}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>

            {/* Bias Disclosure */}
            <div className="card mt-lg" style={{ background: 'rgba(245, 158, 11, 0.05)', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
                <div className="card-header">
                    <h2 className="card-title">🔬 Bias Awareness</h2>
                </div>
                <div className="card-body">
                    <p style={{ marginBottom: 'var(--spacing-md)' }}>
                        AI/ML systems, including those used in VIGIL, may exhibit biases. We are committed to
                        transparency about these limitations:
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--spacing-md)' }}>
                        <div style={{ padding: 'var(--spacing-md)', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)' }}>
                            <h4>Training Data Bias</h4>
                            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                                Pretrained models were trained on datasets that may not represent all demographics equally.
                            </p>
                        </div>
                        <div style={{ padding: 'var(--spacing-md)', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)' }}>
                            <h4>Environmental Factors</h4>
                            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                                Detection performance varies with lighting, clothing colors, and camera angles.
                            </p>
                        </div>
                        <div style={{ padding: 'var(--spacing-md)', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)' }}>
                            <h4>Behavioral Interpretation</h4>
                            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                                "Normal" behavior is context-dependent. The system cannot account for all cultural contexts.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Technical Stack */}
            <div className="card mt-lg">
                <div className="card-header">
                    <h2 className="card-title">🔧 Technical Stack</h2>
                </div>
                <div className="card-body">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--spacing-md)' }}>
                        <div>
                            <h4>Frontend</h4>
                            <ul style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', paddingLeft: 'var(--spacing-lg)' }}>
                                <li>React.js</li>
                                <li>React Router</li>
                                <li>Vanilla CSS</li>
                            </ul>
                        </div>
                        <div>
                            <h4>Backend</h4>
                            <ul style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', paddingLeft: 'var(--spacing-lg)' }}>
                                <li>FastAPI (Python)</li>
                                <li>SQLAlchemy</li>
                                <li>WebSocket</li>
                            </ul>
                        </div>
                        <div>
                            <h4>ML/CV</h4>
                            <ul style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', paddingLeft: 'var(--spacing-lg)' }}>
                                <li>YOLOv8 (Detection)</li>
                                <li>MediaPipe (Pose)</li>
                                <li>OpenCV</li>
                            </ul>
                        </div>
                        <div>
                            <h4>Data</h4>
                            <ul style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', paddingLeft: 'var(--spacing-lg)' }}>
                                <li>MySQL</li>
                                <li>Redis (Optional)</li>
                                <li>File Storage</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer Disclaimer */}
            <div className="card mt-lg" style={{ textAlign: 'center', background: 'var(--bg-tertiary)' }}>
                <div className="card-body">
                    <p style={{ fontSize: 'var(--font-size-lg)', fontWeight: 500, marginBottom: 'var(--spacing-sm)' }}>
                        VIGIL - Privacy-Preserving Intelligent Surveillance Decision-Support System
                    </p>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                        Built for Changethon, IIT Roorkee | Research-Grade Prototype<br />
                        This system is designed for educational and research purposes.
                    </p>
                </div>
            </div>
        </div>
    )
}

export default About

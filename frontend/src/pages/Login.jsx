import { useState } from 'react'

function Login({ onLogin }) {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        // Demo login - in production, this would call the API
        setTimeout(() => {
            if (username && password) {
                // Simulate successful login
                const token = 'demo-token-' + Date.now()
                const user = {
                    username,
                    role: username === 'supervisor' ? 'supervisor' : 'operator'
                }
                onLogin(user, token)
            } else {
                setError('Please enter username and password')
            }
            setLoading(false)
        }, 500)
    }

    return (
        <div className="login-container">
            <div className="card login-card">
                <div className="login-header">
                    <div className="login-logo">👁️</div>
                    <h1 className="login-title">VIGIL</h1>
                    <p className="login-subtitle">
                        Privacy-Preserving Intelligent Surveillance<br />
                        Decision-Support System
                    </p>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label" htmlFor="username">Username</label>
                        <input
                            id="username"
                            type="text"
                            className="form-input"
                            placeholder="Enter username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            className="form-input"
                            placeholder="Enter password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    {error && (
                        <div className="text-danger mb-md" style={{ fontSize: 'var(--font-size-sm)' }}>
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg"
                        style={{ width: '100%' }}
                        disabled={loading}
                    >
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>

                <div className="mt-lg" style={{ textAlign: 'center' }}>
                    <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                        Demo credentials: Any username/password<br />
                        Use "supervisor" as username for elevated access
                    </p>
                </div>

                <div className="disclaimer-banner mt-lg" style={{ marginBottom: 0 }}>
                    <span className="disclaimer-icon">🔒</span>
                    <div className="disclaimer-text" style={{ fontSize: 'var(--font-size-xs)' }}>
                        All actions are logged for accountability.
                        Unauthorized access is prohibited.
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Login

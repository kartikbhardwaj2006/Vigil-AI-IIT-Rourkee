import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import { useTheme } from './hooks/useTheme'
import Dashboard from './pages/Dashboard'
import LiveView from './pages/LiveView'
import Alerts from './pages/Alerts'
import AlertDetail from './pages/AlertDetail'
import Analytics from './pages/Analytics'
import AuditLog from './pages/AuditLog'
import Settings from './pages/Settings'
import About from './pages/About'
import Login from './pages/Login'

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [user, setUser] = useState(null)
    const theme = useTheme()

    useEffect(() => {
        // Check for existing token
        const token = localStorage.getItem('token')
        if (token) {
            setIsAuthenticated(true)
            // In production, validate token with backend
            setUser({ username: 'operator', role: 'operator' })
        }
    }, [])

    const handleLogin = (userData, token) => {
        localStorage.setItem('token', token)
        setIsAuthenticated(true)
        setUser(userData)
    }

    const handleLogout = () => {
        localStorage.removeItem('token')
        setIsAuthenticated(false)
        setUser(null)
    }

    if (!isAuthenticated) {
        return <Login onLogin={handleLogin} />
    }

    return (
        <Layout user={user} onLogout={handleLogout} theme={theme}>
            <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/live" element={<LiveView />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/alerts/:id" element={<AlertDetail />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/audit" element={<AuditLog user={user} />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/about" element={<About />} />
            </Routes>
        </Layout>
    )
}

export default App

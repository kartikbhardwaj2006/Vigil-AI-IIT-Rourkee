// API service for connecting frontend to backend
const API_BASE = '/api'
const STREAM_BASE = 'http://localhost:8000'

// Auth
export async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        body: formData
    })

    if (!response.ok) throw new Error('Login failed')
    return response.json()
}

export async function getCurrentUser(token) {
    const response = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('Failed to get user')
    return response.json()
}

// Cameras
export async function getCameras(token) {
    const response = await fetch(`${API_BASE}/cameras`, {
        headers: { Authorization: `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('Failed to get cameras')
    return response.json()
}

// Alerts
export async function getAlerts(token, params = {}) {
    const query = new URLSearchParams(params).toString()
    const response = await fetch(`${API_BASE}/alerts?${query}`, {
        headers: { Authorization: `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('Failed to get alerts')
    return response.json()
}

export async function getAlertDetail(token, alertId) {
    const response = await fetch(`${API_BASE}/alerts/${alertId}`, {
        headers: { Authorization: `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('Failed to get alert')
    return response.json()
}

export async function performAlertAction(token, alertId, action, notes = '') {
    const response = await fetch(`${API_BASE}/alerts/${alertId}/action`, {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action_type: action, notes })
    })
    if (!response.ok) throw new Error('Failed to perform action')
    return response.json()
}

// Analytics
export async function getDashboardStats(token) {
    const response = await fetch(`${API_BASE}/analytics/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('Failed to get stats')
    return response.json()
}

// Audit
export async function getAuditLogs(token, params = {}) {
    const query = new URLSearchParams(params).toString()
    const response = await fetch(`${API_BASE}/audit?${query}`, {
        headers: { Authorization: `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('Failed to get audit logs')
    return response.json()
}

export async function requestDeAnonymization(token, cameraId, justification, duration = 5) {
    const response = await fetch(`${API_BASE}/audit/de-anonymization-request`, {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            camera_id: cameraId,
            justification,
            duration_minutes: duration
        })
    })
    if (!response.ok) throw new Error('Failed to request de-anonymization')
    return response.json()
}

// WebSocket connection
export function connectToAlerts(onMessage, onError) {
    const ws = new WebSocket('ws://localhost:8000/ws/alerts')

    ws.onopen = () => {
        console.log('Connected to alert stream')
    }

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        onMessage(data)
    }

    ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (onError) onError(error)
    }

    ws.onclose = () => {
        console.log('Disconnected from alert stream')
        // Auto-reconnect after 5 seconds
        setTimeout(() => connectToAlerts(onMessage, onError), 5000)
    }

    return ws
}

// Privacy / Anonymization Controls (stream service)
export async function getPrivacyStatus() {
    const response = await fetch(`${STREAM_BASE}/api/stream/privacy`)
    if (!response.ok) throw new Error('Failed to get privacy status')
    return response.json()
}

export async function increaseBlur(step = 10) {
    const response = await fetch(`${STREAM_BASE}/api/stream/privacy/blur/increase?step=${step}`, {
        method: 'POST',
    })
    if (!response.ok) throw new Error('Failed to increase blur')
    return response.json()
}

export async function decreaseBlur(step = 10) {
    const response = await fetch(`${STREAM_BASE}/api/stream/privacy/blur/decrease?step=${step}`, {
        method: 'POST',
    })
    if (!response.ok) throw new Error('Failed to decrease blur')
    return response.json()
}

export async function setAnonymizationEnabled(enabled) {
    const response = await fetch(`${STREAM_BASE}/api/stream/privacy/anonymization?enabled=${enabled ? 'true' : 'false'}`, {
        method: 'POST',
    })
    if (!response.ok) {
        const text = await response.text()
        throw new Error(text || 'Failed to set anonymization')
    }
    return response.json()
}

export default {
    login,
    getCurrentUser,
    getCameras,
    getAlerts,
    getAlertDetail,
    performAlertAction,
    getDashboardStats,
    getAuditLogs,
    requestDeAnonymization,
    connectToAlerts,
    getPrivacyStatus,
    increaseBlur,
    decreaseBlur,
    setAnonymizationEnabled,
}

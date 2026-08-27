import { NavLink, useLocation } from 'react-router-dom'

function Layout({ children, user, onLogout, theme }) {
    const location = useLocation()

    const navItems = [
        {
            section: 'Overview', items: [
                { path: '/dashboard', icon: '▪', label: 'Dashboard' },
                { path: '/live', icon: '▪', label: 'Live View' },
            ]
        },
        {
            section: 'Monitoring', items: [
                { path: '/alerts', icon: '▪', label: 'Alerts' },
                { path: '/analytics', icon: '▪', label: 'Analytics' },
            ]
        },
        {
            section: 'System', items: [
                { path: '/audit', icon: '▪', label: 'Audit Log', roles: ['supervisor', 'auditor'] },
                { path: '/settings', icon: '▪', label: 'Settings' },
                { path: '/about', icon: '▪', label: 'About & Ethics' },
            ]
        },
    ]

    return (
        <div className="app-layout">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="logo">
                        <div className="logo-icon">V</div>
                        <span className="logo-text">VIGIL</span>
                    </div>
                    <div style={{ marginTop: 'var(--spacing-sm)' }}>
                        <span className="status-pill">
                            <span className="health-dot"></span>
                            DEPLOYMENT: BANK SECURITY
                        </span>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    {navItems.map((section) => (
                        <div key={section.section} className="nav-section">
                            <div className="nav-section-title">{section.section}</div>
                            {section.items
                                .filter(item => !item.roles || item.roles.includes(user?.role))
                                .map((item) => (
                                    <NavLink
                                        key={item.path}
                                        to={item.path}
                                        className={({ isActive }) =>
                                            `nav-link ${isActive ? 'active' : ''}`
                                        }
                                    >
                                        <span className="nav-link-icon">{item.icon}</span>
                                        <span>{item.label}</span>
                                    </NavLink>
                                ))
                            }
                        </div>
                    ))}
                </nav>

                <div className="sidebar-footer">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--spacing-sm)' }}>
                        <button className="theme-toggle" onClick={theme?.toggleTheme} type="button">
                            {theme?.isDark ? 'Dark' : 'Light'} Theme
                        </button>
                    </div>
                    <div className="user-info">
                        <div className="user-avatar">
                            {user?.username?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div className="user-details">
                            <div className="user-name">{user?.username || 'User'}</div>
                            <div className="user-role">{user?.role || 'Operator'}</div>
                        </div>
                        <button
                            className="btn btn-sm btn-secondary"
                            onClick={onLogout}
                            title="Logout"
                        >
                            Exit
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                {children}
            </main>
        </div>
    )
}

export default Layout

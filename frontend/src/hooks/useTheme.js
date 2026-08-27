import { useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'vigil.theme'

export function useTheme() {
    const [theme, setTheme] = useState(() => {
        const saved = localStorage.getItem(STORAGE_KEY)
        return saved === 'dark' || saved === 'light' ? saved : 'light'
    })

    useEffect(() => {
        document.documentElement.dataset.theme = theme
        localStorage.setItem(STORAGE_KEY, theme)
    }, [theme])

    const api = useMemo(() => {
        const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))
        return {
            theme,
            isDark: theme === 'dark',
            setTheme,
            toggleTheme,
        }
    }, [theme])

    return api
}


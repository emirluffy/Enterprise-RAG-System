/**
 * Theme Context - Multiple Theme System
 * Allows users to choose between different color themes
 */
import React, { createContext, useContext, useState, useEffect } from 'react'

interface Theme {
  id: string
  name: string
  displayName: string
  description: string
  background: string
  backgroundSecondary: string
  cardBackground: string
  headerBackground: string
  sidebarBackground: string
  buttonPrimary: string
  buttonSecondary: string
  textPrimary: string
  textSecondary: string
  textAccent: string
  borderColor: string
  accentColor: string
  glowPrimary: string
  glowSecondary: string
  glowTertiary: string
}

const themes: Theme[] = [
  {
    id: 'deep-ocean',
    name: 'deep-ocean',
    displayName: '🌊 Deep Ocean',
    description: 'Indigo purple with slate depths',
    background: 'from-indigo-950 via-purple-950 to-slate-950',
    backgroundSecondary: 'from-indigo-900/20 via-purple-900/10 to-slate-900/20',
    cardBackground: 'bg-white/5',
    headerBackground: 'bg-white/5',
    sidebarBackground: 'bg-white/5',
    buttonPrimary: 'from-blue-500 to-purple-500',
    buttonSecondary: 'from-purple-500 to-pink-500',
    textPrimary: 'text-white',
    textSecondary: 'text-white/70',
    textAccent: 'text-purple-300',
    borderColor: 'border-white/10',
    accentColor: 'text-blue-400',
    glowPrimary: 'bg-blue-500/10',
    glowSecondary: 'bg-purple-500/10',
    glowTertiary: 'bg-pink-500/5'
  },
  {
    id: 'twilight-dream',
    name: 'twilight-dream',
    displayName: '🌅 Twilight Dream',
    description: 'Beautiful blue-purple gradient (Login theme)',
    background: 'from-gray-900 via-blue-900 to-purple-900',
    backgroundSecondary: 'from-blue-900/20 via-purple-900/10 to-gray-900/20',
    cardBackground: 'bg-white/10',
    headerBackground: 'bg-white/10',
    sidebarBackground: 'bg-white/10',
    buttonPrimary: 'from-blue-500 to-purple-600',
    buttonSecondary: 'from-purple-600 to-blue-500',
    textPrimary: 'text-white',
    textSecondary: 'text-blue-200',
    textAccent: 'text-blue-300',
    borderColor: 'border-white/20',
    accentColor: 'text-blue-400',
    glowPrimary: 'bg-blue-500/15',
    glowSecondary: 'bg-purple-500/15',
    glowTertiary: 'bg-blue-400/10'
  },
  {
    id: 'emerald-forest',
    name: 'emerald-forest',
    displayName: '🌲 Emerald Forest',
    description: 'Deep greens with natural earth tones',
    background: 'from-emerald-950 via-green-950 to-teal-950',
    backgroundSecondary: 'from-emerald-900/20 via-green-900/10 to-teal-900/20',
    cardBackground: 'bg-white/5',
    headerBackground: 'bg-white/5',
    sidebarBackground: 'bg-white/5',
    buttonPrimary: 'from-emerald-500 to-teal-500',
    buttonSecondary: 'from-green-500 to-emerald-500',
    textPrimary: 'text-white',
    textSecondary: 'text-emerald-200',
    textAccent: 'text-emerald-300',
    borderColor: 'border-white/10',
    accentColor: 'text-emerald-400',
    glowPrimary: 'bg-emerald-500/10',
    glowSecondary: 'bg-teal-500/10',
    glowTertiary: 'bg-green-500/5'
  },
  {
    id: 'sunset-blaze',
    name: 'sunset-blaze',
    displayName: '🌅 Sunset Blaze',
    description: 'Warm oranges and reds like a sunset',
    background: 'from-orange-950 via-red-950 to-pink-950',
    backgroundSecondary: 'from-orange-900/20 via-red-900/10 to-pink-900/20',
    cardBackground: 'bg-white/5',
    headerBackground: 'bg-white/5',
    sidebarBackground: 'bg-white/5',
    buttonPrimary: 'from-orange-500 to-red-500',
    buttonSecondary: 'from-red-500 to-pink-500',
    textPrimary: 'text-white',
    textSecondary: 'text-orange-200',
    textAccent: 'text-orange-300',
    borderColor: 'border-white/10',
    accentColor: 'text-orange-400',
    glowPrimary: 'bg-orange-500/10',
    glowSecondary: 'bg-red-500/10',
    glowTertiary: 'bg-pink-500/5'
  },
  {
    id: 'cosmic-purple',
    name: 'cosmic-purple',
    displayName: '🌌 Cosmic Purple',
    description: 'Deep space purples with cosmic energy',
    background: 'from-purple-950 via-violet-950 to-indigo-950',
    backgroundSecondary: 'from-purple-900/20 via-violet-900/10 to-indigo-900/20',
    cardBackground: 'bg-white/5',
    headerBackground: 'bg-white/5',
    sidebarBackground: 'bg-white/5',
    buttonPrimary: 'from-purple-500 to-violet-500',
    buttonSecondary: 'from-violet-500 to-indigo-500',
    textPrimary: 'text-white',
    textSecondary: 'text-purple-200',
    textAccent: 'text-purple-300',
    borderColor: 'border-white/10',
    accentColor: 'text-purple-400',
    glowPrimary: 'bg-purple-500/10',
    glowSecondary: 'bg-violet-500/10',
    glowTertiary: 'bg-indigo-500/5'
  }
]

interface ThemeContextType {
  currentTheme: Theme
  setTheme: (themeId: string) => void
  themes: Theme[]
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [currentThemeId, setCurrentThemeId] = useState('twilight-dream')

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('enterprise-rag-theme')
    if (savedTheme && themes.find(t => t.id === savedTheme)) {
      setCurrentThemeId(savedTheme)
    }
  }, [])

  // Save theme to localStorage when changed
  useEffect(() => {
    localStorage.setItem('enterprise-rag-theme', currentThemeId)
  }, [currentThemeId])

  const setTheme = (themeId: string) => {
    const theme = themes.find(t => t.id === themeId)
    if (theme) {
      setCurrentThemeId(themeId)
    }
  }

  const currentTheme = themes.find(t => t.id === currentThemeId) || themes[0]

  return (
    <ThemeContext.Provider value={{
      currentTheme,
      setTheme,
      themes
    }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
} 
/**
 * Theme Selector Component
 * Beautiful UI for choosing between different color themes
 */
import React, { useState } from 'react'
import { useTheme } from '../../contexts/ThemeContext'

interface ThemeSelectorProps {
  isOpen: boolean
  onClose: () => void
}

export function ThemeSelector({ isOpen, onClose }: ThemeSelectorProps) {
  const { currentTheme, setTheme, themes } = useTheme()
  const [hoveredTheme, setHoveredTheme] = useState<string | null>(null)

  const handleThemeSelect = (themeId: string) => {
    setTheme(themeId)
    // Don't close immediately, let user see the change
    setTimeout(() => {
      onClose()
    }, 300)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div 
        className={`${currentTheme.cardBackground} backdrop-blur-xl ${currentTheme.borderColor} border rounded-2xl p-6 w-full max-w-2xl mx-4 shadow-2xl`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className={`text-2xl font-bold ${currentTheme.textPrimary}`}>
            🎨 Choose Your Theme
          </h2>
          <button
            onClick={onClose}
            className={`p-2 ${currentTheme.textSecondary} hover:${currentTheme.textPrimary} hover:bg-white/10 rounded-xl transition-all`}
          >
            ✕
          </button>
        </div>

        {/* Current Theme Info */}
        <div className={`${currentTheme.cardBackground} rounded-xl p-4 mb-6 ${currentTheme.borderColor} border`}>
          <div className="flex items-center space-x-3">
            <div className={`w-8 h-8 bg-gradient-to-r ${currentTheme.buttonPrimary} rounded-lg`}></div>
            <div>
              <div className={`font-semibold ${currentTheme.textPrimary}`}>
                Current: {currentTheme.displayName}
              </div>
              <div className={`text-sm ${currentTheme.textSecondary}`}>
                {currentTheme.description}
              </div>
            </div>
          </div>
        </div>

        {/* Theme Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
          {themes.map((theme) => (
            <div
              key={theme.id}
              className={`
                relative group cursor-pointer transition-all duration-300 transform hover:scale-105
                ${theme.id === currentTheme.id ? 'ring-2 ring-white/50' : ''}
                ${hoveredTheme === theme.id ? 'shadow-xl' : 'shadow-lg'}
              `}
              onClick={() => handleThemeSelect(theme.id)}
              onMouseEnter={() => setHoveredTheme(theme.id)}
              onMouseLeave={() => setHoveredTheme(null)}
            >
              {/* Theme Preview Card */}
              <div className={`bg-gradient-to-br ${theme.background} rounded-xl p-4 border ${theme.borderColor} overflow-hidden`}>
                {/* Mini Background Elements */}
                <div className="absolute inset-0">
                  <div className={`absolute top-2 left-2 w-8 h-8 ${theme.glowPrimary} rounded-full blur-md`}></div>
                  <div className={`absolute bottom-2 right-2 w-6 h-6 ${theme.glowSecondary} rounded-full blur-md`}></div>
                </div>

                {/* Content Preview */}
                <div className="relative z-10">
                  {/* Theme Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className={`w-6 h-6 bg-gradient-to-r ${theme.buttonPrimary} rounded-lg`}></div>
                    <div className={`text-xs ${theme.textSecondary}`}>●●●</div>
                  </div>

                  {/* Theme Name */}
                  <div className={`font-bold ${theme.textPrimary} mb-1`}>
                    {theme.displayName}
                  </div>
                  <div className={`text-xs ${theme.textSecondary} mb-3`}>
                    {theme.description}
                  </div>

                  {/* Mock UI Elements */}
                  <div className="space-y-2">
                    <div className={`h-2 ${theme.cardBackground} rounded opacity-60`}></div>
                    <div className={`h-2 ${theme.cardBackground} rounded w-3/4 opacity-40`}></div>
                    <div className={`h-1.5 bg-gradient-to-r ${theme.buttonPrimary} rounded w-1/2 mt-2`}></div>
                  </div>
                </div>

                {/* Selected Indicator */}
                {theme.id === currentTheme.id && (
                  <div className="absolute top-2 right-2">
                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs">✓</span>
                    </div>
                  </div>
                )}

                {/* Hover Effect */}
                {hoveredTheme === theme.id && (
                  <div className="absolute inset-0 bg-white/5 rounded-xl"></div>
                )}
              </div>

              {/* Theme Label */}
              <div className="text-center mt-2">
                <div className={`text-sm font-medium ${currentTheme.textPrimary}`}>
                  {theme.displayName}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className={`mt-6 text-center ${currentTheme.textSecondary} text-sm`}>
          <p>Theme preferences are saved automatically</p>
        </div>
      </div>
    </div>
  )
}

// Floating Theme Button Component
export function ThemeButton() {
  const { currentTheme } = useTheme()
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className={`
          fixed bottom-6 right-6 z-40
          w-14 h-14 bg-gradient-to-r ${currentTheme.buttonPrimary} 
          rounded-full shadow-lg hover:shadow-xl
          flex items-center justify-center
          transform hover:scale-110 transition-all duration-300
          ${currentTheme.borderColor} border
        `}
        title="Change Theme"
      >
        <span className="text-white text-xl">🎨</span>
      </button>

      <ThemeSelector 
        isOpen={isOpen} 
        onClose={() => setIsOpen(false)} 
      />
    </>
  )
} 
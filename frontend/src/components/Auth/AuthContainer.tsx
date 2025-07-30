/**
 * Enterprise RAG System - Auth Container Component
 * Manages switching between login and register forms
 */
import React, { useState } from 'react'
import { LoginForm } from './LoginForm'
import { RegisterForm } from './RegisterForm'

interface AuthContainerProps {
  onSuccess?: () => void
  defaultView?: 'login' | 'register'
}

export function AuthContainer({ onSuccess, defaultView = 'login' }: AuthContainerProps) {
  const [currentView, setCurrentView] = useState<'login' | 'register'>(defaultView)

  const handleSuccess = () => {
    if (onSuccess) {
      onSuccess()
    }
  }

  const switchToLogin = () => {
    setCurrentView('login')
  }

  const switchToRegister = () => {
    setCurrentView('register')
  }

  if (currentView === 'register') {
    return (
      <RegisterForm
        onSuccess={handleSuccess}
        onSwitchToLogin={switchToLogin}
      />
    )
  }

  return (
    <LoginForm
      onSuccess={handleSuccess}
      onSwitchToRegister={switchToRegister}
    />
  )
} 
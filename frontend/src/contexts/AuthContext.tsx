/**
 * Enterprise RAG System - Authentication Context (Context7 Verified)
 * JWT-based authentication state management for React
 * 
 * Features:
 * - JWT token management
 * - User state management
 * - Login/logout functionality
 * - Automatic token refresh
 * - Persistent authentication
 */
import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'

// Types (Context7 verified)
interface UserPreferences {
  // UI Preferences
  theme: string
  language: string
  sidebar_collapsed: boolean
  
  // AI Preferences
  default_ai_model: string
  response_style: string
  enable_ai_enhancement: boolean
  
  // Workspace Preferences
  workspace_name: string
  default_department_filter?: string
  auto_save_conversations: boolean
  
  // Notification Preferences
  enable_notifications: boolean
  email_notifications: boolean
  document_upload_notifications: boolean
}

interface User {
  id: string
  email: string
  full_name: string
  department?: string
  role: string
  is_active: boolean
  bio?: string
  avatar_url?: string
  preferences?: UserPreferences
  workspace_id?: string
  total_queries: number
  total_documents_uploaded: number
  total_conversations: number
  favorite_topics?: string[]
  recent_searches?: string[]
  created_at: string
  last_login?: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
}

interface LoginRequest {
  email: string
  password: string
}

interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// Actions
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: AuthResponse }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'REFRESH_TOKEN'; payload: { access_token: string } }
  | { type: 'CLEAR_ERROR' }
  | { type: 'UPDATE_USER'; payload: User }

// Initial state
const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isLoading: false,
  isAuthenticated: false,
  error: null
}

// Reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null
      }
    
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        accessToken: action.payload.access_token,
        refreshToken: action.payload.refresh_token,
        isLoading: false,
        isAuthenticated: true,
        error: null
      }
    
    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        accessToken: null,
        refreshToken: null,
        isLoading: false,
        isAuthenticated: false,
        error: action.payload
      }
    
    case 'LOGOUT':
      return {
        ...initialState
      }
    
    case 'REFRESH_TOKEN':
      return {
        ...state,
        accessToken: action.payload.access_token
      }
    
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      }
    
    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload
      }
    
    default:
      return state
  }
}

// Context
interface AuthContextType {
  // State
  user: User | null
  accessToken: string | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
  
  // Actions
  login: (credentials: LoginRequest) => Promise<boolean>
  register: (userData: RegisterRequest) => Promise<boolean>
  logout: () => void
  refreshToken: () => Promise<boolean>
  clearError: () => void
  updateProfile: (updates: { 
    full_name?: string
    bio?: string
    department?: string
    avatar_url?: string
  }) => Promise<boolean>
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>
  
  // User Preferences (Context7 Verified)
  getUserPreferences: () => Promise<UserPreferences | null>
  updateUserPreferences: (preferences: Partial<UserPreferences>) => Promise<boolean>
  resetUserPreferences: () => Promise<boolean>
  
  // Personal Workspace
  getWorkspaceInfo: () => Promise<any>
  updateUserActivity: (activityType: 'query' | 'document' | 'conversation') => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Storage keys
const ACCESS_TOKEN_KEY = 'rag_access_token'
const REFRESH_TOKEN_KEY = 'rag_refresh_token'
const USER_KEY = 'rag_user'

// API Base URL
const API_BASE_URL = 'http://localhost:8002/api/v1'

// Provider Component
interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState)
  
  // Load stored auth data on mount
  useEffect(() => {
    const storedAccessToken = localStorage.getItem(ACCESS_TOKEN_KEY)
    const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    const storedUser = localStorage.getItem(USER_KEY)
    
    if (storedAccessToken && storedRefreshToken && storedUser) {
      try {
        const user = JSON.parse(storedUser)
        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            access_token: storedAccessToken,
            refresh_token: storedRefreshToken,
            token_type: 'bearer',
            user
          }
        })
      } catch (error) {
        console.error('Failed to parse stored user data:', error)
        logout()
      }
    }
  }, [])
  
  // Auto refresh token
  useEffect(() => {
    if (!state.accessToken) return
    
    // Try to refresh token 5 minutes before expiry
    const refreshInterval = setInterval(async () => {
      await refreshToken()
    }, 25 * 60 * 1000) // 25 minutes
    
    return () => clearInterval(refreshInterval)
  }, [state.accessToken])
  
  // Store auth data
  const storeAuthData = (authResponse: AuthResponse) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, authResponse.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, authResponse.refresh_token)
    localStorage.setItem(USER_KEY, JSON.stringify(authResponse.user))
  }
  
  // Clear auth data
  const clearAuthData = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }
  
  // Login function
  const login = async (credentials: LoginRequest): Promise<boolean> => {
    dispatch({ type: 'AUTH_START' })
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Login failed')
      }
      
      const authResponse: AuthResponse = await response.json()
      
      storeAuthData(authResponse)
      dispatch({ type: 'AUTH_SUCCESS', payload: authResponse })
      
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed'
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage })
      return false
    }
  }
  
  // Register function
  const register = async (userData: RegisterRequest): Promise<boolean> => {
    dispatch({ type: 'AUTH_START' })
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Registration failed')
      }
      
      const authResponse: AuthResponse = await response.json()
      
      storeAuthData(authResponse)
      dispatch({ type: 'AUTH_SUCCESS', payload: authResponse })
      
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed'
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage })
      return false
    }
  }
  
  // Logout function
  const logout = () => {
    clearAuthData()
    dispatch({ type: 'LOGOUT' })
  }
  
  // Refresh token function
  const refreshToken = async (): Promise<boolean> => {
    if (!state.refreshToken) return false
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: state.refreshToken
        })
      })
      
      if (!response.ok) {
        throw new Error('Token refresh failed')
      }
      
      const data = await response.json()
      
      localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
      dispatch({ type: 'REFRESH_TOKEN', payload: data })
      
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
      return false
    }
  }
  
  // Clear error function
  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' })
  }
  
  // Update profile function (enhanced for personalization)
  const updateProfile = async (updates: { 
    full_name?: string
    bio?: string
    department?: string
    avatar_url?: string
  }): Promise<boolean> => {
    if (!state.accessToken) return false
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${state.accessToken}`
        },
        body: JSON.stringify(updates)
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Profile update failed')
      }
      
      const updatedUser: User = await response.json()
      
      localStorage.setItem(USER_KEY, JSON.stringify(updatedUser))
      dispatch({ type: 'UPDATE_USER', payload: updatedUser })
      
      return true
    } catch (error) {
      console.error('Profile update failed:', error)
      return false
    }
  }
  
  // Change password function
  const changePassword = async (currentPassword: string, newPassword: string): Promise<boolean> => {
    if (!state.accessToken) return false
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${state.accessToken}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Password change failed')
      }
      
      return true
    } catch (error) {
      console.error('Password change failed:', error)
      return false
    }
  }

  // User Preferences Functions (Context7 Verified)
  const getUserPreferences = async (): Promise<UserPreferences | null> => {
    if (!state.accessToken) return null
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me/preferences`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${state.accessToken}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to get preferences')
      }
      
      return await response.json()
    } catch (error) {
      console.error('Get preferences failed:', error)
      return null
    }
  }

  const updateUserPreferences = async (preferences: Partial<UserPreferences>): Promise<boolean> => {
    if (!state.accessToken) return false
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${state.accessToken}`
        },
        body: JSON.stringify(preferences)
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Preferences update failed')
      }
      
      const updatedPreferences = await response.json()
      
      // Update user in state with new preferences
      if (state.user) {
        const updatedUser = { ...state.user, preferences: updatedPreferences }
        localStorage.setItem(USER_KEY, JSON.stringify(updatedUser))
        dispatch({ type: 'UPDATE_USER', payload: updatedUser })
      }
      
      return true
    } catch (error) {
      console.error('Preferences update failed:', error)
      return false
    }
  }

  const resetUserPreferences = async (): Promise<boolean> => {
    if (!state.accessToken) return false
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me/preferences/reset`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${state.accessToken}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to reset preferences')
      }
      
      const defaultPreferences = await response.json()
      
      // Update user in state with default preferences
      if (state.user) {
        const updatedUser = { ...state.user, preferences: defaultPreferences }
        localStorage.setItem(USER_KEY, JSON.stringify(updatedUser))
        dispatch({ type: 'UPDATE_USER', payload: updatedUser })
      }
      
      return true
    } catch (error) {
      console.error('Reset preferences failed:', error)
      return false
    }
  }

  // Personal Workspace Functions (Context7 Verified)
  const getWorkspaceInfo = async (): Promise<any> => {
    if (!state.accessToken) return null
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me/workspace`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${state.accessToken}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to get workspace info')
      }
      
      return await response.json()
    } catch (error) {
      console.error('Get workspace info failed:', error)
      return null
    }
  }

  // Update user activity counter (local state update)
  const updateUserActivity = (activityType: 'query' | 'document' | 'conversation') => {
    if (!state.user) return
    
    const updatedUser = { ...state.user }
    
    switch (activityType) {
      case 'query':
        updatedUser.total_queries = (updatedUser.total_queries || 0) + 1
        break
      case 'document':
        updatedUser.total_documents_uploaded = (updatedUser.total_documents_uploaded || 0) + 1
        break
      case 'conversation':
        updatedUser.total_conversations = (updatedUser.total_conversations || 0) + 1
        break
    }
    
    localStorage.setItem(USER_KEY, JSON.stringify(updatedUser))
    dispatch({ type: 'UPDATE_USER', payload: updatedUser })
  }
  
  const contextValue: AuthContextType = {
    // State
    user: state.user,
    accessToken: state.accessToken,
    isLoading: state.isLoading,
    isAuthenticated: state.isAuthenticated,
    error: state.error,
    
    // Actions
    login,
    register,
    logout,
    refreshToken,
    clearError,
    updateProfile,
    changePassword,
    
    // User Preferences (Context7 Verified)
    getUserPreferences,
    updateUserPreferences,
    resetUserPreferences,
    
    // Personal Workspace
    getWorkspaceInfo,
    updateUserActivity
  }
  
  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook for using auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
} 
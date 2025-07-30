/**
 * Enterprise RAG System - User Profile Modal Component (Context7 Verified)
 * Complete user profile and preferences management with beautiful UI
 * 
 * Features:
 * - Personal profile editing
 * - User preferences management
 * - Workspace settings
 * - Activity overview
 * - Theme customization
 */
import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'

interface UserProfileModalProps {
  isOpen: boolean
  onClose: () => void
}

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

export function UserProfileModal({ isOpen, onClose }: UserProfileModalProps) {
  const { 
    user, 
    updateProfile, 
    getUserPreferences, 
    updateUserPreferences, 
    resetUserPreferences,
    getWorkspaceInfo 
  } = useAuth()

  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'workspace'>('profile')
  const [isLoading, setIsLoading] = useState(false)
  const [preferences, setPreferences] = useState<UserPreferences | null>(null)
  const [workspaceInfo, setWorkspaceInfo] = useState<any>(null)
  
  // Profile form state
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || '',
    bio: user?.bio || '',
    department: user?.department || '',
    avatar_url: user?.avatar_url || ''
  })

  // Load user preferences and workspace info
  useEffect(() => {
    if (isOpen && user) {
      loadUserData()
    }
  }, [isOpen, user])

  const loadUserData = async () => {
    setIsLoading(true)
    try {
      const [prefs, workspace] = await Promise.all([
        getUserPreferences(),
        getWorkspaceInfo()
      ])
      
      if (prefs) setPreferences(prefs)
      if (workspace) setWorkspaceInfo(workspace)
    } catch (error) {
      console.error('Failed to load user data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      const success = await updateProfile(profileForm)
      if (success) {
        // Profile updated successfully
      }
    } catch (error) {
      console.error('Profile update failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handlePreferencesUpdate = async (updates: Partial<UserPreferences>) => {
    if (!preferences) return
    
    setIsLoading(true)
    try {
      const success = await updateUserPreferences(updates)
      if (success) {
        setPreferences({ ...preferences, ...updates })
      }
    } catch (error) {
      console.error('Preferences update failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleResetPreferences = async () => {
    setIsLoading(true)
    try {
      const success = await resetUserPreferences()
      if (success) {
        // Reload preferences after reset
        await loadUserData()
      }
    } catch (error) {
      console.error('Reset preferences failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-lg">
                {user?.full_name?.charAt(0) || 'U'}
              </span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Kullanıcı Profili</h2>
              <p className="text-gray-400 text-sm">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex">
          {/* Sidebar */}
          <div className="w-64 bg-gray-900 border-r border-gray-700">
            <nav className="p-4">
              <button
                onClick={() => setActiveTab('profile')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors mb-2 ${
                  activeTab === 'profile' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span>Profil Bilgileri</span>
              </button>
              
              <button
                onClick={() => setActiveTab('preferences')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors mb-2 ${
                  activeTab === 'preferences' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>Tercihler</span>
              </button>
              
              <button
                onClick={() => setActiveTab('workspace')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors mb-2 ${
                  activeTab === 'workspace' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <span>Çalışma Alanı</span>
              </button>
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
            {isLoading && (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              </div>
            )}

            {!isLoading && activeTab === 'profile' && (
              <ProfileTab 
                profileForm={profileForm}
                setProfileForm={setProfileForm}
                onSubmit={handleProfileUpdate}
                user={user}
              />
            )}

            {!isLoading && activeTab === 'preferences' && preferences && (
              <PreferencesTab 
                preferences={preferences}
                onUpdate={handlePreferencesUpdate}
                onReset={handleResetPreferences}
              />
            )}

            {!isLoading && activeTab === 'workspace' && workspaceInfo && (
              <WorkspaceTab workspaceInfo={workspaceInfo} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Profile Tab Component
function ProfileTab({ profileForm, setProfileForm, onSubmit, user }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Profil Bilgileri</h3>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-400 text-sm font-medium mb-2">
              Ad Soyad
            </label>
            <input
              type="text"
              value={profileForm.full_name}
              onChange={(e) => setProfileForm((prev: any) => ({ ...prev, full_name: e.target.value }))}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-gray-400 text-sm font-medium mb-2">
              Biyografi
            </label>
            <textarea
              value={profileForm.bio}
              onChange={(e) => setProfileForm((prev: any) => ({ ...prev, bio: e.target.value }))}
              rows={3}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              placeholder="Kendiniz hakkında kısa bilgi..."
            />
          </div>
          
          <div>
            <label className="block text-gray-400 text-sm font-medium mb-2">
              Departman
            </label>
            <input
              type="text"
              value={profileForm.department}
              onChange={(e) => setProfileForm((prev: any) => ({ ...prev, department: e.target.value }))}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          
          <div className="flex items-center justify-between pt-4">
            <div className="text-sm text-gray-400">
              <p>Rol: <span className="text-white font-medium">{user?.role}</span></p>
              <p>Üyelik: <span className="text-white font-medium">
                {new Date(user?.created_at).toLocaleDateString('tr-TR')}
              </span></p>
            </div>
            
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
            >
              Profili Güncelle
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Preferences Tab Component
function PreferencesTab({ preferences, onUpdate, onReset }: any) {
  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Kullanıcı Tercihleri</h3>
        
        {/* UI Preferences */}
        <div className="bg-gray-900 rounded-lg p-4 mb-6">
          <h4 className="text-white font-medium mb-4">Arayüz Ayarları</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-gray-400 text-sm font-medium mb-2">
                Tema
              </label>
              <select
                value={preferences.theme}
                onChange={(e) => onUpdate({ theme: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="twilight-dream">Twilight Dream</option>
                <option value="ocean-blue">Ocean Blue</option>
                <option value="forest-green">Forest Green</option>
                <option value="sunset-orange">Sunset Orange</option>
              </select>
            </div>
            
            <div>
              <label className="block text-gray-400 text-sm font-medium mb-2">
                Dil
              </label>
              <select
                value={preferences.language}
                onChange={(e) => onUpdate({ language: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="tr">Türkçe</option>
                <option value="en">English</option>
              </select>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Sidebar varsayılan olarak kapalı</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.sidebar_collapsed}
                  onChange={(e) => onUpdate({ sidebar_collapsed: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* AI Preferences */}
        <div className="bg-gray-900 rounded-lg p-4 mb-6">
          <h4 className="text-white font-medium mb-4">AI Ayarları</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-gray-400 text-sm font-medium mb-2">
                Varsayılan AI Model
              </label>
              <select
                value={preferences.default_ai_model}
                onChange={(e) => onUpdate({ default_ai_model: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash Lite</option>
                <option value="gpt-4">GPT-4</option>
                <option value="claude-3">Claude 3</option>
              </select>
            </div>
            
            <div>
              <label className="block text-gray-400 text-sm font-medium mb-2">
                Yanıt Stili
              </label>
              <select
                value={preferences.response_style}
                onChange={(e) => onUpdate({ response_style: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="detailed">Detaylı</option>
                <option value="concise">Özet</option>
                <option value="technical">Teknik</option>
              </select>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">AI Enhancement aktif</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.enable_ai_enhancement}
                  onChange={(e) => onUpdate({ enable_ai_enhancement: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Workspace Preferences */}
        <div className="bg-gray-900 rounded-lg p-4 mb-6">
          <h4 className="text-white font-medium mb-4">Çalışma Alanı</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-gray-400 text-sm font-medium mb-2">
                Çalışma Alanı Adı
              </label>
              <input
                type="text"
                value={preferences.workspace_name}
                onChange={(e) => onUpdate({ workspace_name: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Konuşmaları otomatik kaydet</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.auto_save_conversations}
                  onChange={(e) => onUpdate({ auto_save_conversations: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Notification Preferences */}
        <div className="bg-gray-900 rounded-lg p-4 mb-6">
          <h4 className="text-white font-medium mb-4">Bildirim Ayarları</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Bildirimler aktif</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.enable_notifications}
                  onChange={(e) => onUpdate({ enable_notifications: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">E-posta bildirimleri</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.email_notifications}
                  onChange={(e) => onUpdate({ email_notifications: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Döküman yükleme bildirimleri</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.document_upload_notifications}
                  onChange={(e) => onUpdate({ document_upload_notifications: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            onClick={onReset}
            className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Varsayılana Sıfırla
          </button>
        </div>
      </div>
    </div>
  )
}

// Workspace Tab Component
function WorkspaceTab({ workspaceInfo }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Çalışma Alanı Bilgileri</h3>
        
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{workspaceInfo?.total_queries || 0}</p>
                <p className="text-gray-400 text-sm">Toplam Sorgu</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{workspaceInfo?.total_documents || 0}</p>
                <p className="text-gray-400 text-sm">Döküman</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{workspaceInfo?.total_conversations || 0}</p>
                <p className="text-gray-400 text-sm">Konuşma</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-orange-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-white font-medium">
                  {workspaceInfo?.last_activity ? 
                    new Date(workspaceInfo.last_activity).toLocaleDateString('tr-TR') :
                    'Hiç'
                  }
                </p>
                <p className="text-gray-400 text-sm">Son Aktivite</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 bg-gray-900 rounded-lg p-4">
          <h4 className="text-white font-medium mb-4">Çalışma Alanı Detayları</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400">Çalışma Alanı ID:</span>
              <span className="text-white font-mono text-sm">{workspaceInfo?.workspace_id || 'Atanmamış'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Çalışma Alanı Adı:</span>
              <span className="text-white">{workspaceInfo?.workspace_name || 'Kişisel Çalışma Alanı'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Üyelik Tarihi:</span>
              <span className="text-white">
                {workspaceInfo?.member_since ? 
                  new Date(workspaceInfo.member_since).toLocaleDateString('tr-TR') :
                  'Bilinmiyor'
                }
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 
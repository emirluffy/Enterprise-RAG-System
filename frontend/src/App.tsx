import React, { useState, useEffect, useRef, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import './index.css'

// Authentication imports (Context7 verified)
import { useAuth } from './contexts/AuthContext'
import { AuthContainer } from './components/Auth'

// Theme system
import { useTheme } from './contexts/ThemeContext'
import { ThemeButton } from './components/Theme/ThemeSelector'

// WebSocket notifications (Context7 verified)
import WebSocketNotifications from './components/WebSocketNotifications'
import { useWebSocketService } from './hooks/useWebSocketService';



// Phase 5.3: Real-time Collaboration component
import RealtimeCollaboration from './components/Collaboration/RealtimeCollaboration'

// User Profile Modal (Context7 Verified)
import { UserProfileModal } from './components/UserProfile'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api/v1'

// Graph Explorer removed

// Context7 verified React-Uploady imports
import Uploady, { 
  useItemProgressListener, 
  useItemFinishListener, 
  useItemStartListener,
  useBatchStartListener,
  useRequestPreSend
} from "@rpldy/uploady"
import UploadDropZone from "@rpldy/upload-drop-zone"
import UploadButton from "@rpldy/upload-button"

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Array<{
    source: string
    page: string | number
    score: number
    chunk_id: string
  }>
  documents_found?: number
  has_context?: boolean
  confidence?: number
  response_time_ms?: number
  // AI Intelligence fields (Context7 verified)
  related_questions?: string[]
  document_recommendations?: Array<{
    id: string
    title: string
    file_type: string
    content_preview?: string
    relevance_reason: string
  }>
  ai_intelligence_enabled?: boolean
}

interface UploadStatus {
  uploading: boolean
  success: boolean
  error?: string
  filename?: string
  details?: any
}

interface Document {
  id: string
  title: string
  filename: string
  category: string
  upload_date: string
  processed_at: string
  chunks_created: number
  text_length: number
  status: string
}

interface UploadResult {
  filename: string
  status: string
  chunks_created: number
  text_length: number
  file_size: number
  content_type: string
}

interface BatchUploadResponse {
  message: string
  successful_uploads: number
  failed_uploads: number
  results: UploadResult[]
  failures?: Array<{
    filename: string
    error: string
  }>
}



// Context7 verified Multi-Upload Progress Component
const MultiUploadProgress: React.FC = () => {
  const [uploadItems, setUploadItems] = useState<Array<{
    id: string
    filename: string
    progress: number
    status: 'uploading' | 'completed' | 'error'
    error?: string
  }>>([])

  useItemStartListener((item) => {
    console.log('🚀 Item started:', item.id, item.file.name)
    setUploadItems(prev => [...prev, {
      id: item.id,
      filename: item.file.name,
      progress: 0,
      status: 'uploading'
    }])
  })

  useBatchStartListener((batch) => {
    console.log('📦 Batch started:', batch.id, 'items:', batch.items.length)
    batch.items.forEach(item => {
      console.log('  📄 Item:', item.file.name, 'size:', item.file.size)
    })
  })

  useRequestPreSend(({ items, options }) => {
    console.log('🔍 DEBUG - Request Pre-Send:')
    console.log('  Options:', options)
    console.log('  Items count:', items.length)
    console.log('  Destination:', options.destination)
    items.forEach((item, i) => {
      console.log(`  File ${i+1}:`, item.file.name, item.file.type, item.file.size)
    })
    // Return nothing to proceed normally
  })

  useItemProgressListener((item) => {
    setUploadItems(prev => prev.map(upload => 
      upload.id === item.id 
        ? { ...upload, progress: item.completed }
        : upload
    ))
  })

  useItemFinishListener((item) => {
    console.log('✅ Item finished:', item.id, 'status:', item.uploadStatus)
    setUploadItems(prev => prev.map(upload => 
      upload.id === item.id 
        ? { 
            ...upload, 
            progress: 100, 
            status: item.uploadStatus === 200 ? 'completed' : 'error',
            error: item.uploadStatus !== 200 ? 'Upload failed' : undefined
          }
        : upload
    ))
  })

  if (uploadItems.length === 0) return null

  return (
    <div className="fixed bottom-6 right-6 w-80 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-4 shadow-2xl z-50">
      <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
        <span className="animate-spin mr-2">⚡</span>
        Upload Progress
      </h3>
      <div className="space-y-3 max-h-60 overflow-y-auto">
        {uploadItems.map((item) => (
          <div key={item.id} className="bg-white/5 rounded-xl p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/80 truncate flex-1 mr-2">
                {item.filename}
              </span>
              <span className="text-xs text-white/60">
                {item.status === 'completed' ? '✅' : 
                 item.status === 'error' ? '❌' : 
                 `${item.progress}%`}
              </span>
            </div>
            {item.status === 'uploading' && (
              <div className="w-full bg-white/10 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${item.progress}%` }}
                />
              </div>
            )}
            {item.error && (
              <p className="text-xs text-red-400 mt-1">{item.error}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function App() {
  // Authentication (Context7 verified)
  const { isAuthenticated, isLoading: authLoading, user, logout } = useAuth()

  // Show auth screen if not authenticated
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <AuthContainer />
  }

  // Main Chat Application (existing functionality)
  return <AuthenticatedApp user={user} onLogout={logout} />
}

// Separate component for authenticated users
function AuthenticatedApp({ user, onLogout }: { user: any, onLogout: () => void }) {
  // Authentication hook (Context7 verified)
  const auth = useAuth()
  
  // Theme hook
  const { currentTheme } = useTheme()
  
  // WebSocket service hook (Context7 verified)
  const {
    isConnected,
    connectionStatus,
    activeUsers
  } = useWebSocketService();

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'library' | 'collaboration'>('chat')
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ uploading: false, success: false })
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoadingDocs, setIsLoadingDocs] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  


  // Real Conversation Management
  const [conversations, setConversations] = useState<any[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [isLoadingConversations, setIsLoadingConversations] = useState(false)
  const [sessionId] = useState<string>(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  
  // ChatGPT-style sidebar state
  const [showSidebar, setShowSidebar] = useState(true)
  
  // User Profile Modal state (Context7 Verified)
  const [showUserProfile, setShowUserProfile] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Context7 verified Multi-Upload Configuration
  const uploadDestination = {
    url: `${API_BASE_URL}/documents/upload-multiple`,
    method: "POST" as const,
    headers: {
      'Authorization': `Bearer ${auth.accessToken}`
    },
    filesParamName: "files"
  }

  // Context7 verified Batch Upload Success Handler
  const handleBatchUploadSuccess = useCallback((response: BatchUploadResponse) => {
    console.log('Batch upload completed:', response)
    
    // Show success notification
    const successMessage: Message = {
      id: uuidv4(),
      type: 'assistant',
      content: `✅ **Multi-file Upload Completed**\n\n` +
        `📊 **Results:**\n` +
        `• ✅ Successfully uploaded: ${response.successful_uploads} files\n` +
        `• ❌ Failed uploads: ${response.failed_uploads} files\n\n` +
        `📄 **Processed Files:**\n` +
        response.results.map(r => 
          `• **${r.filename}** - ${r.chunks_created} chunks, ${(r.file_size / 1024).toFixed(1)}KB`
        ).join('\n') +
        (response.failures ? '\n\n❌ **Failed Files:**\n' + 
          response.failures.map(f => `• ${f.filename}: ${f.error}`).join('\n') : '') +
        '\n\n🔍 All files are now searchable in the chat!',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, successMessage])
    
    // Track user activity (Context7 verified)
    auth.updateUserActivity('document')
    
    // Refresh document library if open
    if (activeTab === 'library') {
      fetchDocuments()
    }
  }, [activeTab])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  React.useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Fetch documents for library (Context7 verified user-specific filtering)
  const fetchDocuments = async () => {
    setIsLoadingDocs(true)
    try {
      const response = await fetch(`${API_BASE_URL}/documents/library`, {
        headers: {
          'Authorization': `Bearer ${auth.accessToken}`
        }
      })
      const data = await response.json()
      setDocuments(data.documents || [])
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setIsLoadingDocs(false)
    }
  }





  // Delete document function
  const deleteDocument = async (document: Document) => {
    const confirmed = window.confirm(`Are you sure you want to delete "${document.title}"?\n\nThis action cannot be undone.`)
    if (!confirmed) return

    try {
      const response = await fetch(`${API_BASE_URL}/documents/document/${encodeURIComponent(document.id)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${auth.accessToken}`
        }
      })

      if (response.ok) {
        const result = await response.json()
        
        // Show success message
        const successMessage: Message = {
          id: uuidv4(),
          type: 'assistant',
          content: `✅ **Document Deleted Successfully**\n\n📄 **Deleted:** ${document.title}\n🗑️ **Status:** Removed from system\n📊 **Chunks removed:** ${document.chunks_created}\n\n🔄 The document library has been updated.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, successMessage])
        
        // Refresh document list
        fetchDocuments()
        

        
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Delete failed')
      }
    } catch (error) {
      console.error('Error deleting document:', error)
      const errorMessage: Message = {
        id: uuidv4(),
        type: 'assistant',
        content: `❌ **Document Deletion Failed**\n\n📄 **Document:** ${document.title}\n🚫 **Error:** ${error instanceof Error ? error.message : 'Unknown error'}\n\nPlease try again or contact support.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  // Context7 verified: Real Conversation Management Functions
  const fetchConversations = async () => {
    setIsLoadingConversations(true)
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/`, {
        headers: {
          'Authorization': `Bearer ${auth.accessToken}`
        }
      })
      const data = await response.json()
      setConversations(data.conversations || [])
    } catch (error) {
      console.error('Error fetching conversations:', error)
      setConversations([])
    } finally {
      setIsLoadingConversations(false)
    }
  }

  const createNewConversation = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.accessToken}`
        },
        body: JSON.stringify({
          title: null,  // Will be auto-generated by AI
          session_id: sessionId,
          language: 'tr'
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setCurrentConversationId(data.id)
        setMessages([])
        
        // Refresh conversations list
        fetchConversations()
        
        // Track user activity (Context7 verified)
        auth.updateUserActivity('conversation')
        
        return data.id
      } else {
        // Fallback to temporary ID
        const tempId = `temp_${Date.now()}`
        setCurrentConversationId(tempId)
        setMessages([])
        return tempId
      }
    } catch (error) {
      console.error('Error creating conversation:', error)
      // Fallback to temporary ID
      const tempId = `temp_${Date.now()}`
      setCurrentConversationId(tempId)
      setMessages([])
      return tempId
    }
  }

  const loadConversation = async (conversationId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/`, {
        headers: {
          'Authorization': `Bearer ${auth.accessToken}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setCurrentConversationId(conversationId)
        
        // Convert backend messages to frontend format
        const frontendMessages: Message[] = data.messages.map((msg: any) => ({
          id: msg.id,
          type: msg.message_type === 'user' ? 'user' : 'assistant',
          content: msg.content,
          timestamp: new Date(msg.created_at),
          response_time_ms: msg.response_time_ms || undefined,
          sources: msg.sources_used ? msg.sources_used.map((source: string) => ({
            source,
            page: 'Unknown',
            score: 0,
            chunk_id: '',
            slide_number: 'Unknown',
            relevance_percentage: 0,
            content_type: 'document'
          })) : undefined
        }))
        
        setMessages(frontendMessages)
        
        // Track user activity (Context7 verified)
        auth.updateUserActivity('conversation')
        
        return true
      }
    } catch (error) {
      console.error('Error loading conversation:', error)
    }
    return false
  }

  const saveMessageToConversation = async (message: Message, conversationId?: string) => {
    // DISABLED: Message saving until conversation API is fixed
    return
  }

  const deleteConversation = async (conversationId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${auth.accessToken}`
        }
      })
      
      if (response.ok) {
        // Remove from conversations list
        setConversations(prev => prev.filter(conv => conv.id !== conversationId))
        
        // If this was the current conversation, clear it
        if (currentConversationId === conversationId) {
          setCurrentConversationId(null)
          setMessages([])
        }
        
        // Track user activity (Context7 verified)
        auth.updateUserActivity('conversation')
      }
    } catch (error) {
      console.error('Error deleting conversation:', error)
    }
  }

  // Load conversations on component mount and setup
  useEffect(() => {
    fetchConversations()
    
    // If no current conversation, create one
    if (!currentConversationId && messages.length === 0) {
      createNewConversation()
    }
  }, [sessionId])

  // Load documents when library tab is active
  useEffect(() => {
    if (activeTab === 'library') {
      fetchDocuments()
    }
  }, [activeTab])

  // Auto-save messages to current conversation
  useEffect(() => {
    if (messages.length > 0 && currentConversationId) {
      const lastMessage = messages[messages.length - 1]
      saveMessageToConversation(lastMessage)
    }
  }, [messages, currentConversationId])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    // Create or ensure we have a conversation
    let conversationId = currentConversationId
    if (!conversationId) {
      conversationId = await createNewConversation()
      if (!conversationId) return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    
    // Scroll to bottom after user message (Context7 verified)
    setTimeout(() => scrollToBottom(), 100)

    try {
      const startTime = Date.now()
      
      // Build conversation context for multi-turn support
      const conversationContext = messages.slice(-8).map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content
      }))

      const response = await fetch(`${API_BASE_URL}/chat/query`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.accessToken}`
        },
        body: JSON.stringify({ 
          question: input.trim(),
          conversation_context: conversationContext,
          conversation_id: conversationId,
          session_id: sessionId
        })
      })

      const data = await response.json()
      const responseTime = Date.now() - startTime

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.answer || data.message || 'I apologize, but I encountered an error processing your request.',
        timestamp: new Date(),
        sources: data.sources || [],
        documents_found: data.documents_found || 0,
        has_context: data.has_context || false,
        confidence: data.confidence || 0,
        response_time_ms: responseTime,
        // AI Intelligence fields (Context7 verified)
        related_questions: data.related_questions || [],
        document_recommendations: data.document_recommendations || [],
        ai_intelligence_enabled: data.ai_intelligence_enabled || false
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Scroll to bottom after assistant response (Context7 verified)
      setTimeout(() => scrollToBottom(), 100)
      
      // Refresh conversations list to get updated AI-generated title (Context7 verified)
      setTimeout(() => fetchConversations(), 500)
      
      // Track user activity (Context7 verified)
      auth.updateUserActivity('query')
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      
      // Scroll to bottom after error message (Context7 verified)
      setTimeout(() => scrollToBottom(), 100)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    setUploadStatus({ uploading: true, success: false })

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: 'POST',
        body: formData
      })

      const result = await response.json()
      
      if (response.ok) {
        setUploadStatus({
          uploading: false,
          success: true,
          filename: file.name,
          details: result
        })
        
        setTimeout(() => {
          setUploadStatus({ uploading: false, success: false })
        }, 5000)
      } else {
        throw new Error(result.detail || 'Upload failed')
      }
    } catch (error) {
      setUploadStatus({
        uploading: false,
        success: false,
        error: error instanceof Error ? error.message : 'Upload failed'
      })
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  const categories = ['all', ...new Set(documents.map(doc => doc.category))]
  const filteredDocuments = selectedCategory === 'all' 
    ? documents 
    : documents.filter(doc => doc.category === selectedCategory)

  // Helper function to format document title (Context7 UX Pattern)
  const formatDocumentTitle = (title: string, filename: string): { displayTitle: string, fullTitle: string } => {
    // If title is just a UUID or long string, use filename instead
    if (title.length > 50 || /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.test(title)) {
      const cleanName = filename.replace(/\.[^/.]+$/, '') // Remove extension
      return {
        displayTitle: cleanName.length > 35 ? cleanName.substring(0, 35) + '...' : cleanName,
        fullTitle: filename
      }
    }
    
    return {
      displayTitle: title.length > 35 ? title.substring(0, 35) + '...' : title,
      fullTitle: title
    }
  }

  // Format file size helper (Context7 Pattern)
  const formatFileSize = (sizeKb: number): string => {
    if (sizeKb < 1024) return `${sizeKb.toFixed(1)}KB`
    const sizeMb = sizeKb / 1024
    if (sizeMb < 1024) return `${sizeMb.toFixed(1)}MB`
    const sizeGb = sizeMb / 1024
    return `${sizeGb.toFixed(1)}GB`
  }

  // Get file type icon (Context7 Visual Enhancement)
  const getFileTypeIcon = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'pdf': return '📄'
      case 'docx': 
      case 'doc': return '📝'
      case 'txt': return '📋'
      case 'pptx':
      case 'ppt': return '📊'
      case 'xlsx':
      case 'xls': return '📈'
      default: return '📄'
    }
  }



  return (
    <div className={`h-screen w-full bg-gradient-to-br ${currentTheme.background} relative overflow-hidden flex`}>
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className={`absolute top-20 left-20 w-72 h-72 ${currentTheme.glowPrimary} rounded-full blur-3xl animate-pulse`}></div>
        <div className={`absolute bottom-20 right-20 w-96 h-96 ${currentTheme.glowSecondary} rounded-full blur-3xl animate-pulse delay-1000`}></div>
        <div className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 ${currentTheme.glowTertiary} rounded-full blur-3xl animate-pulse delay-2000`}></div>
      </div>

      {/* Gradient Overlay */}
      <div className={`absolute inset-0 bg-gradient-to-br ${currentTheme.backgroundSecondary}`}></div>
      
      {/* ChatGPT-style Sidebar */}
      {showSidebar && (
        <div className={`w-80 ${currentTheme.sidebarBackground} backdrop-blur-xl border-r ${currentTheme.borderColor} flex flex-col relative z-10`}>
          {/* Sidebar Header */}
          <div className="p-4 border-b border-white/10 flex items-center justify-between">
            <button
              onClick={createNewConversation}
              className="flex-1 p-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-xl text-white flex items-center space-x-2 transition-all mr-2 shadow-lg"
            >
              <span>➕</span>
              <span>New Chat</span>
            </button>
            <button
              onClick={() => setShowSidebar(false)}
              className="p-3 text-white/60 hover:text-white hover:bg-white/10 rounded-xl transition-colors"
            >
              ✕
            </button>
          </div>
          
          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto p-2">
            {isLoadingConversations ? (
              <div className="text-center text-white/50 py-8">
                <div className="text-2xl mb-2">📝</div>
                <p className="text-sm">Loading conversations...</p>
              </div>
            ) : conversations.length === 0 ? (
              <div className="text-center text-white/50 py-8">
                <div className="text-3xl mb-2">💬</div>
                <p className="text-sm">No conversations yet</p>
                <p className="text-xs text-white/40 mt-2">Start chatting below!</p>
              </div>
            ) : (
              conversations.map((conv) => {
                // Format the conversation title with smart fallbacks
                const getConversationTitle = (conv: any) => {
                  if (conv.title && conv.title !== 'Chat' && !conv.title.startsWith('Chat ')) {
                    return conv.title
                  }
                  // Fallback to first message preview if available
                  if (conv.last_message_preview) {
                    const words = conv.last_message_preview.split(' ').slice(0, 4)
                    return words.join(' ') + (words.length >= 4 ? '...' : '')
                  }
                  return 'New Chat'
                }
                
                const displayTitle = getConversationTitle(conv)
                const isActiveConv = currentConversationId === conv.id
                
                return (
                  <div
                    key={conv.id}
                    className={`group relative p-3 rounded-xl cursor-pointer transition-all duration-200 mb-2 ${
                      isActiveConv
                        ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/30 shadow-lg backdrop-blur-sm' 
                        : 'bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/20 backdrop-blur-sm'
                    }`}
                    onClick={() => loadConversation(conv.id)}
                  >
                    {/* Active conversation indicator */}
                    {isActiveConv && (
                      <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-blue-400 to-purple-500 rounded-r-full"></div>
                    )}
                    
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0 pl-2">
                        {/* Chat title with icon */}
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-xs">💬</span>
                          <div className={`truncate font-medium text-sm ${
                            isActiveConv ? 'text-white' : 'text-white/90'
                          }`}>
                            {displayTitle}
                          </div>
                        </div>
                        
                        {/* Message preview */}
                        <div className={`text-xs mt-1 truncate ${
                          isActiveConv ? 'text-white/70' : 'text-white/60'
                        }`}>
                          {conv.last_message_preview || `${conv.message_count} mesaj`}
                        </div>
                        
                        {/* Time and message count */}
                        <div className="flex items-center justify-between mt-2">
                          <div className={`text-xs ${
                            isActiveConv ? 'text-white/60' : 'text-white/40'
                          }`}>
                            {new Date(conv.last_activity).toLocaleDateString('tr-TR', { 
                              day: 'numeric', 
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                          <div className={`text-xs px-2 py-1 rounded-full ${
                            isActiveConv 
                              ? 'bg-blue-500/20 text-blue-200' 
                              : 'bg-white/10 text-white/60'
                          }`}>
                            {conv.message_count}
                          </div>
                        </div>
                      </div>
                      
                      {/* Delete button */}
                      <button 
                        className="opacity-0 group-hover:opacity-100 text-white/60 hover:text-red-300 hover:bg-red-500/20 p-1.5 rounded-lg transition-all duration-200 ml-2"
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteConversation(conv.id)
                        }}
                        title="Delete conversation"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                )
              })
            )}
          </div>
          
          {/* User Profile Section */}
          <div className="p-4 border-t border-white/10">
            <div className="flex items-center justify-between mb-3">
              <div 
                className="flex items-center space-x-3 cursor-pointer hover:bg-white/5 rounded-xl p-2 -m-2 transition-all"
                onClick={() => setShowUserProfile(true)}
                title="View Profile"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg">
                  <span className="text-white text-lg">{user?.full_name?.charAt(0) || '👤'}</span>
                </div>
                <div>
                  <div className="text-white text-sm font-semibold truncate max-w-24">
                    {user?.full_name || 'User'}
                  </div>
                  <div className="text-white/60 text-xs truncate max-w-24">
                    {user?.role || 'user'}
                  </div>
                </div>
              </div>
              <div className="flex space-x-1">
                <button
                  onClick={() => setShowUserProfile(true)}
                  className="p-2 text-white/60 hover:text-white hover:bg-white/10 rounded-xl transition-all"
                  title="User Profile"
                >
                  ⚙️
                </button>
                <button
                  onClick={onLogout}
                  className="p-2 text-white/60 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-all"
                  title="Logout"
                >
                  🚪
                </button>
              </div>
            </div>
            <div className="bg-white/5 rounded-xl p-3 text-center">
              <div className="text-white/80 text-xs">Enterprise RAG System</div>
              <div className="text-white/60 text-xs">AI Document Intelligence</div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen relative z-10">
        
        {/* Modern Header */}
        <header className={`backdrop-blur-xl ${currentTheme.headerBackground} border-b ${currentTheme.borderColor} p-4 shadow-lg`}>
          <div className="flex items-center justify-between">
            {/* Left side - Sidebar toggle and title */}
            <div className="flex items-center space-x-4">
              {!showSidebar && (
                <button
                  onClick={() => setShowSidebar(true)}
                  className="p-2 text-white/60 hover:text-white hover:bg-white/10 rounded-xl transition-all"
                >
                  ☰
                </button>
              )}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                  <span className="text-lg">🧠</span>
                </div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent">
                  {activeTab === 'chat' ? 'AI Chat Assistant' :
                   activeTab === 'upload' ? 'Document Upload' :
                   activeTab === 'library' ? 'Document Library' :
                   activeTab === 'collaboration' ? 'Real-time Collaboration' : 'Enterprise RAG'}
                </h1>
              </div>
            </div>
            
            {/* Right side - Tab Navigation */}
            <div className="flex bg-white/5 p-1 rounded-xl border border-white/10">
              <button 
                onClick={() => setActiveTab('chat')}
                className={`px-4 py-2 rounded-lg transition-all duration-300 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === 'chat' 
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg transform scale-105' 
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>💬</span>
                <span>Chat</span>
              </button>
              <button 
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-lg transition-all duration-300 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === 'upload' 
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg transform scale-105' 
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>📁</span>
                <span>Upload</span>
              </button>
              <button 
                onClick={() => setActiveTab('library')}
                className={`px-4 py-2 rounded-lg transition-all duration-300 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === 'library' 
                    ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg transform scale-105' 
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>📚</span>
                <span>Library</span>
              </button>

              <button 
                onClick={() => setActiveTab('collaboration')}
                className={`px-4 py-2 rounded-lg transition-all duration-300 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === 'collaboration' 
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg transform scale-105' 
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>👥</span>
                <span>Collaborate</span>
              </button>


            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 backdrop-blur-xl bg-white/5 overflow-hidden">
          
          {activeTab === 'chat' ? (
            /* Chat Interface */
            <div className="flex flex-col h-full">
              
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center space-y-6">
                      <div className="relative">
                        <div className="w-24 h-24 bg-gradient-to-br from-blue-400/20 to-purple-500/20 rounded-3xl flex items-center justify-center mx-auto backdrop-blur-xl border border-white/10">
                          <span className="text-5xl">💡</span>
                        </div>
                        <div className="absolute -top-2 -right-2 w-6 h-6 bg-blue-400 rounded-full animate-ping"></div>
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-white mb-3">AI Assistant Ready</h3>
                        <p className="text-white/60 max-w-lg leading-relaxed">
                          Ask me anything about your documents and I'll provide detailed answers with precise source citations.
                        </p>
                      </div>
                      <div className="flex justify-center space-x-4 text-sm">
                        <div className="flex items-center space-x-2 bg-white/5 px-4 py-2 rounded-xl border border-white/10">
                          <span>📚</span>
                          <span className="text-white/70">Smart Document Analysis</span>
                        </div>
                        <div className="flex items-center space-x-2 bg-white/5 px-4 py-2 rounded-xl border border-white/10">
                          <span>🎯</span>
                          <span className="text-white/70">Precise Source Citations</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-4xl ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                        
                        {/* Modern Message Bubble */}
                        <div className={`relative group ${message.type === 'user' ? 'ml-12' : 'mr-12'}`}>
                          <div className={`p-5 rounded-3xl backdrop-blur-xl border shadow-xl ${
                            message.type === 'user' 
                              ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white border-blue-400/20 shadow-blue-500/20' 
                              : 'bg-white/10 border-white/20 text-white shadow-white/5'
                          }`}>
                            <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
                            
                            {/* Message Metadata */}
                            <div className="mt-3 flex items-center justify-between text-xs opacity-70">
                              <span className="flex items-center space-x-1">
                                <span>🕒</span>
                                <span>{message.timestamp.toLocaleTimeString()}</span>
                              </span>
                              {message.type === 'assistant' && message.response_time_ms && (
                                <span className="flex items-center space-x-1">
                                  <span>⚡</span>
                                  <span>{message.response_time_ms}ms</span>
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Enhanced Sources Display */}
                          {message.type === 'assistant' && message.sources && message.sources.length > 0 && (
                            <div className="mt-4 mr-12">
                              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-xl">
                                <div className="flex items-center justify-between mb-4">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-sm text-white font-semibold">📚 Kaynaklar</span>
                                    <span className="text-xs bg-white/10 text-white/80 px-2 py-1 rounded-full">
                                      {message.documents_found} documents
                                    </span>
                                  </div>
                                  <span className="text-xs bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-3 py-1 rounded-full font-medium">
                                    {(message.confidence! * 100).toFixed(0)}% confidence
                                  </span>
                                </div>
                                <div className="p-4 space-y-2">
                                  {message.sources.map((source, index) => (
                                    <div key={index} className="flex items-center justify-between text-xs text-white/70">
                                      <p className="truncate w-60 pr-2">{source.source}</p>
                                      <p className="flex-shrink-0">{source.page}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* AI Intelligence: Related Questions (Context7 verified) */}
                          {message.type === 'assistant' && message.related_questions && message.related_questions.length > 0 && (
                            <div className="mt-4 mr-12">
                              <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 backdrop-blur-xl border border-blue-400/20 rounded-2xl p-5 shadow-xl">
                                <div className="flex items-center space-x-2 mb-4">
                                  <span className="text-sm text-blue-300 font-semibold">🤔 Related Questions</span>
                                  <span className="text-xs bg-blue-500/20 text-blue-200 px-2 py-1 rounded-full">
                                    AI Suggested
                                  </span>
                                </div>
                                <div className="space-y-2">
                                  {message.related_questions.map((question, idx) => (
                                    <button
                                      key={idx}
                                      onClick={() => setInput(question)}
                                      className="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/5 hover:border-blue-400/30 transition-all group"
                                    >
                                      <div className="text-white/90 text-sm group-hover:text-blue-200 transition-colors">
                                        {question}
                                      </div>
                                    </button>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* AI Intelligence: Document Recommendations (Context7 verified) */}
                          {message.type === 'assistant' && message.document_recommendations && message.document_recommendations.length > 0 && (
                            <div className="mt-4 mr-12">
                              <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 backdrop-blur-xl border border-green-400/20 rounded-2xl p-5 shadow-xl">
                                <div className="flex items-center space-x-2 mb-4">
                                  <span className="text-sm text-green-300 font-semibold">📄 Recommended Documents</span>
                                  <span className="text-xs bg-green-500/20 text-green-200 px-2 py-1 rounded-full">
                                    AI Curated
                                  </span>
                                </div>
                                <div className="space-y-3">
                                  {message.document_recommendations.map((doc, idx) => (
                                    <div key={idx} className="p-3 bg-white/5 rounded-xl border border-white/5 hover:border-green-400/30 transition-all">
                                      <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                          <div className="text-white/90 text-sm font-medium">{doc.title}</div>
                                          <div className="text-white/60 text-xs mt-1">
                                            {doc.file_type.toUpperCase()} • {doc.relevance_reason}
                                          </div>
                                          {doc.content_preview && (
                                            <div className="text-white/50 text-xs mt-2 line-clamp-2">
                                              {doc.content_preview}
                                            </div>
                                          )}
                                        </div>
                                        <div className="ml-3">
                                          <span className="text-green-300 text-xs font-bold">
                                            📎
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                
                {/* Messages End Ref for Auto-scroll (Context7 verified) */}
                <div ref={messagesEndRef} />
                
                {/* Enhanced Loading Indicator */}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-5 mr-12 shadow-xl">
                      <div className="flex items-center space-x-3">
                        <div className="flex space-x-1">
                          <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce"></div>
                          <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce delay-100"></div>
                          <div className="w-3 h-3 bg-pink-400 rounded-full animate-bounce delay-200"></div>
                        </div>
                        <span className="text-white/80 text-sm font-medium">AI is analyzing...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Real-time Features Indicator */}
              <div className="px-6 py-2 border-t border-white/5 bg-white/3 backdrop-blur-xl">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
                      <span className="text-white/60">
                        {isConnected ? '⚡ Real-time Active' : '❌ Disconnected'}
                      </span>
                    </div>
                    <div className="text-white/40">|</div>
                    <div className="text-white/60">👥 {activeUsers} Online</div>
                    <div className="text-white/40">|</div>
                    <div className="text-white/60">🚀 WebSocket Features: ON</div>
                  </div>
                  <div className="text-white/40">
                    Connection: {connectionStatus}
                  </div>
                </div>
              </div>

              {/* Modern Chat Input */}
              <div className="p-6 border-t border-white/10 bg-white/5 backdrop-blur-xl">
                <div className="flex space-x-4">
                  <div className="flex-1 relative">
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Ask me anything about your documents... (Real-time powered)"
                      rows={1}
                      className="w-full p-4 pr-14 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl text-white placeholder-white/50 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all shadow-inner"
                      disabled={isLoading}
                    />
                    <button
                      onClick={sendMessage}
                      disabled={!input.trim() || isLoading}
                      className="absolute right-2 top-2 p-2.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl text-white disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-blue-500/25 transition-all transform hover:scale-105 active:scale-95"
                    >
                      <span className="text-lg">🚀</span>
                    </button>
                  </div>
                  <button
                    onClick={clearChat}
                    className="px-4 py-2 bg-white/5 border border-white/10 rounded-2xl text-white/70 hover:bg-white/10 hover:text-white transition-all backdrop-blur-md"
                    title="Clear Chat History"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ) : activeTab === 'library' ? (
            <div className="h-full flex flex-col p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">📚 Document Library</h2>
                  <p className="text-white/60">Manage your uploaded documents and knowledge base</p>
                </div>
                <button 
                  onClick={fetchDocuments}
                  className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl hover:scale-105 transition-all duration-200 font-medium shadow-lg"
                >
                  🔄 Refresh
                </button>
              </div>

              {/* Enhanced Category Filter */}
              <div className="mb-6">
                <div className="flex flex-wrap gap-3">
                  <span className="text-white/60 text-sm font-medium self-center mr-2">Filter by category:</span>
                  {categories.map((category) => (
                    <button
                      key={category}
                      onClick={() => setSelectedCategory(category)}
                      className={`px-4 py-2 rounded-xl text-sm font-medium transition-all transform hover:scale-105 ${
                        selectedCategory === category
                          ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                          : 'bg-white/10 text-white/70 hover:bg-white/20 hover:text-white'
                      }`}
                    >
                      {category === 'all' ? `📚 All Documents (${documents.length})` : `📁 ${category}`}
                    </button>
                  ))}
                </div>
              </div>

              {/* Enhanced Documents Grid */}
              <div className="flex-1 overflow-y-auto">
                {isLoadingDocs ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center space-y-4">
                      <div className="w-16 h-16 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto"></div>
                      <p className="text-white/60">Loading documents...</p>
                    </div>
                  </div>
                ) : filteredDocuments.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center text-white/60 space-y-6">
                      <div className="text-8xl">📭</div>
                      <div>
                        <h3 className="text-2xl font-semibold mb-2">No Documents Found</h3>
                        <p className="text-lg">Upload some documents to get started!</p>
                        <p className="text-sm text-white/40 mt-2">Supported: PDF, DOCX, TXT, PPTX</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {filteredDocuments.map((doc) => {
                      const { displayTitle, fullTitle } = formatDocumentTitle(doc.title, doc.filename)
                      const fileIcon = getFileTypeIcon(doc.filename)
                      
                      return (
                        <div
                          key={doc.id}
                          className="group bg-gradient-to-br from-white/5 to-white/10 border border-white/20 rounded-2xl p-6 hover:from-white/10 hover:to-white/15 hover:border-white/30 transition-all duration-300 transform hover:scale-[1.02] hover:shadow-2xl backdrop-blur-xl"
                          title={fullTitle}
                        >
                          {/* Header with File Icon and Status */}
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center space-x-3">
                              <div className="text-3xl">{fileIcon}</div>
                              <div className="min-w-0 flex-1">
                                <h3 
                                  className="text-lg font-semibold text-white leading-tight hover:text-blue-300 transition-colors cursor-pointer"
                                  title={fullTitle}
                                >
                                  {displayTitle}
                                </h3>
                                <div className="text-xs text-white/60 mt-1 font-medium">
                                  {doc.filename.split('.').pop()?.toUpperCase()} • {formatFileSize(doc.text_length / 1024)}
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <span className={`px-3 py-1 rounded-xl text-xs font-semibold ${
                                doc.status === 'processed' 
                                  ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                                  : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
                              }`}>
                                {doc.status === 'processed' ? '✅ Ready' : '⏳ Processing'}
                              </span>
                              
                              <button
                                onClick={() => deleteDocument(doc)}
                                className="opacity-0 group-hover:opacity-100 p-2 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded-xl transition-all duration-200"
                                title={`Delete ${fullTitle}`}
                              >
                                🗑️
                              </button>
                            </div>
                          </div>

                          {/* Document Stats */}
                          <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                <div className="text-white/60 text-xs font-medium">Chunks</div>
                                <div className="text-white text-lg font-bold">{doc.chunks_created}</div>
                              </div>
                              <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                                <div className="text-white/60 text-xs font-medium">Size</div>
                                <div className="text-white text-lg font-bold">{formatFileSize(doc.text_length / 1024)}</div>
                              </div>
                            </div>
                            
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between items-center">
                                <span className="text-white/60">Category:</span>
                                <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded-lg text-xs font-medium">
                                  {doc.category}
                                </span>
                              </div>
                              
                              <div className="flex justify-between items-center">
                                <span className="text-white/60">Uploaded:</span>
                                <span className="text-white/80 text-xs">
                                  {doc.upload_date ? new Date(doc.upload_date).toLocaleDateString('tr-TR', {
                                    day: '2-digit',
                                    month: '2-digit',
                                    year: 'numeric'
                                  }) : 'Invalid Date'}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="mt-4 pt-4 border-t border-white/10">
                            <div className="flex space-x-2">
                              <button 
                                className="flex-1 px-3 py-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-300 rounded-lg text-xs font-medium hover:from-blue-500/30 hover:to-purple-500/30 transition-all duration-200 border border-blue-500/30"
                                title="View document details"
                              >
                                👁️ View
                              </button>
                              <button 
                                onClick={() => {
                                  setInput(`Bu belge hakkında bilgi ver: ${doc.filename}`)
                                  setActiveTab('chat')
                                }}
                                className="flex-1 px-3 py-2 bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-300 rounded-lg text-xs font-medium hover:from-green-500/30 hover:to-emerald-500/30 transition-all duration-200 border border-green-500/30 hover:scale-105"
                                title="Search in this document"
                              >
                                🔍 Search
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
              
              {/* Enhanced Footer Stats */}
              {!isLoadingDocs && filteredDocuments.length > 0 && (
                <div className="mt-6 pt-4 border-t border-white/10">
                  <div className="flex items-center justify-between text-sm text-white/60">
                    <div>
                      Showing {filteredDocuments.length} of {documents.length} documents
                    </div>
                    <div className="flex items-center space-x-4">
                      <span>Total chunks: {filteredDocuments.reduce((sum, doc) => sum + doc.chunks_created, 0)}</span>
                      <span>Total size: {formatFileSize(filteredDocuments.reduce((sum, doc) => sum + (doc.text_length / 1024), 0))}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : activeTab === 'collaboration' ? (
            /* Real-time Collaboration Interface */
            <div className="h-full p-6">
              <RealtimeCollaboration
                roomId="banking-support-room"
                userId={user?.id || 'anonymous'}
                userName={user?.full_name || user?.email || 'Anonymous User'}
                userAvatar={user?.avatar}
                roomType="chat"
                className="h-full"
              />
            </div>
          ) : (
            /* Enhanced Upload Interface */
            <div className="h-full flex flex-col p-6">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-white mb-2 flex items-center">
                  <span className="mr-3">📤</span>
                  Multi-File Upload
                </h2>
                <p className="text-white/60">Upload multiple documents to enhance your AI knowledge base</p>
              </div>
              
              <Uploady 
                destination={uploadDestination}
                multiple={true}
                grouped={false}
                autoUpload={true}
                fileFilter={(file) => {
                  const validTypes = ['.pdf', '.docx', '.txt', '.pptx'];
                  const fileName = (file as File).name || '';
                  const fileExt = '.' + fileName.split('.').pop()?.toLowerCase();
                  return validTypes.includes(fileExt);
                }}
              >
                <div className="space-y-6">
                  {/* Context7 verified Drag & Drop Zone */}
                  <UploadDropZone 
                    onDragOverClassName="border-purple-400 bg-purple-500/20"
                    className="border-2 border-dashed border-white/30 rounded-3xl p-16 text-center hover:border-purple-400 hover:bg-white/5 transition-all duration-300 cursor-pointer"
                  >
                    <div className="space-y-4">
                      <div className="text-6xl">📁</div>
                      <h3 className="text-2xl font-semibold text-white">
                        Drag & Drop Files Here
                      </h3>
                      <p className="text-white/70 max-w-md mx-auto">
                        Drop multiple files to upload them all at once. 
                        Supports PDF, DOCX, TXT, PPTX files up to 100MB each.
                      </p>
                      <div className="flex justify-center space-x-4 text-sm text-white/50">
                        <span>📄 PDF</span>
                        <span>📝 DOCX</span>
                        <span>📋 TXT</span>
                        <span>📊 PPTX</span>
                      </div>
                    </div>
                  </UploadDropZone>

                  {/* Context7 verified Upload Button */}
                  <div className="text-center">
                    <UploadButton className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-8 py-4 rounded-2xl font-medium hover:from-purple-600 hover:to-pink-600 transition-all duration-200 inline-flex items-center space-x-2">
                      <span>📂</span>
                      <span>Or Browse Files</span>
                    </UploadButton>
                  </div>

                  {/* Upload Limits Info */}
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h4 className="text-lg font-semibold text-white mb-3">
                      📋 Upload Guidelines
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-white/70">
                      <div>
                        <strong className="text-white">File Limits:</strong>
                        <ul className="mt-1 space-y-1">
                          <li>• Maximum 10 files per batch</li>
                          <li>• Up to 100MB per file</li>
                          <li>• No total size limit</li>
                        </ul>
                      </div>
                      <div>
                        <strong className="text-white">Supported Formats:</strong>
                        <ul className="mt-1 space-y-1">
                          <li>• PDF documents</li>
                          <li>• Word documents (.docx)</li>
                          <li>• Text files (.txt)</li>
                          <li>• PowerPoint (.pptx)</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Context7 verified Progress Component */}
                <MultiUploadProgress />
              </Uploady>
            </div>
          )}
        </main>
        
        {/* Context7-verified WebSocket Notifications */}
        <WebSocketNotifications 
          userId={user?.id}
          position="top-right"
          maxNotifications={5}
        />
        
        {/* Theme Selector Button */}
        <ThemeButton />
      </div>
      
      {/* User Profile Modal (Context7 Verified) */}
      <UserProfileModal 
        isOpen={showUserProfile}
        onClose={() => setShowUserProfile(false)}
      />
    </div>
  )
}

export default App 
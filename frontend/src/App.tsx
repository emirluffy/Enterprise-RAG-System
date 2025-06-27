import React, { useState, useEffect, useRef, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import './index.css'

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
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'library'>('chat')
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ uploading: false, success: false })
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoadingDocs, setIsLoadingDocs] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Context7 verified Multi-Upload Configuration
  const uploadDestination = {
    url: "http://localhost:8002/api/v1/documents/upload-multiple",
    method: "POST" as const,
    headers: {},
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

  // Fetch documents for library
  const fetchDocuments = async () => {
    setIsLoadingDocs(true)
    try {
      const response = await fetch('http://localhost:8002/api/v1/documents/library')
      const data = await response.json()
      setDocuments(data.documents || [])
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setIsLoadingDocs(false)
    }
  }

  // Load documents when library tab is active
  useEffect(() => {
    if (activeTab === 'library') {
      fetchDocuments()
    }
  }, [activeTab])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const startTime = Date.now()
      const response = await fetch('http://localhost:8002/api/v1/chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input.trim() })
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
        response_time_ms: responseTime
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    setUploadStatus({ uploading: true, success: false })

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8002/api/v1/documents/upload', {
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-950 to-slate-950 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-20 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-pink-500/5 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/20 via-purple-900/10 to-slate-900/20"></div>
      
      {/* Main Container */}
      <div className="relative z-10 container mx-auto px-4 py-6 h-screen flex flex-col max-w-7xl">
        
        {/* Modern Header */}
        <header className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-6 mb-6 shadow-2xl">
          <div className="flex items-center justify-between">
            {/* Logo & Title */}
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg">
                  <span className="text-2xl">🧠</span>
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent">
                  Enterprise RAG
                </h1>
                <p className="text-white/60 text-sm font-medium">AI Document Intelligence System</p>
              </div>
            </div>
            
            {/* Modern Tab Navigation */}
            <div className="flex bg-white/5 p-2 rounded-2xl border border-white/10">
              <button 
                onClick={() => setActiveTab('chat')}
                className={`px-6 py-3 rounded-xl transition-all duration-300 font-medium flex items-center space-x-2 ${
                  activeTab === 'chat' 
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/25 transform scale-105' 
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>💬</span>
                <span>Chat</span>
              </button>
              <button 
                onClick={() => setActiveTab('upload')}
                className={`px-6 py-3 rounded-xl transition-all duration-300 font-medium flex items-center space-x-2 ${
                  activeTab === 'upload' 
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/25 transform scale-105' 
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>📁</span>
                <span>Upload</span>
              </button>
              <button 
                onClick={() => setActiveTab('library')}
                className={`px-6 py-3 rounded-xl transition-all duration-300 font-medium flex items-center space-x-2 ${
                  activeTab === 'library' 
                    ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25 transform scale-105' 
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                <span>📚</span>
                <span>Library</span>
              </button>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
          
          {activeTab === 'chat' ? (
            /* Chat Interface */
            <div className="flex flex-col h-full">
              
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
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
                          Upload your documents and ask intelligent questions. I'll analyze your content with advanced AI and provide detailed answers with precise source citations.
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
                                    <span className="text-sm text-white font-semibold">📚 Knowledge Sources</span>
                                    <span className="text-xs bg-white/10 text-white/80 px-2 py-1 rounded-full">
                                      {message.documents_found} documents
                                    </span>
                                  </div>
                                  <span className="text-xs bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-3 py-1 rounded-full font-medium">
                                    {(message.confidence! * 100).toFixed(0)}% confidence
                                  </span>
                                </div>
                                <div className="space-y-3">
                                  {message.sources.slice(0, 3).map((source, idx) => (
                                    <div key={idx} className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5">
                                      <div className="flex-1">
                                        <div className="text-white/90 text-sm font-medium truncate">{source.source}</div>
                                        <div className="text-white/60 text-xs">Page {source.page}</div>
                                      </div>
                                      <div className="ml-3 text-right">
                                        <div className="text-blue-300 text-sm font-bold">
                                          {(source.score * 100).toFixed(1)}%
                                        </div>
                                        <div className="text-white/50 text-xs">relevance</div>
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

              {/* Modern Chat Input */}
              <div className="p-6 border-t border-white/10 bg-white/5 backdrop-blur-xl">
                <div className="flex space-x-4">
                  <div className="flex-1 relative">
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Ask me anything about your documents..."
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
            <div className="h-full flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">📚 Doküman Kütüphanesi</h2>
                  <p className="text-white/60">Yüklenmiş dokümanlarınızı görüntüleyin ve yönetin</p>
                </div>
                <button 
                  onClick={fetchDocuments}
                  className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl hover:scale-105 transition-all duration-200 font-medium"
                >
                  🔄 Yenile
                </button>
              </div>

              {/* Category Filter */}
              <div className="mb-6">
                <div className="flex flex-wrap gap-2">
                  {categories.map((category) => (
                    <button
                      key={category}
                      onClick={() => setSelectedCategory(category)}
                      className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                        selectedCategory === category
                          ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                          : 'bg-white/10 text-white/70 hover:bg-white/20'
                      }`}
                    >
                      {category === 'all' ? 'All Documents' : category}
                    </button>
                  ))}
                </div>
              </div>

              {/* Documents Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredDocuments.length === 0 ? (
                  <div className="col-span-full text-center text-white/60 py-20">
                    <div className="text-6xl mb-4">📭</div>
                    <h3 className="text-xl font-semibold mb-2">No Documents Found</h3>
                    <p>Upload some documents to get started!</p>
                  </div>
                ) : (
                  filteredDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="bg-white/10 border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all duration-200"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <h3 className="text-lg font-semibold text-white truncate flex-1">
                          {doc.title}
                        </h3>
                        <span className={`px-2 py-1 rounded-lg text-xs font-medium ${
                          doc.status === 'processed' 
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {doc.status}
                        </span>
                      </div>

                      <div className="space-y-2 text-sm text-white/70">
                        <div className="flex justify-between">
                          <span>Category:</span>
                          <span className="text-white">{doc.category}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Chunks:</span>
                          <span className="text-white">{doc.chunks_created}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Size:</span>
                          <span className="text-white">{(doc.text_length / 1024).toFixed(1)}KB</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Uploaded:</span>
                          <span className="text-white">
                            {new Date(doc.upload_date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : (
            /* Context7 Verified Multi-File Upload Interface */
            <div className="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                <span className="mr-3">📤</span>
                Multiple File Upload
              </h2>
              
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
      </div>
    </div>
  )
}

export default App 
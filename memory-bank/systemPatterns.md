# System Patterns - Enterprise RAG System

## Architecture Overview

### High-Level System Design
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend     │    │   AI/ML Layer   │
│  React + TS     │◄──►│    FastAPI      │◄──►│  Gemini 2.5     │
│  Tailwind CSS   │    │    Python       │    │  Flash-Lite     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User State    │    │   Document      │    │   Vector Store  │
│   Management    │    │   Storage       │    │   Pinecone/     │
│   (Zustand)     │    │   (S3/MinIO)    │    │   FAISS         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### RAG Pipeline Architecture
```
Document Ingestion Pipeline:
┌───────────┐ → ┌───────────┐ → ┌───────────┐ → ┌───────────┐
│  Document │   │   Text    │   │ Embedding │   │  Vector   │
│  Upload   │   │Extraction │   │Generation │   │  Storage  │
└───────────┘   └───────────┘   └───────────┘   └───────────┘
      │               │               │               │
      ▼               ▼               ▼               ▼
   OCR/Parse     Chunking +      text-embedding   pgvector/
   Multiple      Metadata        -3-small         Pinecone
   Formats       Extraction      OpenAI API

Query Processing Pipeline:
┌───────────┐ → ┌───────────┐ → ┌───────────┐ → ┌───────────┐
│   User    │   │   Query   │   │ Retrieval │   │ Response  │
│   Query   │   │Processing │   │ + Context │   │Generation │
└───────────┘   └───────────┘   └───────────┘   └───────────┘
      │               │               │               │
      ▼               ▼               ▼               ▼
  Natural Lang.   Embedding +      Top-K Vector    Gemini 2.5
  Understanding   Preprocessing    Search (k=5)    Flash-Lite
```

## Key Technical Decisions

### 1. Model Selection Strategy
**Primary Model**: Google Gemini 2.5 Flash-Lite Preview
- **Rationale**: Free tier with 1000 requests/day, high throughput
- **Scaling Plan**: Auto-upgrade to paid tiers based on usage
- **Fallback**: OpenAI GPT-3.5 Turbo for emergency scenarios

### 2. Database Architecture
**Primary Database**: PostgreSQL 15 + pgvector
- **Rationale**: ACID compliance, mature ecosystem, vector extension
- **Vector Storage**: Hybrid approach (Pinecone for production, FAISS for dev)
- **Caching Layer**: Redis for session management and frequent queries

### 3. Embedding Strategy
**Primary Embeddings**: OpenAI text-embedding-3-small
- **Rationale**: High quality, cost-effective, established performance
- **Backup**: Google Gemini embeddings for redundancy
- **Chunking**: 500-token chunks with 50-token overlap

### 4. Frontend Architecture
**Framework**: React 18 with TypeScript
- **State Management**: Zustand (lightweight, performant)
- **Styling**: Tailwind CSS + Headless UI (consistent, accessible)
- **Build Tool**: Vite (fast development, optimized builds)

## Component Relationships

### Core Components
```
┌─────────────────────────────────────────────────────────┐
│                     Web Application                    │
├─────────────────────────────────────────────────────────┤
│ ChatInterface │ DocumentLib │ Dashboard │ AdminPanel   │
├─────────────────────────────────────────────────────────┤
│           Shared Components & Services                 │
│ AuthService │ ApiClient │ StateManager │ ThemeProvider │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     Backend API                        │
├─────────────────────────────────────────────────────────┤
│ QueryEngine │ DocProcessor │ UserManagement │ Analytics │
├─────────────────────────────────────────────────────────┤
│              Core Services                              │
│ AuthMiddleware │ RateLimit │ Validation │ ErrorHandler │
└─────────────────────────────────────────────────────────┘
```

### Data Flow Patterns
```
User Query Flow:
Frontend → API Gateway → Query Processor → Vector Search → 
LLM Generation → Response Formatter → Frontend

Document Upload Flow:
Frontend → File Upload API → Document Processor → 
Text Extraction → Chunking → Embedding → Vector Storage
```

## Design Patterns in Use

### 1. Repository Pattern
- **Purpose**: Abstract data access layer
- **Implementation**: Separate repositories for documents, users, queries
- **Benefits**: Testable, maintainable, database-agnostic

### 2. Strategy Pattern
- **Purpose**: Multiple LLM providers and embedding models
- **Implementation**: Pluggable model interfaces
- **Benefits**: Easy A/B testing, fallback mechanisms

### 3. Observer Pattern
- **Purpose**: Real-time updates and analytics
- **Implementation**: Event-driven architecture for user actions
- **Benefits**: Decoupled components, extensible analytics

### 4. Command Pattern
- **Purpose**: Document processing pipelines
- **Implementation**: Chainable processing steps
- **Benefits**: Retry logic, audit trails, parallel processing

## Security Architecture

### Authentication & Authorization
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│     SSO     │    │    RBAC     │    │   Session   │
│ Integration │◄──►│   Engine    │◄──►│ Management  │
│(Active Dir) │    │             │    │   (Redis)   │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Data Protection
- **Encryption at Rest**: AES-256 for document storage
- **Encryption in Transit**: TLS 1.3 for all API communication
- **Data Residency**: Turkey-based storage for compliance
- **Audit Logging**: Complete activity trail for compliance

## Performance Patterns

### 1. Caching Strategy
- **L1 Cache**: Browser cache for static assets
- **L2 Cache**: Redis for frequent queries and sessions
- **L3 Cache**: Vector similarity cache for common queries

### 2. Rate Limiting
- **API Level**: 15 requests/minute (Gemini free tier)
- **User Level**: Intelligent queuing for fairness
- **System Level**: Circuit breaker for downstream services

### 3. Scaling Patterns
- **Horizontal Scaling**: Stateless API servers
- **Database Scaling**: Read replicas for analytics
- **Vector Search**: Partitioned vector indices

## Error Handling Patterns

### 1. Graceful Degradation
- LLM service unavailable → Show cached similar answers
- Vector search fails → Fallback to keyword search
- Network issues → Offline capability for basic features

### 2. Circuit Breaker
- Monitor downstream service health
- Automatic failover to backup services
- User notification of service limitations

### 3. Retry Logic
- Exponential backoff for API calls
- Dead letter queues for failed document processing
- User-visible status for long-running operations

## Critical Development Operations

### 🚨 MANDATORY: Server Startup Protocol

**ALWAYS use `./start.sh` for server operations - NO EXCEPTIONS**

#### Why ./start.sh is MANDATORY:
1. **Process Cleanup**: Automatically kills existing Python/Node processes
2. **Port Conflict Prevention**: Prevents "port already in use" errors
3. **Clean State**: Ensures fresh server instances without memory leaks
4. **Dual Server Management**: Properly starts both Backend (8002) + Frontend (5174)
5. **Environment Consistency**: Applies correct environment variables and configs

#### Correct Server Management:
```bash
# ✅ CORRECT - Always use this
./start.sh

# ❌ WRONG - Never use these directly
cd backend && python simple_server.py  # Missing process cleanup
cd frontend && npm run dev              # Missing backend coordination
```

#### Emergency Commands (only if ./start.sh fails):
```bash
# Manual cleanup if needed
taskkill /F /IM python.exe /T
taskkill /F /IM node.exe /T

# Then use ./start.sh
./start.sh
```

#### What ./start.sh Does:
1. 🛑 Stops existing servers (Python + Node processes)
2. 🔍 Force kills processes on ports 8002 and 5174  
3. ⚡ Starts Backend FastAPI server on port 8002
4. 🎨 Starts Frontend React+Vite server on port 5174
5. ✅ Confirms both servers are operational

**Memory Rule: NEVER bypass ./start.sh for server operations. It prevents 90% of development issues.**

---

This system architecture ensures scalability, maintainability, and reliability while meeting enterprise security and performance requirements. 
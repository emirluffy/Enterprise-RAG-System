# Technical Context - Enterprise RAG System

## Technology Stack

### Frontend Technologies
- **React 18.2+**: Latest stable release with concurrent features
- **TypeScript 5.0+**: Type safety and developer experience
- **Tailwind CSS 3.3+**: Utility-first styling framework
- **Headless UI 1.7+**: Unstyled, accessible UI components
- **Zustand 4.4+**: Lightweight state management
- **Vite 4.4+**: Fast development and optimized builds
- **React Query/TanStack Query**: Server state management

### Backend Technologies
- **Python 3.11+**: Latest stable Python with performance improvements
- **FastAPI 0.100+**: Modern async web framework
- **Pydantic 2.0+**: Data validation and settings management
- **Uvicorn**: ASGI server for production
- **Gunicorn**: Process manager for scaling
- **SQLAlchemy 2.0+**: Modern ORM with async support
- **Alembic**: Database migration tool

### Database & Storage
- **PostgreSQL 15+**: Primary database with JSON support
- **pgvector 0.5+**: Vector similarity search extension
- **Redis 7.0+**: Caching and session management
- **MinIO**: S3-compatible object storage (development)
- **AWS S3**: Production file storage
- **Pinecone**: Managed vector database (production)
- **FAISS**: Local vector search (development)

### AI/ML Technologies
- **Google Gemini 2.5 Flash-Lite Preview**: Primary LLM (gemini-2.5-flash-lite-preview-06-17)
- **Google Gemini Embeddings**: gemini-embedding-exp-03-07 (3072 dimensions)
- **OpenAI text-embedding-3-small**: Fallback embeddings
- **Google Cloud Vision API**: OCR for scanned documents
- **Tesseract**: Open-source OCR engine
- **spaCy 3.6+**: Natural language processing
- **NLTK**: Text processing utilities
- **LangChain**: LLM orchestration framework

### DevOps & Infrastructure
- **Docker 24.0+**: Containerization
- **Docker Compose**: Local development environment
- **Kubernetes**: Container orchestration
- **GitHub Actions**: CI/CD pipeline
- **Grafana**: Monitoring and dashboards
- **Prometheus**: Metrics collection
- **ELK Stack**: Centralized logging
- **Nginx**: Reverse proxy and load balancing

## Development Environment Setup

### Prerequisites
```bash
# Required software versions
Node.js >= 18.0.0
Python >= 3.11.0
Docker >= 24.0.0
PostgreSQL >= 15.0
Redis >= 7.0.0
Git >= 2.40.0
```

### Local Development Stack
```yaml
# docker-compose.yml structure
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    
  postgres:
    image: pgvector/pgvector:pg15
    ports: ["5432:5432"]
    
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    
  minio:
    image: minio/minio
    ports: ["9000:9000", "9001:9001"]
```

### Environment Variables
```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost:5432/rag_db
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_secret_key
ENVIRONMENT=development

# Frontend (.env.local)
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development
```

## Technical Constraints

### Performance Requirements
- **Response Time**: <3 seconds for 95th percentile
- **Concurrent Users**: Support 1000 simultaneous users
- **Throughput**: Handle 100 requests/second peak load
- **Memory Usage**: <4GB per backend instance
- **CPU Usage**: <80% average load

### API Rate Limits
- **Gemini Flash-Lite Preview**: 15 RPM, 1000 RPD, 250K TPM
- **OpenAI Embeddings**: 3000 RPM, 200K TPD
- **Google Vision API**: 1800 requests/minute
- **System Rate Limit**: Intelligent queuing to respect upstream limits

### Storage Constraints
- **Document Size**: Maximum 50MB per file
- **Total Storage**: 1TB per tenant
- **Database Size**: PostgreSQL recommended max 1TB
- **Vector Dimensions**: 3072 for gemini-embedding-exp-03-07 (primary), 1536 for text-embedding-3-small (fallback)
- **Index Size**: Optimized for <10M vectors

### Security Constraints
- **Data Residency**: All data must remain in Turkey
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Authentication**: SSO integration mandatory
- **Audit Requirements**: Full audit trail for 7 years
- **GDPR Compliance**: Data subject rights implementation

## Development Workflow

### Git Strategy
- **Main Branch**: Production-ready code
- **Develop Branch**: Integration branch for features
- **Feature Branches**: `feature/RAG-XXX-description`
- **Hotfix Branches**: `hotfix/RAG-XXX-description`
- **Release Branches**: `release/vX.Y.Z`

### Code Quality Standards
```bash
# Frontend
- ESLint + Prettier for code formatting
- TypeScript strict mode enabled
- Jest + React Testing Library for testing
- Husky for pre-commit hooks

# Backend
- Black for code formatting
- Pylint + mypy for static analysis
- pytest for testing
- pre-commit hooks for quality gates
```

### Testing Strategy
- **Unit Tests**: >80% code coverage
- **Integration Tests**: API endpoint testing
- **E2E Tests**: Critical user journeys with Playwright
- **Load Testing**: k6 for performance validation
- **Security Testing**: OWASP ZAP for vulnerability scanning

## Integration Requirements

### External Service Dependencies
- **Active Directory**: SSO authentication
- **SMTP Server**: Email notifications
- **Monitoring Services**: Grafana Cloud (optional)
- **CDN**: CloudFlare for static assets
- **DNS**: Route53 or equivalent

### API Integrations
```python
# Required API clients
gemini_client = GenAI(api_key=GEMINI_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
vision_client = vision.ImageAnnotatorClient()
```

### Database Schema Requirements
```sql
-- Core tables structure
users (id, email, role, created_at, updated_at)
documents (id, filename, content_type, upload_date, processed_at)
document_chunks (id, document_id, content, embedding, metadata)
queries (id, user_id, query_text, response, created_at)
sessions (id, user_id, token, expires_at)
```

## Deployment Architecture

### Production Environment
- **Kubernetes Cluster**: Multi-node setup with auto-scaling
- **Load Balancer**: NGINX Ingress Controller
- **Database**: Managed PostgreSQL with read replicas
- **Caching**: Redis Cluster for high availability
- **Storage**: S3 with CloudFront CDN
- **Monitoring**: Full observability stack

### Staging Environment
- **Single Node**: Cost-optimized Kubernetes setup
- **Database**: Single PostgreSQL instance
- **Storage**: MinIO for S3 compatibility
- **Monitoring**: Essential metrics only

### Development Environment
- **Local Docker**: Complete stack in docker-compose
- **Database**: Local PostgreSQL with pgvector
- **Storage**: Local MinIO instance
- **Hot Reload**: Enabled for rapid development

This technical context ensures all team members understand the technology choices, constraints, and development practices for the Enterprise RAG System. 
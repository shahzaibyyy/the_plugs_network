# The Plugs - Enterprise B2B Networking Platform

**The Plugs** is an enterprise-grade professional networking and event management platform designed for high-volume B2B operations. Built with FastAPI, this backend provides comprehensive APIs for professional networking, event management, and enterprise integrations.

## 🚀 Features

### Professional Networking
- **Advanced Matching Algorithms**: AI-powered professional connections
- **Relationship Tracking**: Comprehensive CRM capabilities
- **Cross-Industry Networking**: Connect professionals across diverse backgrounds

### Event Management
- **Full Lifecycle Management**: Complete event planning and execution
- **Large-Scale Operations**: Handle high-volume corporate events
- **Registration & Ticketing**: Streamlined attendee management

### Enterprise Integration
- **HubSpot Sync**: Seamless CRM integration
- **CSV Export/Import**: Bulk data operations
- **Multi-tenant Architecture**: Complete data isolation per organization

### Infrastructure
- **Microservices Architecture**: Scalable, modular design
- **Background Job Processing**: Celery-powered async operations
- **Enterprise Security**: JWT auth, RBAC, data encryption
- **Comprehensive Monitoring**: Health checks, metrics, logging

## 🛠️ Technology Stack

- **FastAPI**: High-performance Python web framework
- **SQLAlchemy**: Advanced ORM with PostgreSQL
- **Redis**: Caching, sessions, and message broker
- **Celery**: Distributed task queue for background jobs
- **Alembic**: Database migration management
- **Docker**: Containerized deployment
- **Kubernetes**: Container orchestration (production)

## 🏗️ Architecture

```
┌─────────────────┐
│   API Layer     │  ← FastAPI routers, middleware, auth
├─────────────────┤
│  Service Layer  │  ← Business logic, orchestration
├─────────────────┤
│Repository Layer │  ← Data access abstraction
├─────────────────┤
│   Model Layer   │  ← SQLAlchemy models, database entities
└─────────────────┘
```

### Key Principles
- **Clean Architecture**: Dependency inversion and separation of concerns
- **Domain-Driven Design**: Clear business domain boundaries
- **SOLID Principles**: Maintainable, extensible code
- **Multi-Tenant SaaS**: Organization-level data isolation

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd the_plugs_backend
   ```

2. **Run the setup script**
   ```bash
   ./setup.sh
   ```

3. **Configure environment**
   ```bash
   # Edit .env file with your configuration
   cp .env.example .env
   vim .env  # Add your database and Redis URLs
   ```

4. **Start the development server**
   ```bash
   ./scripts/start.sh
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - API Base URL: http://localhost:8000/api/v1

## 📋 Available Scripts

### Development
```bash
./scripts/start.sh          # Start development server
./scripts/test.sh           # Run tests with coverage
./scripts/migrate.sh        # Run database migrations
```

### Testing
```bash
./scripts/test.sh unit      # Run unit tests only
./scripts/test.sh integration # Run integration tests
./scripts/test.sh e2e       # Run end-to-end tests
./scripts/test.sh fast      # Run fast tests (no coverage)
```

### Database Management
```bash
./scripts/migrate.sh                    # Run migrations
./scripts/migrate.sh create "message"   # Create new migration
./scripts/migrate.sh history            # View migration history
./scripts/migrate.sh current            # Show current version
```

## 🗂️ Project Structure

```
the_plugs_backend/
├── app/
│   ├── api/                    # API layer
│   │   └── v1/                 # API version 1
│   ├── config/                 # Configuration management
│   ├── core/                   # Core utilities and dependencies
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic layer
│   ├── repositories/           # Data access layer
│   ├── workers/                # Celery background workers
│   ├── utils/                  # Utility functions
│   └── main.py                 # FastAPI application entry point
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── e2e/                    # End-to-end tests
│   └── fixtures/               # Test data fixtures
├── scripts/                    # Development scripts
├── deployment/                 # Deployment configurations
│   ├── kubernetes/             # K8s manifests
│   ├── helm/                   # Helm charts
│   └── docker/                 # Docker configurations
└── docs/                       # Documentation
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/the_plugs

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External Services
HUBSPOT_API_KEY=your-hubspot-api-key
```

## 🧪 Testing

### Test Structure
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows
- **Fixtures**: Reusable test data

### Running Tests
```bash
# All tests with coverage
./scripts/test.sh

# Specific test types
./scripts/test.sh unit
./scripts/test.sh integration
./scripts/test.sh e2e

# Fast tests (development)
./scripts/test.sh fast
```

### Test Coverage
Coverage reports are generated in `htmlcov/` directory.

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## ☸️ Kubernetes Deployment

### Using Helm
```bash
# Install with Helm
helm upgrade --install the-plugs deployment/helm/ \
  -f deployment/helm/values-production.yaml

# Check deployment
kubectl get pods -n the-plugs
```

### Direct Kubernetes
```bash
# Apply manifests
kubectl apply -f deployment/kubernetes/

# Check status
kubectl get all -n the-plugs
```

## 🔄 Background Workers

### Celery Workers
Start specialized workers for different task types:

```bash
# Email processing
celery -A app.workers.celery_app worker --loglevel=info --queues=email

# Media processing
celery -A app.workers.celery_app worker --loglevel=info --queues=media

# Analytics processing
celery -A app.workers.celery_app worker --loglevel=info --queues=analytics

# Monitor with Flower
celery -A app.workers.celery_app flower
```

### Background Tasks
- **Email Processing**: Welcome emails, notifications, bulk campaigns
- **Media Processing**: File uploads, image optimization
- **Analytics**: Data aggregation, report generation
- **AI Processing**: Matching algorithms, recommendations
- **Cleanup**: Data maintenance, archival

## 📊 Monitoring

### Health Checks
- **Application**: `/health`
- **Database**: `/api/v1/health/database`
- **Redis**: `/api/v1/health/redis`
- **Detailed**: `/metrics`

### Logging
- **Structured JSON logs** for production
- **Correlation IDs** for request tracing
- **Performance metrics** for optimization

## 🔐 Security

### Authentication & Authorization
- **JWT-based authentication** with refresh tokens
- **Role-based access control (RBAC)**
- **Organization-scoped data access**

### Data Protection
- **Encryption at rest and in transit**
- **Input validation** with Pydantic
- **SQL injection protection** via SQLAlchemy
- **Rate limiting** for API endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow **PEP 8** style guidelines
- Write **comprehensive tests** for new features
- Update **documentation** for API changes
- Use **type hints** throughout the codebase

## 📝 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Versioning
- Current version: `v1`
- Base URL: `/api/v1`
- Backward compatibility maintained

### Core Endpoints
- **Authentication**: `/api/v1/auth/*`
- **Users**: `/api/v1/users/*`
- **Organizations**: `/api/v1/organizations/*`
- **Events**: `/api/v1/events/*`
- **Networking**: `/api/v1/networking/*`

## 🚀 Production Deployment

### Environment Setup
1. Configure production environment variables
2. Set up PostgreSQL database with SSL
3. Configure Redis cluster for high availability
4. Set up load balancer and SSL certificates

### Scaling Considerations
- **Horizontal scaling**: Multiple API instances behind load balancer
- **Database optimization**: Connection pooling, read replicas
- **Caching strategy**: Redis for sessions and frequently accessed data
- **Background processing**: Multiple Celery workers with different queues

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Check the [documentation](docs/)
- Open an [issue](issues/)
- Contact the development team

---

**The Plugs** - Connecting professionals, powering growth. 🚀

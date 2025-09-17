# The Plugs - Enterprise B2B Networking Platform

**The Plugs** is an enterprise-grade professional networking and event management platform designed for high-volume B2B operations. Built with FastAPI, this backend provides comprehensive APIs for professional networking, event management, and enterprise integrations.
# The Plugs - Entity Relationship Diagram

## Complete ERD Diagram

```mermaid
erDiagram
    %% Core Entities
    organizations {
        uuid id PK
        string name
        string domain
        string subscription_plan
        json settings
        boolean is_active
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }

    users {
        uuid id PK
        uuid organization_id FK
        string email UK
        string password_hash
        string first_name
        string last_name
        string phone
        text bio
        string avatar_url
        string job_title
        string company
        string linkedin_url
        boolean is_active
        boolean is_verified
        boolean is_admin
        datetime verified_at
        datetime last_login
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        uuid created_by FK
        uuid updated_by FK
    }

    contacts {
        uuid id PK
        uuid organization_id FK
        uuid created_by FK
        string first_name
        string last_name
        string email
        string phone
        string company
        string job_title
        string linkedin_url
        text bio
        string avatar_url
        string contact_type "target|contact|plug"
        string status "new_client|existing_client|hot_lead|cold_lead"
        string priority "high|medium|low"
        string business_type
        string network_type
        string industry
        text notes
        json metadata
        integer lead_score
        datetime last_interaction
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        uuid updated_by FK
    }

    contact_interactions {
        uuid id PK
        uuid organization_id FK
        uuid contact_id FK
        uuid user_id FK
        string interaction_type "meeting|call|email|linkedin|event|follow_up"
        string subject
        text description
        text outcome
        datetime interaction_date
        string status "completed|scheduled|cancelled"
        json metadata
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }

    events {
        uuid id PK
        uuid organization_id FK
        uuid created_by FK
        string title
        text description
        string event_type "conference|workshop|networking|meeting"
        string status "draft|published|ongoing|completed|cancelled"
        datetime start_date
        datetime end_date
        string timezone
        string location
        string venue
        json venue_details
        decimal budget
        string currency
        integer max_attendees
        integer current_attendees
        string registration_url
        json settings
        json metadata
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        uuid updated_by FK
    }

    event_attendees {
        uuid id PK
        uuid organization_id FK
        uuid event_id FK
        uuid user_id FK
        string status "registered|confirmed|attended|no_show|cancelled"
        datetime registration_date
        datetime check_in_time
        datetime check_out_time
        text notes
        json metadata
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }

    event_agenda_items {
        uuid id PK
        uuid organization_id FK
        uuid event_id FK
        uuid created_by FK
        string title
        text description
        datetime start_time
        datetime end_time
        string agenda_type "presentation|break|networking|workshop"
        string location
        uuid speaker_id FK
        integer sort_order
        string status "scheduled|ongoing|completed|cancelled"
        json metadata
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }

    expenses {
        uuid id PK
        uuid organization_id FK
        uuid created_by FK
        uuid event_id FK
        string title
        text description
        decimal amount
        string currency
        string category
        string expense_type "travel|accommodation|catering|venue|marketing|other"
        datetime expense_date
        string status "pending|approved|rejected|paid"
        string receipt_url
        text notes
        uuid approved_by FK
        datetime approved_at
        json metadata
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }

    media {
        uuid id PK
        uuid organization_id FK
        uuid uploaded_by FK
        string title
        text description
        string file_name
        string file_path
        string file_url
        string media_type "image|video|document|audio"
        string mime_type
        bigint file_size
        json metadata
        string status "processing|ready|failed"
        uuid related_event FK
        uuid related_contact FK
        string access_level "public|private|organization"
        json tags
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }

    media_collections {
        uuid id PK
        uuid organization_id FK
        uuid created_by FK
        string name
        text description
        string collection_type "event_photos|contact_media|general"
        json settings
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }

    media_collection_items {
        uuid id PK
        uuid collection_id FK
        uuid media_id FK
        integer sort_order
        datetime created_at
    }

    notifications {
        uuid id PK
        uuid organization_id FK
        uuid user_id FK
        string title
        text message
        string notification_type "info|success|warning|error|reminder"
        string channel "in_app|email|sms|push"
        json data
        boolean is_read
        datetime read_at
        datetime expires_at
        datetime created_at
        datetime updated_at
        boolean is_deleted
    }

    integrations {
        uuid id PK
        uuid organization_id FK
        string provider "hubspot|mailchimp|zoom|teams"
        string integration_type "crm|email|video|calendar"
        json credentials
        json settings
        boolean is_active
        datetime last_sync
        string status "connected|disconnected|error"
        json metadata
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }

    integration_logs {
        uuid id PK
        uuid organization_id FK
        uuid integration_id FK
        string operation "sync|export|import|webhook"
        string status "success|failed|partial"
        text message
        json request_data
        json response_data
        datetime started_at
        datetime completed_at
        integer records_processed
        integer records_failed
        json error_details
        datetime created_at
    }

    analytics_events {
        uuid id PK
        uuid organization_id FK
        uuid user_id FK
        string event_name
        string event_category
        json properties
        string session_id
        string ip_address
        string user_agent
        datetime event_timestamp
        datetime created_at
    }

    audit_logs {
        uuid id PK
        uuid organization_id FK
        uuid user_id FK
        string table_name
        uuid record_id
        string action "create|update|delete|restore"
        json old_values
        json new_values
        json metadata
        datetime created_at
    }

    %% Relationships
    organizations ||--o{ users : "belongs_to"
    organizations ||--o{ contacts : "belongs_to"
    organizations ||--o{ events : "belongs_to"
    organizations ||--o{ media : "belongs_to"
    organizations ||--o{ expenses : "belongs_to"
    organizations ||--o{ notifications : "belongs_to"
    organizations ||--o{ integrations : "belongs_to"

    users ||--o{ contacts : "created_by"
    users ||--o{ events : "created_by"
    users ||--o{ media : "uploaded_by"
    users ||--o{ expenses : "created_by"
    users ||--o{ contact_interactions : "performed_by"
    users ||--o{ event_agenda_items : "created_by"
    users ||--o{ media_collections : "created_by"

    contacts ||--o{ contact_interactions : "has_interactions"
    contacts ||--o{ media : "related_to"

    events ||--o{ event_attendees : "has_attendees"
    events ||--o{ event_agenda_items : "has_agenda_items"
    events ||--o{ expenses : "has_expenses"
    events ||--o{ media : "has_media"

    users ||--o{ event_attendees : "attends"
    users ||--o{ event_agenda_items : "speaks_at"

    media_collections ||--o{ media_collection_items : "contains"
    media ||--o{ media_collection_items : "belongs_to"

    integrations ||--o{ integration_logs : "has_logs"

    users ||--o{ notifications : "receives"
    users ||--o{ analytics_events : "generates"
    users ||--o{ audit_logs : "performs_action"
```

## Key Relationships Explained

### Core Business Relationships

1. **Organization → Users**: Multi-tenant isolation
2. **Users → Contacts**: Professional networking management
3. **Contacts → Interactions**: Relationship tracking
4. **Events → Attendees**: Event participation
5. **Events → Agenda**: Detailed event scheduling
6. **Events → Expenses**: Financial tracking
7. **Media → Collections**: Content organization

### Cross-Entity Relationships

1. **Media ↔ Events**: Event documentation
2. **Media ↔ Contacts**: Contact-related content
3. **Users ↔ Event Attendees**: Participation tracking
4. **Integrations ↔ Logs**: System integration monitoring

## Entity Categories

### **Core Business Entities**
- Organizations, Users, Contacts, Events

### **Relationship Management**
- Contact Interactions, Event Attendees, Event Agenda Items

### **Content Management**
- Media, Media Collections, Media Collection Items

### **Financial Management**
- Expenses

### **Communication**
- Notifications

### **System Integration**
- Integrations, Integration Logs

### **Analytics & Audit**
- Analytics Events, Audit Logs

---

*This ERD represents the complete data model for The Plugs enterprise networking platform, supporting all features shown in the Figma designs.*


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

#!/bin/zsh

# The Plugs - Enterprise B2B Networking Platform Setup Script
# Creates complete project structure with empty files

set -e



# Root level files
touch .env.example .env.local .env.staging .env.production .gitignore .pre-commit-config.yaml
touch docker-compose.yml docker-compose.prod.yml Dockerfile pyproject.toml requirements.txt requirements-dev.txt
touch README.md alembic.ini pytest.ini mypy.ini .flake8 .coveragerc

# Scripts directory
mkdir -p scripts
touch scripts/__init__.py scripts/start.sh scripts/deploy.sh scripts/test.sh scripts/migrate.sh

# Documentation
mkdir -p docs/{api,deployment,architecture}
touch docs/contributing.md

# Main app structure
mkdir -p app/{config,core,models,schemas,services,repositories/interfaces,api/v1,workers,utils,migrations/versions,static/{images,css,js}}

# App root files
touch app/__init__.py app/main.py

# Config files
touch app/config/__init__.py app/config/settings.py app/config/database.py app/config/redis.py app/config/logging.py app/config/security.py

# Core files
touch app/core/__init__.py app/core/dependencies.py app/core/exceptions.py app/core/middleware.py app/core/security.py app/core/pagination.py app/core/events.py app/core/constants.py

# Models - Enterprise B2B focused
touch app/models/__init__.py app/models/base.py app/models/mixins.py
touch app/models/user.py app/models/organization.py app/models/event.py app/models/networking.py
touch app/models/expense.py app/models/media.py app/models/notification.py app/models/analytics.py
touch app/models/tenant.py app/models/integration.py app/models/audit.py

# Schemas
touch app/schemas/__init__.py app/schemas/base.py
touch app/schemas/user.py app/schemas/organization.py app/schemas/event.py app/schemas/networking.py
touch app/schemas/expense.py app/schemas/media.py app/schemas/notification.py app/schemas/analytics.py
touch app/schemas/auth.py app/schemas/common.py app/schemas/tenant.py

# Services - Business logic
touch app/services/__init__.py app/services/base.py
touch app/services/user_service.py app/services/organization_service.py app/services/event_service.py
touch app/services/networking_service.py app/services/expense_service.py app/services/media_service.py
touch app/services/auth_service.py app/services/email_service.py app/services/cache_service.py
touch app/services/notification_service.py app/services/analytics_service.py app/services/ai_service.py
touch app/services/tenant_service.py app/services/integration_service.py

# Repositories - Data access layer
touch app/repositories/__init__.py app/repositories/base.py
touch app/repositories/user_repository.py app/repositories/organization_repository.py app/repositories/event_repository.py
touch app/repositories/networking_repository.py app/repositories/expense_repository.py app/repositories/media_repository.py
touch app/repositories/notification_repository.py app/repositories/analytics_repository.py

# Repository interfaces
touch app/repositories/interfaces/__init__.py
touch app/repositories/interfaces/user_interface.py app/repositories/interfaces/organization_interface.py
touch app/repositories/interfaces/event_interface.py app/repositories/interfaces/networking_interface.py
touch app/repositories/interfaces/expense_interface.py app/repositories/interfaces/media_interface.py

# API endpoints
touch app/api/__init__.py app/api/router.py

# API v1 endpoints
touch app/api/v1/__init__.py app/api/v1/router.py
touch app/api/v1/auth.py app/api/v1/users.py app/api/v1/organizations.py app/api/v1/events.py
touch app/api/v1/networking.py app/api/v1/expenses.py app/api/v1/media.py app/api/v1/notifications.py
touch app/api/v1/analytics.py app/api/v1/health.py app/api/v1/admin.py app/api/v1/tenants.py

# Background workers
touch app/workers/__init__.py app/workers/celery_app.py
touch app/workers/email_worker.py app/workers/media_worker.py app/workers/analytics_worker.py
touch app/workers/notification_worker.py app/workers/ai_worker.py app/workers/cleanup_worker.py

# Utilities
touch app/utils/__init__.py
touch app/utils/datetime.py app/utils/encryption.py app/utils/validators.py app/utils/formatters.py
touch app/utils/file_handler.py app/utils/helpers.py app/utils/ai_helpers.py app/utils/networking_utils.py

# Migrations
touch app/migrations/env.py app/migrations/script.py.mako app/migrations/README.md
touch app/migrations/versions/.gitkeep

# Tests structure
mkdir -p tests/{unit/{test_services,test_repositories,test_utils},integration,e2e,fixtures}

# Test root files
touch tests/__init__.py tests/conftest.py tests/test_config.py

# Unit tests
touch tests/unit/__init__.py
touch tests/unit/test_services/test_user_service.py tests/unit/test_services/test_organization_service.py
touch tests/unit/test_services/test_event_service.py tests/unit/test_services/test_networking_service.py
touch tests/unit/test_services/test_expense_service.py tests/unit/test_services/test_auth_service.py

touch tests/unit/test_repositories/test_user_repository.py tests/unit/test_repositories/test_organization_repository.py
touch tests/unit/test_repositories/test_event_repository.py tests/unit/test_repositories/test_networking_repository.py

touch tests/unit/test_utils/test_datetime.py tests/unit/test_utils/test_encryption.py
touch tests/unit/test_utils/test_validators.py tests/unit/test_utils/test_networking_utils.py

# Integration tests
touch tests/integration/__init__.py
touch tests/integration/test_auth_flow.py tests/integration/test_user_crud.py tests/integration/test_organization_crud.py
touch tests/integration/test_event_crud.py tests/integration/test_networking_flow.py tests/integration/test_expense_flow.py

# E2E tests
touch tests/e2e/__init__.py
touch tests/e2e/test_api_endpoints.py tests/e2e/test_user_journey.py tests/e2e/test_event_journey.py
touch tests/e2e/test_networking_journey.py

# Test fixtures
touch tests/fixtures/__init__.py tests/fixtures/database.py
touch tests/fixtures/users.py tests/fixtures/organizations.py tests/fixtures/events.py
touch tests/fixtures/networking.py tests/fixtures/expenses.py

# Monitoring
mkdir -p monitoring
touch monitoring/__init__.py monitoring/metrics.py monitoring/health_checks.py monitoring/tracing.py monitoring/alerting.py

# Deployment
mkdir -p deployment/{kubernetes,helm/templates,terraform/modules,nginx/ssl}

# Kubernetes manifests
touch deployment/kubernetes/namespace.yaml deployment/kubernetes/deployment.yaml
touch deployment/kubernetes/service.yaml deployment/kubernetes/ingress.yaml
touch deployment/kubernetes/configmap.yaml deployment/kubernetes/secrets.yaml

# Helm charts
touch deployment/helm/Chart.yaml deployment/helm/values.yaml
touch deployment/helm/values-staging.yaml deployment/helm/values-production.yaml
touch deployment/helm/templates/.gitkeep

# Terraform
touch deployment/terraform/main.tf deployment/terraform/variables.tf deployment/terraform/outputs.tf
touch deployment/terraform/modules/.gitkeep

# Nginx
touch deployment/nginx/nginx.conf deployment/nginx/ssl/.gitkeep

# GitHub Actions
mkdir -p .github/workflows
touch .github/workflows/ci.yml .github/workflows/cd.yml
touch .github/workflows/security-scan.yml .github/workflows/dependency-update.yml

echo "✅ The Plugs project structure created successfully!"
echo "📁 Project location: $(pwd)"
echo ""
echo "Next steps:"
echo "1. cd $PROJECT_NAME"
echo "2. Create virtual environment: python -m venv venv"
echo "3. Activate venv: source venv/bin/activate"
echo "4. Install dependencies: pip install -r requirements.txt"
echo "5. Copy .env.example to .env and configure"
echo "6. Run: uvicorn app.main:app --reload"
echo ""
echo "🚀 Happy coding with The Plugs!"
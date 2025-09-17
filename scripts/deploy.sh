#!/bin/bash

# Studagent Deployment Script
# This script handles deployment to staging and production environments

set -e

# Configuration
APP_NAME="studagent"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io}"
DOCKER_USERNAME="${DOCKER_USERNAME:-your-username}"
DOCKER_REPO="${DOCKER_REGISTRY}/${DOCKER_USERNAME}/${APP_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    log_info "Dependencies check passed."
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."

    cd backend
    docker build -t ${DOCKER_REPO}/backend:latest .
    docker build -t ${DOCKER_REPO}/backend:${GITHUB_SHA:-latest} .

    cd ../frontend
    # Assuming you have a frontend Dockerfile
    # docker build -t ${DOCKER_REPO}/frontend:latest .

    log_info "Docker images built successfully."
}

# Push images to registry
push_images() {
    log_info "Pushing images to registry..."

    echo "${DOCKER_PASSWORD}" | docker login ${DOCKER_REGISTRY} -u ${DOCKER_USERNAME} --password-stdin

    docker push ${DOCKER_REPO}/backend:latest
    docker push ${DOCKER_REPO}/backend:${GITHUB_SHA:-latest}

    log_info "Images pushed successfully."
}

# Deploy to staging
deploy_staging() {
    log_info "Deploying to staging environment..."

    # Create staging environment file
    cat > .env.staging << EOF
DATABASE_URL=postgresql://user:password@db:5432/studagent_staging
REDIS_URL=redis://redis:6379/0
SECRET_KEY=${SECRET_KEY}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}
GROQ_API_KEY=${GROQ_API_KEY}
ENVIRONMENT=staging
DEBUG=False
EOF

    # Deploy using docker-compose
    docker-compose -f docker-compose.staging.yml up -d

    log_info "Staging deployment completed."
}

# Deploy to production
deploy_production() {
    log_info "Deploying to production environment..."

    # Create production environment file
    cat > .env.production << EOF
DATABASE_URL=postgresql://user:password@db:5432/studagent_prod
REDIS_URL=redis://redis:6379/0
SECRET_KEY=${SECRET_KEY}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}
GROQ_API_KEY=${GROQ_API_KEY}
ENVIRONMENT=production
DEBUG=False
EOF

    # Deploy using docker-compose
    docker-compose -f docker-compose.production.yml up -d

    log_info "Production deployment completed."
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."

    docker-compose exec backend alembic upgrade head

    log_info "Database migrations completed."
}

# Health check
health_check() {
    log_info "Performing health check..."

    # Wait for services to be ready
    sleep 30

    # Check backend health
    if curl -f http://localhost:8000/api/v1/health; then
        log_info "Backend health check passed."
    else
        log_error "Backend health check failed."
        exit 1
    fi

    # Check frontend health (if applicable)
    # if curl -f http://localhost:3000; then
    #     log_info "Frontend health check passed."
    # else
    #     log_error "Frontend health check failed."
    #     exit 1
    # fi
}

# Rollback deployment
rollback() {
    log_info "Rolling back deployment..."

    # Stop current deployment
    docker-compose down

    # Start previous version
    docker-compose pull
    docker-compose up -d

    log_info "Rollback completed."
}

# Main deployment function
main() {
    local environment=${1:-staging}

    log_info "Starting deployment to ${environment}..."

    check_dependencies

    case ${environment} in
        staging)
            build_images
            push_images
            deploy_staging
            run_migrations
            health_check
            ;;
        production)
            # For production, assume images are already built and pushed
            deploy_production
            run_migrations
            health_check
            ;;
        rollback)
            rollback
            ;;
        *)
            log_error "Invalid environment: ${environment}"
            log_info "Usage: $0 [staging|production|rollback]"
            exit 1
            ;;
    esac

    log_info "Deployment to ${environment} completed successfully! 🎉"
}

# Run main function with provided arguments
main "$@"
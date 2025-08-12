#!/bin/bash

# Lawyerless Development Environment Setup Script
# This script sets up the complete development environment for Lawyerless

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Docker
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        print_status "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        print_status "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check Git
    if ! command_exists git; then
        print_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "All system requirements met!"
}

# Function to setup environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    cd "$PROJECT_ROOT"
    
    # Copy main environment file
    if [ ! -f ".env.local" ]; then
        cp ".env.example" ".env.local"
        print_success "Created .env.local from .env.example"
        print_warning "Please edit .env.local and add your API keys!"
        print_warning "Required: OPENAI_API_KEY or ANTHROPIC_API_KEY"
    else
        print_status ".env.local already exists"
    fi
    
    # Backend environment
    if [ ! -f "backend/.env.local" ]; then
        cp ".env.example" "backend/.env.local"
        print_success "Created backend/.env.local"
    fi
    
    # Frontend environment
    if [ ! -f "frontend/.env.local" ]; then
        cp "frontend/.env.local.example" "frontend/.env.local" 2>/dev/null || {
            cat > "frontend/.env.local" << EOF
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_APP_VERSION=1.0.0-dev
NEXT_PUBLIC_ENABLE_DEBUG=true
NEXT_TELEMETRY_DISABLED=1
EOF
        }
        print_success "Created frontend/.env.local"
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    cd "$PROJECT_ROOT"
    
    # Create Docker config directories
    mkdir -p docker/redis
    mkdir -p docker/postgres
    mkdir -p docker/nginx
    mkdir -p docker/prometheus
    mkdir -p docker/grafana/provisioning
    
    # Create data directories
    mkdir -p data/uploads
    mkdir -p data/temp
    mkdir -p logs
    mkdir -p tmp
    
    # Set permissions
    chmod 755 data/uploads data/temp logs tmp
    
    print_success "Created project directories"
}

# Function to check API keys
check_api_keys() {
    print_status "Checking API keys configuration..."
    
    if [ -f ".env.local" ]; then
        if grep -q "your_openai_api_key_here" ".env.local" && grep -q "your_anthropic_api_key_here" ".env.local"; then
            print_warning "API keys not configured in .env.local"
            print_warning "Please edit .env.local and add either OPENAI_API_KEY or ANTHROPIC_API_KEY"
            print_status "You can continue setup and add keys later, but analysis won't work without them."
            
            read -p "Continue setup without API keys? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_status "Please configure API keys in .env.local and run this script again."
                exit 1
            fi
        else
            print_success "API keys appear to be configured"
        fi
    fi
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build backend image
    print_status "Building backend image..."
    docker build -f backend/Dockerfile.dev -t lawyerless-backend:dev backend/
    
    # Build frontend image
    print_status "Building frontend image..."
    docker build -f frontend/Dockerfile.dev -t lawyerless-frontend:dev frontend/
    
    print_success "Docker images built successfully"
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    cd "$PROJECT_ROOT"
    
    # Start core services
    docker-compose up -d redis database
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Start main application services
    docker-compose up -d backend frontend
    
    print_success "Services started!"
}

# Function to check service health
check_health() {
    print_status "Checking service health..."
    
    # Wait a bit for services to fully start
    sleep 30
    
    # Check backend health
    if curl -s -f "http://localhost:8000/health" >/dev/null; then
        print_success "Backend is healthy (http://localhost:8000)"
    else
        print_warning "Backend health check failed"
        print_status "Check logs: docker-compose logs backend"
    fi
    
    # Check frontend health
    if curl -s -f "http://localhost:3000" >/dev/null; then
        print_success "Frontend is healthy (http://localhost:3000)"
    else
        print_warning "Frontend health check failed"
        print_status "Check logs: docker-compose logs frontend"
    fi
    
    # Check Redis
    if docker-compose exec redis redis-cli ping >/dev/null 2>&1; then
        print_success "Redis is healthy"
    else
        print_warning "Redis health check failed"
    fi
}

# Function to show final status
show_status() {
    print_status "=== Lawyerless Development Environment Status ==="
    echo
    print_status "🌐 Frontend: http://localhost:3000"
    print_status "🚀 Backend API: http://localhost:8000"
    print_status "📚 API Docs: http://localhost:8000/docs"
    print_status "🔧 Redis: localhost:6379"
    print_status "🐘 PostgreSQL: localhost:5432"
    echo
    print_status "=== Useful Commands ==="
    echo "  View logs:           docker-compose logs -f [service]"
    echo "  Stop services:       docker-compose down"
    echo "  Restart service:     docker-compose restart [service]"
    echo "  Run backend shell:   docker-compose exec backend bash"
    echo "  Run frontend shell:  docker-compose exec frontend sh"
    echo "  View status:         docker-compose ps"
    echo
    print_success "Development environment is ready!"
    echo
    if [ -f ".env.local" ] && grep -q "your_.*_api_key_here" ".env.local"; then
        print_warning "⚠️  Remember to configure your API keys in .env.local"
        print_warning "   Contract analysis won't work without proper LLM API keys!"
    fi
}

# Function to cleanup on error
cleanup_on_error() {
    print_error "Setup failed. Cleaning up..."
    docker-compose down 2>/dev/null || true
}

# Main execution
main() {
    print_status "🚀 Starting Lawyerless Development Environment Setup"
    echo
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    # Run setup steps
    check_requirements
    setup_environment
    create_directories
    check_api_keys
    build_images
    start_services
    check_health
    show_status
    
    print_success "🎉 Setup completed successfully!"
}

# Handle command line arguments
case "$1" in
    --check-only)
        check_requirements
        print_success "System requirements check passed!"
        ;;
    --env-only)
        setup_environment
        create_directories
        print_success "Environment setup completed!"
        ;;
    --build-only)
        build_images
        print_success "Docker images built!"
        ;;
    --start-only)
        start_services
        check_health
        show_status
        ;;
    --help|-h)
        echo "Lawyerless Development Environment Setup Script"
        echo
        echo "Usage: $0 [option]"
        echo
        echo "Options:"
        echo "  --check-only    Only check system requirements"
        echo "  --env-only      Only setup environment files and directories"
        echo "  --build-only    Only build Docker images"
        echo "  --start-only    Only start services (assumes images are built)"
        echo "  --help, -h      Show this help message"
        echo
        echo "Default: Run full setup process"
        ;;
    *)
        main
        ;;
esac
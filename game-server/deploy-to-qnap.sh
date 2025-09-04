#!/bin/bash

# Planetarion QNAP Deployment Script
# This script deploys the optimized Planetarion game server to QNAP NAS

set -e  # Exit on any error

# Load configuration from environment or local file
load_config() {
    # Try to load from .qnap-deploy.env file first
    if [[ -f ".qnap-deploy.env" ]]; then
        log_info "Loading configuration from .qnap-deploy.env"
        source .qnap-deploy.env
    fi

    # Check if required variables are set
    if [[ -z "$QNAP_IP" ]]; then
        log_error "QNAP_IP environment variable is not set"
        log_info "Please set it with: export QNAP_IP='your-qnap-ip'"
        log_info "Or create .qnap-deploy.env file with your configuration"
        exit 1
    fi

    if [[ -z "$QNAP_USER" ]]; then
        log_error "QNAP_USER environment variable is not set"
        log_info "Please set it with: export QNAP_USER='your-username'"
        log_info "Or create .qnap-deploy.env file with your configuration"
        exit 1
    fi

    # Set defaults for optional variables
    QNAP_PROJECT_DIR=${QNAP_PROJECT_DIR:-"/share/CACHEDEV1_DATA/planetarion"}
    DOCKER_COMPOSE_FILE=${DOCKER_COMPOSE_FILE:-"docker-compose.qnap.yml"}
    QNAP_SSH_KEY=${QNAP_SSH_KEY:-""}

    log_info "Configuration loaded:"
    log_info "  QNAP IP: $QNAP_IP"
    log_info "  QNAP User: $QNAP_USER"
    log_info "  Project Dir: $QNAP_PROJECT_DIR"
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if SSH key exists (multiple possible names)
    SSH_KEY_FOUND=false
    for key_name in id_rsa qnap_key; do
        if [[ -f ~/.ssh/${key_name} ]]; then
            SSH_KEY_FILE=~/.ssh/${key_name}
            SSH_KEY_FOUND=true
            log_success "Found SSH key: ${key_name}"
            break
        fi
    done

    if [[ $SSH_KEY_FOUND == false ]]; then
        log_error "SSH key not found. Please generate one with: ssh-keygen -t rsa -b 4096"
        log_info "Or ensure your SSH key is in ~/.ssh/ (supported names: id_rsa, qnap_key)"
        exit 1
    fi

    # Check if Docker is available locally (for building)
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed locally. Please install Docker first."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Setup SSH access to QNAP
setup_ssh_access() {
    log_info "Setting up SSH access to QNAP..."

    # Determine public key file name
    SSH_PUB_KEY="${SSH_KEY_FILE}.pub"

    # Copy SSH public key to QNAP (you may need to enter password first time)
    if [[ -f "$SSH_PUB_KEY" ]]; then
        ssh-copy-id -i "$SSH_PUB_KEY" ${QNAP_USER}@${QNAP_IP} 2>/dev/null || {
            log_warning "SSH key copy failed. You may need to:"
            log_warning "1. Connect manually: ssh -i ${SSH_KEY_FILE} ${QNAP_USER}@${QNAP_IP}"
            log_warning "2. Add your SSH key to ~/.ssh/authorized_keys on QNAP"
            log_warning "3. Or use certificate authentication as you mentioned"
            read -p "Press Enter to continue after setting up SSH access..."
        }
    else
        log_warning "SSH public key not found: $SSH_PUB_KEY"
        log_warning "You may need to set up SSH key authentication manually"
        read -p "Press Enter to continue..."
    fi

    # Test SSH connection
    if ssh -o ConnectTimeout=10 -i "$SSH_KEY_FILE" ${QNAP_USER}@${QNAP_IP} "echo 'SSH connection successful'" &>/dev/null; then
        log_success "SSH connection established"
    else
        log_error "SSH connection failed. Please check your credentials and network."
        exit 1
    fi
}

# Prepare QNAP environment
prepare_qnap() {
    log_info "Preparing QNAP environment..."

    # Create project directory
    ssh ${QNAP_USER}@${QNAP_IP} "mkdir -p ${QNAP_PROJECT_DIR}"

    # Check if Docker is installed on QNAP
    if ! ssh ${QNAP_USER}@${QNAP_IP} "which docker" &>/dev/null; then
        log_error "Docker is not installed on QNAP. Please install Container Station or Docker."
        exit 1
    fi

    # Check if docker-compose is available
    if ! ssh ${QNAP_USER}@${QNAP_IP} "which docker-compose" &>/dev/null; then
        log_warning "docker-compose not found. Using 'docker compose' (Docker Compose V2)"
        DOCKER_COMPOSE_CMD="docker compose"
    else
        DOCKER_COMPOSE_CMD="docker-compose"
    fi

    # Create Docker data directory
    ssh ${QNAP_USER}@${QNAP_IP} "mkdir -p /share/CACHEDEV1_DATA/Docker/postgres_data"

    log_success "QNAP environment prepared"
}

# Build and push images
build_images() {
    log_info "Building optimized Docker images..."

    # Build backend image
    log_info "Building backend image..."
    docker build -f src/backend/Dockerfile -t planetarion-backend:qnap src/

    # Build frontend image
    log_info "Building frontend image..."
    docker build -f src/frontend/Dockerfile -t planetarion-frontend:qnap src/frontend/

    log_success "Images built successfully"
}

# Deploy to QNAP
deploy_to_qnap() {
    log_info "Deploying to QNAP..."

    # Copy docker-compose file
    scp ${DOCKER_COMPOSE_FILE} ${QNAP_USER}@${QNAP_IP}:${QNAP_PROJECT_DIR}/

    # Copy source code (read-only for containers)
    log_info "Copying source code..."
    rsync -avz --delete --exclude='node_modules' --exclude='__pycache__' --exclude='.git' \
        ./src/ ${QNAP_USER}@${QNAP_IP}:${QNAP_PROJECT_DIR}/src/

    # Load images on QNAP (if using Container Station)
    log_info "Loading images on QNAP..."
    docker save planetarion-backend:qnap | ssh ${QNAP_USER}@${QNAP_IP} "docker load"
    docker save planetarion-frontend:qnap | ssh ${QNAP_USER}@${QNAP_IP} "docker load"

    # Alternative: Build directly on QNAP
    log_warning "If image loading fails, images will be built directly on QNAP"

    # Start services
    log_info "Starting services..."
    ssh ${QNAP_USER}@${QNAP_IP} "cd ${QNAP_PROJECT_DIR} && ${DOCKER_COMPOSE_CMD} -f ${DOCKER_COMPOSE_FILE} up -d --build"

    log_success "Deployment completed!"
}

# Check deployment status
check_deployment() {
    log_info "Checking deployment status..."

    # Wait a moment for services to start
    sleep 10

    # Check if services are running
    ssh ${QNAP_USER}@${QNAP_IP} "cd ${QNAP_PROJECT_DIR} && ${DOCKER_COMPOSE_CMD} -f ${DOCKER_COMPOSE_FILE} ps"

    # Test backend health
    if curl -f http://${QNAP_IP}:5000/api/planet &>/dev/null; then
        log_success "Backend is responding"
    else
        log_warning "Backend health check failed - it may still be starting"
    fi

    # Test frontend
    if curl -f http://${QNAP_IP}:3000/ &>/dev/null; then
        log_success "Frontend is responding"
    else
        log_warning "Frontend health check failed - it may still be starting"
    fi
}

# Show access information
show_access_info() {
    log_success "Planetarion is now running on your QNAP!"
    echo ""
    echo "Access URLs:"
    echo "  Frontend: http://${QNAP_IP}:3000"
    echo "  Backend API: http://${QNAP_IP}:5000"
    echo ""
    echo "To check logs:"
    echo "  ssh ${QNAP_USER}@${QNAP_IP}"
    echo "  cd ${QNAP_PROJECT_DIR}"
    echo "  ${DOCKER_COMPOSE_CMD} -f ${DOCKER_COMPOSE_FILE} logs -f"
    echo ""
    echo "To restart services:"
    echo "  ${DOCKER_COMPOSE_CMD} -f ${DOCKER_COMPOSE_FILE} restart"
    echo ""
    echo "To stop services:"
    echo "  ${DOCKER_COMPOSE_CMD} -f ${DOCKER_COMPOSE_FILE} down"
}

# Test connectivity first
test_connectivity() {
    log_info "Running connectivity tests..."

    if [[ -f "./test-qnap-connectivity.sh" ]]; then
        if ./test-qnap-connectivity.sh; then
            log_success "All connectivity tests passed!"
        else
            log_error "Connectivity tests failed. Please resolve the issues above before proceeding."
            exit 1
        fi
    else
        log_warning "Connectivity test script not found. Proceeding without tests..."
        log_info "You can run connectivity tests separately with: ./test-qnap-connectivity.sh"
    fi
}

# Main deployment process
main() {
    echo "🚀 Planetarion QNAP Deployment Script"
    echo "===================================="

    # Load configuration first
    load_config
    echo ""

    # Always test connectivity first
    test_connectivity
    echo ""

    check_prerequisites
    setup_ssh_access
    prepare_qnap
    build_images
    deploy_to_qnap
    check_deployment
    show_access_info

    log_success "Deployment completed successfully!"
    log_info "Your Planetarion game server is now running on QNAP at ${QNAP_IP}"
}

# Run main function
main "$@"

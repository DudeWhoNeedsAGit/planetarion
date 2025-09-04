#!/bin/bash

# Simple Planetarion QNAP Deployment Script (No connectivity test)
# This script deploys the optimized Planetarion game server to QNAP NAS

set -e  # Exit on any error

# Configuration
QNAP_IP="${QNAP_IP}"  # Use environment variable or default
QNAP_USER="${QNAP_USER:-admin}"      # Use environment variable or default
PROJECT_DIR="/share/CACHEDEV1_DATA/planetarion"
DOCKER_COMPOSE_FILE="docker-compose.qnap.yml"

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

# Load configuration from .qnap-deploy.env if it exists
if [[ -f ".qnap-deploy.env" ]]; then
    log_info "Loading configuration from .qnap-deploy.env"
    source .qnap-deploy.env
fi

log_info "Configuration loaded:"
log_info "  QNAP IP: $QNAP_IP"
log_info "  QNAP User: $QNAP_USER"
log_info "  Project Dir: $QNAP_PROJECT_DIR"

# Check if Docker is available locally
log_info "Checking local Docker..."
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed locally. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker is not running. Please start Docker first."
    exit 1
fi

log_success "Local Docker is working"

# Check if SSH key exists
log_info "Checking SSH keys..."
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
    exit 1
fi

# Build optimized images
log_info "Building optimized Docker images..."
log_info "Building backend image..."
docker build -f src/backend/Dockerfile -t planetarion-backend:qnap src/

log_info "Building frontend image..."
docker build -f src/frontend/Dockerfile -t planetarion-frontend:qnap src/frontend/

log_success "Images built successfully"

# Deploy to QNAP
log_info "Deploying to QNAP..."

# Create project directory first
log_info "Creating project directory on QNAP..."
ssh -i "$SSH_KEY_FILE" -o PasswordAuthentication=no -o StrictHostKeyChecking=no ${QNAP_USER}@${QNAP_IP} "mkdir -p ${QNAP_PROJECT_DIR}"

# Copy docker-compose file
log_info "Copying docker-compose file..."
scp -i "$SSH_KEY_FILE" -o PasswordAuthentication=no -o StrictHostKeyChecking=no ${DOCKER_COMPOSE_FILE} ${QNAP_USER}@${QNAP_IP}:${QNAP_PROJECT_DIR}/

# Copy source code
log_info "Copying source code..."
rsync -avz --delete --exclude='node_modules' --exclude='__pycache__' --exclude='.git' \
    -e "ssh -i $SSH_KEY_FILE -o PasswordAuthentication=no -o StrictHostKeyChecking=no" \
    ./src/ ${QNAP_USER}@${QNAP_IP}:${QNAP_PROJECT_DIR}/src/

# Load images on QNAP
log_info "Loading images on QNAP..."
DOCKER_PATH="/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker"
docker save planetarion-backend:qnap | ssh -i "$SSH_KEY_FILE" -o PasswordAuthentication=no -o StrictHostKeyChecking=no ${QNAP_USER}@${QNAP_IP} "${DOCKER_PATH} load"
docker save planetarion-frontend:qnap | ssh -i "$SSH_KEY_FILE" -o PasswordAuthentication=no -o StrictHostKeyChecking=no ${QNAP_USER}@${QNAP_IP} "${DOCKER_PATH} load"

# Start services
log_info "Starting services on QNAP..."
ssh -i "$SSH_KEY_FILE" -o PasswordAuthentication=no -o StrictHostKeyChecking=no ${QNAP_USER}@${QNAP_IP} "cd ${QNAP_PROJECT_DIR} && ${DOCKER_PATH} compose -f ${DOCKER_COMPOSE_FILE} up -d --build"

log_success "Deployment completed!"

# Wait a moment for services to start
log_info "Waiting for services to start..."
sleep 15

# Test deployment
log_info "Testing deployment..."

# Test backend
if curl -f http://${QNAP_IP}:5000/api/planet &>/dev/null; then
    log_success "Backend is responding at http://${QNAP_IP}:5000"
else
    log_warning "Backend health check failed - it may still be starting"
fi

# Test frontend
if curl -f http://${QNAP_IP}:3000/ &>/dev/null; then
    log_success "Frontend is responding at http://${QNAP_IP}:3000"
else
    log_warning "Frontend health check failed - it may still be starting"
fi

# Final success message
log_success "🎉 Planetarion deployment completed!"
echo ""
echo "Access your game at:"
echo "  Frontend: http://${QNAP_IP}:3000"
echo "  Backend API: http://${QNAP_IP}:5000"
echo ""
echo "To check logs on QNAP:"
echo "  ssh ${QNAP_USER}@${QNAP_IP}"
echo "  cd ${QNAP_PROJECT_DIR}"
echo "  docker-compose -f ${DOCKER_COMPOSE_FILE} logs -f"

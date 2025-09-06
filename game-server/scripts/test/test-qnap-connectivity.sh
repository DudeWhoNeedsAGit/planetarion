#!/bin/bash

# Planetarion QNAP Connectivity Test
# Tests all prerequisites before deployment

set -e  # Exit on any error

# Load configuration from environment or local file
load_config() {
    # Try to load from .qnap-deploy.env file first
    if [[ -f ".qnap-deploy.env" ]]; then
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
}

# Load configuration at the beginning
load_config

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_TOTAL=0

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    ((TESTS_PASSED++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    ((TESTS_TOTAL++))
}

# Test local prerequisites
test_local_prerequisites() {
    log_info "Testing local prerequisites..."

    # Test Docker
    log_test "Docker availability"
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            log_success "Docker is running and accessible"
        else
            log_error "Docker is installed but not running. Start Docker first."
            exit 1
        fi
    else
        log_error "Docker is not installed. Please install Docker."
        exit 1
    fi

    # Test SSH client
    log_test "SSH client availability"
    if command -v ssh &> /dev/null; then
        log_success "SSH client is available"
    else
        log_error "SSH client is not available"
        exit 1
    fi

    # Test network connectivity to QNAP
    log_test "Network connectivity to QNAP"
    if ping -c 3 -W 5 ${QNAP_IP} &> /dev/null; then
        log_success "Network connectivity to ${QNAP_IP} is working"
    else
        log_error "Cannot reach ${QNAP_IP}. Check network connectivity."
        exit 1
    fi

    # Test required ports
    log_test "Port 22 (SSH) availability"
    if nc -z -w5 ${QNAP_IP} 22 &> /dev/null; then
        log_success "SSH port (22) is open on QNAP"
    else
        log_error "SSH port (22) is not accessible on QNAP"
        log_info "Make sure SSH is enabled in QNAP Control Panel > Network & File Services > Telnet/SSH"
        exit 1
    fi

    # Test target ports (should be free)
    log_test "Port 5000 availability"
    if nc -z -w5 ${QNAP_IP} 5000 &> /dev/null; then
        log_warning "Port 5000 is already in use on QNAP"
        log_info "This might be okay if you're updating an existing deployment"
    else
        log_success "Port 5000 is available on QNAP"
    fi

    log_test "Port 3000 availability"
    if nc -z -w5 ${QNAP_IP} 3000 &> /dev/null; then
        log_warning "Port 3000 is already in use on QNAP"
        log_info "This might be okay if you're updating an existing deployment"
    else
        log_success "Port 3000 is available on QNAP"
    fi
}

# Test SSH access
test_ssh_access() {
    log_info "Testing SSH access to QNAP..."

    # Test SSH key authentication first (try multiple key names)
    SSH_KEY_FOUND=false
    for key_name in id_rsa qnap_key; do
        if [[ -f ~/.ssh/${key_name} ]]; then
            log_test "SSH key authentication (${key_name})"
            if ssh -o ConnectTimeout=10 -o BatchMode=yes -i ~/.ssh/${key_name} ${QNAP_USER}@${QNAP_IP} "echo 'SSH key auth successful'" &>/dev/null; then
                log_success "SSH key authentication is working (${key_name})"
                SSH_KEY_FOUND=true
                return 0
            fi
        fi
    done

    if [[ $SSH_KEY_FOUND == false ]]; then
        log_warning "No working SSH keys found, trying password authentication..."
    fi

    # Test password authentication
    log_test "SSH password authentication"
    if ssh -o ConnectTimeout=10 -o NumberOfPasswordPrompts=1 ${QNAP_USER}@${QNAP_IP} "echo 'SSH password auth successful'" &>/dev/null; then
        log_success "SSH password authentication is working"
    else
        log_error "SSH authentication failed"
        log_info "Please ensure:"
        log_info "1. SSH is enabled on QNAP"
        log_info "2. Your username/password is correct"
        log_info "3. Or set up SSH key authentication (supported keys: id_rsa, qnap_key)"
        exit 1
    fi
}

# Test QNAP system
test_qnap_system() {
    log_info "Testing QNAP system..."

    # Test basic commands
    log_test "Basic QNAP system access"
    if ssh ${QNAP_USER}@${QNAP_IP} "uname -a" &>/dev/null; then
        log_success "Basic system access is working"
    else
        log_error "Cannot execute basic commands on QNAP"
        exit 1
    fi

    # Test Docker availability
    log_test "Docker availability on QNAP"
    if ssh ${QNAP_USER}@${QNAP_IP} "which docker" &>/dev/null; then
        log_success "Docker is installed on QNAP"
    else
        log_error "Docker is not installed on QNAP"
        log_info "Please install Container Station from QNAP App Center"
        exit 1
    fi

    # Test Docker functionality
    log_test "Docker functionality on QNAP"
    if ssh ${QNAP_USER}@${QNAP_IP} "docker version" &>/dev/null; then
        log_success "Docker is working on QNAP"
    else
        log_error "Docker is not functioning properly on QNAP"
        log_info "Make sure Container Station is running"
        exit 1
    fi

    # Test docker-compose availability
    log_test "Docker Compose availability"
    if ssh ${QNAP_USER}@${QNAP_IP} "which docker-compose || which docker" | grep -q "docker"; then
        log_success "Docker Compose or Docker CLI is available"
    else
        log_error "Neither docker-compose nor docker CLI found"
        exit 1
    fi

    # Test storage space
    log_test "Available storage space"
    STORAGE_INFO=$(ssh ${QNAP_USER}@${QNAP_IP} "df -h /share/CACHEDEV1_DATA" | tail -1)
    AVAILABLE=$(echo $STORAGE_INFO | awk '{print $4}')
    log_info "Available storage: $AVAILABLE"

    # Convert available space to MB for comparison
    AVAILABLE_MB=$(ssh ${QNAP_USER}@${QNAP_IP} "df /share/CACHEDEV1_DATA | tail -1 | awk '{print int(\$4/1024)}'")
    if [[ $AVAILABLE_MB -gt 1024 ]]; then  # More than 1GB
        log_success "Sufficient storage space available ($AVAILABLE_MB MB)"
    else
        log_warning "Limited storage space ($AVAILABLE_MB MB). Deployment might work but consider cleanup."
    fi

    # Test directory creation
    log_test "Directory creation permissions"
    if ssh ${QNAP_USER}@${QNAP_IP} "mkdir -p /share/CACHEDEV1_DATA/planetarion_test && rmdir /share/CACHEDEV1_DATA/planetarion_test"; then
        log_success "Directory creation permissions are working"
    else
        log_error "Cannot create directories on QNAP storage"
        log_info "Check your user permissions on QNAP"
        exit 1
    fi
}

# Test deployment simulation
test_deployment_simulation() {
    log_info "Testing deployment simulation..."

    # Test file transfer
    log_test "File transfer capability"
    echo "test file for connectivity check" > /tmp/qnap_test_file.txt
    if scp /tmp/qnap_test_file.txt ${QNAP_USER}@${QNAP_IP}:/tmp/ &>/dev/null; then
        log_success "File transfer to QNAP is working"
        ssh ${QNAP_USER}@${QNAP_IP} "rm -f /tmp/qnap_test_file.txt" &>/dev/null
    else
        log_error "File transfer to QNAP failed"
        exit 1
    fi
    rm -f /tmp/qnap_test_file.txt

    # Test Docker image operations
    log_test "Docker image operations"
    if ssh ${QNAP_USER}@${QNAP_IP} "docker pull alpine:latest && docker rmi alpine:latest" &>/dev/null; then
        log_success "Docker image operations are working"
    else
        log_warning "Docker image operations may be slow or have issues"
        log_info "This might be okay for deployment but could be slower"
    fi
}

# Show summary
show_summary() {
    echo ""
    echo "========================================"
    echo "🧪 CONNECTIVITY TEST SUMMARY"
    echo "========================================"

    SUCCESS_RATE=$((TESTS_PASSED * 100 / TESTS_TOTAL))

    if [[ $SUCCESS_RATE -eq 100 ]]; then
        echo -e "${GREEN}✅ ALL TESTS PASSED ($TESTS_PASSED/$TESTS_TOTAL)${NC}"
        echo ""
        echo "🎉 Your system is ready for Planetarion deployment!"
        echo "Run the deployment script:"
        echo "  ./deploy-to-qnap.sh"
    elif [[ $SUCCESS_RATE -ge 75 ]]; then
        echo -e "${YELLOW}⚠️ MOST TESTS PASSED ($TESTS_PASSED/$TESTS_TOTAL)${NC}"
        echo ""
        echo "Your system should work for deployment, but check the warnings above."
    else
        echo -e "${RED}❌ MANY TESTS FAILED ($TESTS_PASSED/$TESTS_TOTAL)${NC}"
        echo ""
        echo "Please resolve the issues above before attempting deployment."
        exit 1
    fi

    echo ""
    echo "Test Details:"
    echo "  QNAP IP: ${QNAP_IP}"
    echo "  QNAP User: ${QNAP_USER}"
    echo "  Target Ports: 5000 (backend), 3000 (frontend)"
    echo "  Storage Path: /share/CACHEDEV1_DATA/planetarion"
}

# Main test function
main() {
    echo "🧪 Planetarion QNAP Connectivity Test"
    echo "====================================="
    echo ""

    test_local_prerequisites
    echo ""
    test_ssh_access
    echo ""
    test_qnap_system
    echo ""
    test_deployment_simulation
    echo ""
    show_summary
}

# Run main function
main "$@"

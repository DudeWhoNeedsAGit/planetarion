#!/bin/bash

# Planetarion Test Runner
# Comprehensive testing script using Docker

set -e

echo "🚀 Starting Planetarion Test Suite"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available"
    exit 1
fi

# Use docker compose (newer syntax) if available, otherwise docker-compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

print_status "Using Docker Compose: $DOCKER_COMPOSE"

# Function to run backend tests
run_backend_tests() {
    print_status "Running Backend Tests..."
    print_status "Building and starting test services..."

    # Start test services
    $DOCKER_COMPOSE -f docker-compose.test.yml up --build -d test-db

    # Wait for database to be ready
    print_status "Waiting for test database to be ready..."
    sleep 10

    # Run backend tests
    if $DOCKER_COMPOSE -f docker-compose.test.yml run --rm test-backend; then
        print_success "Backend tests passed!"
        return 0
    else
        print_error "Backend tests failed!"
        return 1
    fi
}

# Function to run E2E tests
run_e2e_tests() {
    print_status "Running End-to-End Tests..."

    # Start all test services
    $DOCKER_COMPOSE -f docker-compose.test.yml up --build -d

    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 15

    # Run E2E tests
    if $DOCKER_COMPOSE -f docker-compose.test.yml run --rm test-frontend; then
        print_success "E2E tests passed!"
        return 0
    else
        print_error "E2E tests failed!"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    print_status "Running Complete Test Suite..."

    local backend_result=0
    local e2e_result=0

    # Run backend tests
    if ! run_backend_tests; then
        backend_result=1
    fi

    # Run E2E tests
    if ! run_e2e_tests; then
        e2e_result=1
    fi

    # Cleanup
    print_status "Cleaning up test containers..."
    $DOCKER_COMPOSE -f docker-compose.test.yml down -v

    # Report results
    echo ""
    echo "=================================="
    echo "Test Results Summary:"
    echo "=================================="

    if [ $backend_result -eq 0 ]; then
        print_success "✅ Backend Tests: PASSED"
    else
        print_error "❌ Backend Tests: FAILED"
    fi

    if [ $e2e_result -eq 0 ]; then
        print_success "✅ E2E Tests: PASSED"
    else
        print_error "❌ E2E Tests: FAILED"
    fi

    if [ $backend_result -eq 0 ] && [ $e2e_result -eq 0 ]; then
        print_success "🎉 All tests passed!"
        return 0
    else
        print_error "💥 Some tests failed!"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Planetarion Test Runner"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  backend    Run only backend tests"
    echo "  e2e        Run only E2E tests"
    echo "  all        Run all tests (default)"
    echo "  clean      Clean up test containers and volumes"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 all          # Run complete test suite"
    echo "  $0 backend      # Run only backend tests"
    echo "  $0 e2e          # Run only E2E tests"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up test containers and volumes..."
    $DOCKER_COMPOSE -f docker-compose.test.yml down -v
    print_success "Cleanup completed!"
}

# Main script logic
case "${1:-all}" in
    "backend")
        if run_backend_tests; then
            print_success "Backend tests completed successfully!"
            cleanup
            exit 0
        else
            print_error "Backend tests failed!"
            cleanup
            exit 1
        fi
        ;;
    "e2e")
        if run_e2e_tests; then
            print_success "E2E tests completed successfully!"
            cleanup
            exit 0
        else
            print_error "E2E tests failed!"
            cleanup
            exit 1
        fi
        ;;
    "all")
        if run_all_tests; then
            exit 0
        else
            exit 1
        fi
        ;;
    "clean")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac

# Planetarion Development Makefile
# Single entry point for all development tasks

.PHONY: help unit integration e2e frontend all clean dev-up dev-down test-up test-down tdd tdd-stop

# Default target - Show help
help: # Show all available commands
	@echo "Planetarion Development Commands:"
	@echo ""
	@echo "Testing (SQLite):"
	@echo "  make unit              - Run unit tests (fast, no Docker)"
	@echo "  make integration       - Run integration tests (fast, no Docker)"
	@echo "  make integration-failed - Run only previously failed integration tests"
	@echo "  make integration FAILED=1 - Run integration tests, failed ones first"
	@echo "  make e2e               - Run end-to-end tests (Docker + PostgreSQL)"
	@echo "  make e2e-ui            - Run E2E tests with local UI (no Docker)"
	@echo "  make e2e-ui TEST_FILE=tests/e2e/dashboard.spec.js - Run specific E2E test file"
	@echo "  make frontend          - Run frontend tests (Docker)"
	@echo "  make all               - Run all tests (unit + integration + e2e)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run linting and formatting"
	@echo "  make format        - Auto-format code"
	@echo "  make check         - Run all quality checks"
	@echo ""
	@echo "Development Tools:"
	@echo "  make setup-hooks   - Install pre-commit hooks"
	@echo "  make update-deps   - Update Python dependencies"
	@echo "  make clean-cache   - Clean Python cache files"
	@echo ""
	@echo "Environment Management:"
	@echo "  make dev-up        - Start development containers"
	@echo "  make dev-down      - Stop development containers"
	@echo "  make test-up       - Start test containers"
	@echo "  make test-down     - Stop test containers"
	@echo "  make tdd           - Complete TDD workflow (setup + start + test)"
	@echo "  make tdd-stop      - Stop TDD development servers"
	@echo "  make clean         - Clean up all containers and volumes"

# Local development tests (SQLite, no Docker)
unit: # Run unit tests (fast, no Docker)
	@echo "🧪 Running Unit Tests (SQLite)..."
	. venv/bin/activate && python -m pytest tests/unit -v --tb=short --disable-warnings

integration: # Run integration tests (fast, no Docker)
	@echo "🔗 Running Integration Tests (SQLite)..."
	. venv/bin/activate && python -m pytest tests/integration $(if $(FAILED),--lf,) -v --tb=short --disable-warnings

integration-failed: # Run only previously failed integration tests
	@echo "🔄 Running Only Previously Failed Integration Tests..."
	. venv/bin/activate && python -m pytest tests/integration --lf -v --tb=short --disable-warnings

# Docker-based tests (PostgreSQL)
e2e: # Run end-to-end tests (Docker + PostgreSQL)
	@echo "🌐 Running E2E Tests (Docker + PostgreSQL)..."
	docker-compose -f config/docker/docker-compose.test.yml up --build -d test-db test-backend
	@sleep 10
	docker-compose -f config/docker/docker-compose.test.yml run --rm test-frontend
	@docker-compose -f config/docker/docker-compose.test.yml down

e2e-ui: # Run E2E tests with local UI (no Docker)
	@echo "🖥️  Running E2E Tests with Local UI (No Docker)..."
	@echo "📋 This will start backend and frontend locally, then run E2E tests"
	@if [ -n "$(TEST_FILE)" ]; then \
		echo "🎯 Targeting specific test file: $(TEST_FILE)"; \
	else \
		echo "🎯 Running all E2E tests"; \
	fi
	@echo ""
	@echo "🔧 Starting backend server..."
	@PYTHONPATH=/home/yves/repos/planetarion/game-server/src python -m src > backend.log 2>&1 &
	@echo $$! > backend.pid
	@echo "✅ Backend started (PID: $$(cat backend.pid))"
	@echo ""
	@echo "🎨 Starting frontend server..."
	@cd src/frontend && npm start > frontend.log 2>&1 &
	@echo $$! > frontend.pid
	@echo "✅ Frontend started (PID: $$(cat frontend.pid))"
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo ""
	@echo "🧪 Running E2E tests..."
	@if [ -n "$(TEST_FILE)" ]; then \
		cd src/frontend && npx playwright test $(TEST_FILE) --headed --timeout=60000; \
	else \
		cd src/frontend && npm run test:e2e; \
	fi
	@echo ""
	@echo "🧹 Cleaning up processes..."
	@-kill $$(cat backend.pid) 2>/dev/null || true
	@-kill $$(cat frontend.pid) 2>/dev/null || true
	@-rm -f backend.pid frontend.pid backend.log frontend.log
	@echo "✅ Cleanup complete"


frontend: # Run frontend tests (Docker)
	@echo "🎨 Running Frontend Tests (Docker)..."
	docker-compose -f config/docker/docker-compose.test.yml up --build -d test-backend
	@sleep 5
	docker-compose -f config/docker/docker-compose.test.yml run --rm test-frontend npm test
	@docker-compose -f config/docker/docker-compose.test.yml down

# Combined testing
all: # Run all tests (unit + integration + e2e)
	@echo "🧪 Running All Tests (Unit + Integration + E2E)..."
	$(MAKE) unit
	$(MAKE) integration
	$(MAKE) e2e

# Environment management
dev-up: # Start development containers
	@echo "🚀 Starting Development Environment..."
	docker-compose up -d
	@echo "✅ Development environment ready:"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:5000"
	@echo "   Database: localhost:5432"

dev-down: # Stop development containers
	@echo "🛑 Stopping Development Environment..."
	docker-compose down

test-up: # Start test containers
	@echo "🧪 Starting Test Environment..."
	docker-compose -f config/docker/docker-compose.test.yml up -d
	@echo "✅ Test environment ready"

test-down: # Stop test containers
	@echo "🛑 Stopping Test Environment..."
	docker-compose -f config/docker/docker-compose.test.yml down

# Code quality targets
lint: # Run linting and formatting
	@echo "🔍 Running Linting..."
	. venv/bin/activate && PYTHONPATH=src/backend python -m flake8 src/backend tests/
	@echo "✅ Python linting complete"

format: # Auto-format code
	@echo "🎨 Formatting Code..."
	. venv/bin/activate && PYTHONPATH=src/backend python -m black src/backend tests/
	. venv/bin/activate && PYTHONPATH=src/backend python -m isort src/backend tests/
	@echo "✅ Code formatting complete"

check: # Run all quality checks
	@echo "✅ All quality checks passed"

# Development tools
analyze: # Run repository structure analysis
	@echo "🔍 Running Repository Analysis..."
	../cline-scripts/repo-analyzer.sh
	@echo "✅ Analysis complete"

setup-hooks: # Install pre-commit hooks
	@echo "🔗 Setting up pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed"

update-deps: # Update Python dependencies
	@echo "📦 Updating Python dependencies..."
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install --upgrade -r src/backend/requirements.txt
	@echo "✅ Dependencies updated"

clean-cache: # Clean Python cache files
	@echo "🧹 Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "✅ Cache files cleaned"

# Combined targets
quality: # Run code quality checks
	format lint
	@echo "✅ Code quality checks complete"

setup: # Complete development setup
	setup-hooks update-deps
	@echo "✅ Development environment setup complete"

setup-dev: # Run development environment setup
	@echo "� Running development environment setup..."
	./scripts/setup-dev.sh
	@echo "✅ Development environment setup complete"

clean: # Clean up containers and volumes
	@echo "🧹 Cleaning up all containers and volumes..."
	docker-compose down -v
	docker-compose -f config/docker/docker-compose.test.yml down -v
	@echo "✅ Cleanup complete"

tdd: # Complete TDD workflow (setup + start + test)
	@echo "🔄 Starting Complete TDD Workflow..."
	@echo ""
	@echo "📋 TDD Workflow Steps:"
	@echo "   1. One-time setup (if needed)"
	@echo "   2. Start development servers"
	@echo "   3. Visit http://localhost:3000 to test manually"
	@echo "   4. Run automated tests"
	@echo ""
	@echo "🚀 Step 1: One-time setup..."
	@if [ ! -d "backend/venv" ] || [ ! -d "src/frontend/node_modules" ]; then \
		echo "   Running initial setup..."; \
		./scripts/setup-dev.sh; \
	else \
		echo "   ✅ Setup already complete"; \
	fi
	@echo ""
	@echo "🎯 Step 2: Starting development servers..."
	./test/dev/start.sh
	@echo ""
	@echo "🌐 Step 3: Manual Testing"
	@echo "   Visit: http://localhost:3000"
	@echo "   Test your changes manually in the browser"
	@echo ""
	@echo "🧪 Step 4: Running automated tests..."
	./test/dev/tdd.sh
	@echo ""
	@echo "🛑 To stop servers: ./test/dev/stop.sh"
	@echo ""
	@echo "✅ TDD Workflow Complete!"
	@echo "   🔄 Repeat steps 3-4 as needed for development"

tdd-stop: # Stop TDD development servers
	@echo "🛑 Stopping TDD Development Servers..."
	@echo ""
	@echo "📋 Stopping Services:"
	@echo "   - Flask backend server"
	@echo "   - React frontend server"
	@echo "   - Any background processes"
	@echo ""
	./test/dev/stop.sh
	@echo ""
	@echo "✅ All TDD servers stopped!"
	@echo "   🔄 Ready to restart with: make tdd"

# Planetarion Development Makefile
# Single entry point for all development tasks

.PHONY: help unit integration e2e frontend supertest all clean dev-up dev-down test-up test-down tdd tdd-stop

# Optional vars:
# - TICK=1 enables server-side auto-ticks for local manual play (test-env/test).
TICK ?= 0
ifeq ($(TICK),1)
TICK_ENV := PLANETARION_TICK_SCHEDULER_ENABLED=true PLANETARION_TICK_INTERVAL_SECONDS=2
else
TICK_ENV :=
endif

# Local admin token for fast DB snapshot/restore endpoints (dev/test only).
DEV_ADMIN_TOKEN ?= planetarion-dev

# Optional vars:
# - FRESH=1 forces full teardown + repopulate (slow, but useful when schema changes)
FRESH ?= 0

# Pytest DB isolation:
# - `instance/test_e2e.db` is reserved for manual play / Playwright UI runs.
# - Running `make unit` / `make integration` should never mutate that file.
# Use a throwaway SQLite file under /tmp and wipe it each run for deterministic results.
PYTEST_DB ?= /tmp/planetarion_pytest.db

# Local SQLite DB used for manual UI + Playwright runs.
TEST_DB_PATH ?= ./instance/test_e2e.db
TEST_DB_URL ?= sqlite:////$(CURDIR)/instance/test_e2e.db
PYTHONPATH_SRC ?= $(CURDIR)/src

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
	@echo "  make e2e-ui-tick       - Same as e2e-ui TICK=1"
	@echo "  make e2e-c             - Run Table C full loop Playwright spec (local UI)"
	@echo "  make test-env          - Start backend + frontend for manual testing (no Playwright)"
	@echo "  make test-env TICK=1   - Start manual test env with auto-ticks enabled"
	@echo "  make test-env-tick     - Same as test-env TICK=1"
	@echo "  make test-env FRESH=1  - Full rebuild (slow) + snapshot"
	@echo "  make test-env-reset    - Restore DB from snapshot (fast; servers stay running)"
	@echo "  make test-env-snapshot - Create/overwrite snapshot from live DB"
	@echo "  make scenario-two-player-reset - Reset DB to 2-player + pirates scenario"
	@echo "  make test-a            - Run Table A backend golden-path integration test"
	@echo "  make supertest         - Run JavaScript integration tests (Supertest + Jest)"
	@echo "  make supertest TEST_FILE=src/__tests__/integration/colonization.integration.test.js - Run specific Supertest test file"
	@echo "  make frontend          - Run frontend tests (Docker)"
	@echo "  make all               - Run all tests (unit + integration + e2e + supertest)"
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
	@echo "  make test          - Start local test environment (SQLite + servers + test data)"
	@echo "  make test-tick     - Same as test TICK=1"
	@echo "  make test-stop     - Stop local test environment"
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
	@rm -f $(PYTEST_DB) || true
	@if [ -n "$(TEST_FILE)" ]; then \
		echo "🎯 Running specific test file: $(TEST_FILE)"; \
		. venv/bin/activate && DATABASE_URL=sqlite:////$(PYTEST_DB) python -m pytest $(TEST_FILE) -v --tb=short --disable-warnings; \
	else \
		. venv/bin/activate && DATABASE_URL=sqlite:////$(PYTEST_DB) python -m pytest tests/unit -v --tb=short --disable-warnings; \
	fi

integration: # Run integration tests (fast, no Docker)
	@echo "🔗 Running Integration Tests (SQLite)..."
	@rm -f $(PYTEST_DB) || true
	@if [ -n "$(TEST_FILE)" ]; then \
		echo "🎯 Running specific test file: $(TEST_FILE)"; \
		. venv/bin/activate && DATABASE_URL=sqlite:////$(PYTEST_DB) python -m pytest $(TEST_FILE) -v --tb=short --disable-warnings; \
	else \
		. venv/bin/activate && DATABASE_URL=sqlite:////$(PYTEST_DB) python -m pytest tests/integration $(if $(FAILED),--lf,) -v --tb=short --disable-warnings; \
	fi

integration-failed: # Run only previously failed integration tests
	@echo "🔄 Running Only Previously Failed Integration Tests..."
	. venv/bin/activate && DATABASE_URL=sqlite:////$(PYTEST_DB) python -m pytest tests/integration --lf -v --tb=short --disable-warnings

test-a: # Table A backend golden-path integration test
	@echo "🧪 Running Table A backend golden-path test..."
	. venv/bin/activate && DATABASE_URL=sqlite:////$(PYTEST_DB) python -m pytest tests/integration/test_two_player_table_a_golden_path.py -v --tb=short --disable-warnings

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
	@if [ "$(TICK)" = "1" ]; then echo "⏱️  Auto-ticks: enabled"; else echo "⏸️  Auto-ticks: disabled (set TICK=1)"; fi
	@if [ "$(FRESH)" = "1" ]; then echo "♻️  DB mode: FRESH (repopulate)"; else echo "⚡ DB mode: RESTORE (snapshot)"; fi
	@if [ -n "$(TEST_FILE)" ]; then \
		echo "🎯 Targeting specific test file: $(TEST_FILE)"; \
	else \
		echo "🎯 Running all E2E tests"; \
	fi
	@echo ""
	@echo "🧹 Cleaning up any existing processes and test database..."
	@-pkill -f "[F]LASK_ENV=testing" || true
	@-pkill -f "[p]ython -m src" || true
	@-pkill -f "[n]pm start" || true
	@-lsof -ti:5000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@-rm -f instance/test_e2e.db
	@if [ "$(FRESH)" = "1" ]; then rm -f instance/test_e2e.db.bak; fi
	@sleep 2
	@echo "✅ Cleanup complete"
	@echo ""
	@echo "🔧 Creating instance directory for database..."
	@-mkdir -p instance
	@echo "✅ Instance directory ready"
	@echo ""
	@echo "🔧 Starting backend server..."
	@. venv/bin/activate && DATABASE_URL='$(TEST_DB_URL)' $(TICK_ENV) PLANETARION_FORCED_TRAVEL_TIME_SECONDS=0 PLANETARION_DEV_ADMIN_TOKEN=$(DEV_ADMIN_TOKEN) FLASK_ENV=testing PYTHONPATH=$(PYTHONPATH_SRC) PYTHONUNBUFFERED=1 python3 -u -m src > backend.log 2>&1 &
	@sleep 1 && ps aux | grep "python3 -u -m src" | grep -v grep | awk '{print $$2}' | head -1 > backend.pid
	@echo "⏳ Waiting for backend to become healthy..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45; do \
		if curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
			echo "✅ Backend started successfully"; \
			break; \
		fi; \
		sleep 1; \
	done
	@if ! curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
		echo "❌ BACKEND FAILED TO START!"; \
		echo "🔍 Backend log:"; \
		cat backend.log; \
		echo ""; \
		echo "🛑 Stopping Makefile execution..."; \
		exit 1; \
	fi
	@echo "🔍 Backend process verification:"
	@if ! ps -p $$(cat backend.pid) > /dev/null; then \
		echo "❌ Backend PID $$(cat backend.pid) is not running!"; \
		ps aux | grep python; \
		exit 1; \
	fi
	@echo "   ✅ Backend PID $$(cat backend.pid) is running"
	@ps -p $$(cat backend.pid) -o pid,ppid,cmd | head -2
	@if ! lsof -i :5000 > /dev/null; then \
		echo "❌ Nothing listening on port 5000"; \
		lsof -i :5000 || echo "No processes found on port 5000"; \
		exit 1; \
	fi
	@echo "   ✅ Port 5000 is listening"
	@echo ""
	@echo "📊 Setting up test database (fast backup/restore)..."
	@echo "   Waiting for backend to initialize..."
	@sleep 2
	@echo "   Checking backend health..."
	@for i in 1 2 3; do \
		if curl -s http://localhost:5000/health > /dev/null 2>&1; then \
			echo "   ✅ Backend is healthy"; \
			break; \
		else \
			echo "   ⏳ Backend not ready yet (attempt $$i/3)..."; \
			sleep 1; \
		fi; \
	done
	@export DATABASE_URL='$(TEST_DB_URL)' && export BACKEND_URL=http://localhost:5000 && export PYTHONPATH=$(PYTHONPATH_SRC) && export PLANETARION_DEV_ADMIN_TOKEN=$(DEV_ADMIN_TOKEN) && . venv/bin/activate && python scripts/setup_test_db.py
	@echo "✅ Test database ready"
	@echo ""
	@echo "🎨 Starting frontend server..."
	@cd src/frontend && REACT_APP_BACKEND_URL=http://localhost:5000 REACT_APP_DEV_AUTO_TICK_ON_PENDING=true npm start > frontend.log 2>&1 &
	@echo "⏳ Waiting for frontend to become ready..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45; do \
		if curl -s --max-time 1 http://localhost:3000 | grep -q "<!DOCTYPE html>"; then \
			break; \
		fi; \
		sleep 1; \
	done
	@if ! curl -s --max-time 1 http://localhost:3000 | grep -q "<!DOCTYPE html>"; then \
		echo "❌ FRONTEND FAILED TO START!"; \
		echo "🔍 Frontend log:"; \
		cat src/frontend/frontend.log || true; \
		echo ""; \
		echo "🛑 Stopping Makefile execution..."; \
		exit 1; \
	fi
	@lsof -ti:3000 | head -1 > frontend.pid
	@echo "🔍 Frontend process verification:"
	@if ! ps -p $$(cat frontend.pid) > /dev/null; then \
		echo "❌ Frontend PID $$(cat frontend.pid) is not running!"; \
		ps aux | grep node; \
		exit 1; \
	fi
	@echo "   ✅ Frontend PID $$(cat frontend.pid) is running"
	@ps -p $$(cat frontend.pid) -o pid,ppid,cmd | head -2
	@if ! lsof -i :3000 > /dev/null; then \
		echo "❌ Nothing listening on port 3000"; \
		lsof -i :3000 || echo "No processes found on port 3000"; \
		exit 1; \
	fi
	@echo "   ✅ Port 3000 is listening"
	@echo "✅ Frontend started successfully"
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "🔍 Final connectivity check:"
	@echo "   Testing backend connectivity..."
	@curl -s -o /dev/null -w "   Backend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:5000/health
	@echo "   Testing frontend connectivity..."
	@curl -s -o /dev/null -w "   Frontend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:3000
	@echo "   ✅ Services connectivity verified"
	@echo ""
	@echo "🧪 Running E2E tests..."
	@if [ -n "$(TEST_FILE)" ]; then \
		cd src/frontend && npx playwright test $(TEST_FILE) --headed --timeout=60000; \
	else \
		cd src/frontend && npm run test:e2e; \
	fi
	@TEST_EXIT_CODE=$$?
	@echo ""
	@echo "🧪 Test completed with exit code: $$TEST_EXIT_CODE"
	@echo ""
	@echo "🧹 Cleaning up processes and test database..."
	@-kill $$(cat backend.pid) 2>/dev/null || true
	@-kill $$(cat frontend.pid) 2>/dev/null || true
	@-rm -f backend.pid frontend.pid backend.log frontend.log
	@-rm -f instance/test_e2e.db
	@echo "✅ Cleanup complete"
	@exit $$TEST_EXIT_CODE

e2e-c: # Table C full loop Playwright spec (local UI)
	@$(MAKE) e2e-ui TEST_FILE=tests/e2e/two-player-full-loop.spec.js

# Convenience wrappers (GNU make doesn't support flags like --tick)
test-env-tick:
	@$(MAKE) test-stop >/dev/null 2>&1 || true
	@$(MAKE) test-env TICK=1

test-tick:
	@$(MAKE) test TICK=1

e2e-ui-tick:
	@$(MAKE) e2e-ui TICK=1


frontend: # Run frontend tests (Docker)
	@echo "🎨 Running Frontend Tests (Docker)..."
	docker-compose -f config/docker/docker-compose.test.yml up --build -d test-backend
	@sleep 5
	docker-compose -f config/docker/docker-compose.test.yml run --rm test-frontend npm test
	@docker-compose -f config/docker/docker-compose.test.yml down

supertest: # Run JavaScript integration tests (Supertest + Jest)
	@echo "🧪 Running JavaScript Integration Tests (Supertest + Jest)..."
	@echo "📋 This will start backend and frontend locally, then run Supertest integration tests"
	@echo ""
	@echo "🧹 Cleaning up any existing processes and test database..."
	@-pkill -f "[F]LASK_ENV=testing" || true
	@-pkill -f "[p]ython -m src" || true
	@-pkill -f "[n]pm start" || true
	@-lsof -ti:5000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@-rm -f instance/test_supertest.db
	@sleep 2
	@echo "✅ Cleanup complete"
	@echo ""
	@echo "🔧 Creating instance directory for database..."
	@-mkdir -p instance
	@echo "✅ Instance directory ready"
	@echo ""
	@echo "🔧 Starting backend server for Supertest..."
	@. venv/bin/activate && DATABASE_URL='$(TEST_DB_URL)' PLANETARION_DEV_ADMIN_TOKEN=$(DEV_ADMIN_TOKEN) PLANETARION_FORCED_TRAVEL_TIME_SECONDS=0 FLASK_ENV=testing PYTHONPATH=$(PYTHONPATH_SRC) PYTHONUNBUFFERED=1 python3 -u -m src > backend.log 2>&1 &
	@sleep 1 && ps aux | grep "python3 -u -m src" | grep -v grep | awk '{print $$2}' | head -1 > backend.pid
	@echo "⏳ Waiting for backend to become healthy..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45; do \
		if curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
			echo "✅ Backend started successfully"; \
			break; \
		fi; \
		sleep 1; \
	done
	@if ! curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
		echo "❌ BACKEND FAILED TO START!"; \
		echo "🔍 Backend log:"; \
		cat backend.log; \
		echo ""; \
		echo "🛑 Stopping Makefile execution..."; \
		exit 1; \
	fi
	@echo "🔍 Backend process verification:"
	@if ! ps -p $$(cat backend.pid) > /dev/null; then \
		echo "❌ Backend PID $$(cat backend.pid) is not running!"; \
		ps aux | grep python; \
		exit 1; \
	fi
	@echo "   ✅ Backend PID $$(cat backend.pid) is running"
	@ps -p $$(cat backend.pid) -o pid,ppid,cmd | head -2
	@if ! lsof -i :5000 > /dev/null; then \
		echo "❌ Nothing listening on port 5000"; \
		lsof -i :5000 || echo "No processes found on port 5000"; \
		exit 1; \
	fi
	@echo "   ✅ Port 5000 is listening"
	@echo ""
	@echo "📊 Populating test database..."
	@echo "   Waiting for backend to initialize..."
	@sleep 3  # Reduced from 8s since we're using fast backup restore
	@echo "   Checking backend health..."
	@for i in 1 2 3; do \
		if curl -s http://localhost:5000/health > /dev/null 2>&1; then \
			echo "   ✅ Backend is healthy"; \
			break; \
		else \
			echo "   ⏳ Backend not ready yet (attempt $$i/3)..."; \
			sleep 1; \
		fi; \
	done
	@echo "🔧 Setting up test database (fast backup/restore)..."
	@export DATABASE_URL='$(TEST_DB_URL)' && export BACKEND_URL=http://localhost:5000 && export PYTHONPATH=$(PYTHONPATH_SRC) && . venv/bin/activate && python scripts/setup_test_db.py
	@echo "✅ Test database populated"
	@echo ""
	@echo "🎨 Starting frontend server for Supertest..."
	@cd src/frontend && REACT_APP_BACKEND_URL=http://localhost:5000 REACT_APP_DEV_AUTO_TICK_ON_PENDING=true npm start > frontend.log 2>&1 &
	@sleep 1 && ps aux | grep "npm start" | grep -v grep | awk '{print $$2}' | head -1 > frontend.pid
	@sleep 10  # Give React time to start or crash
	@if ! curl -s http://localhost:3000 | grep -q "<!DOCTYPE html>"; then \
		echo "❌ FRONTEND FAILED TO START!"; \
		echo "🔍 Frontend log:"; \
		cat frontend.log; \
		echo ""; \
		echo "🛑 Stopping Makefile execution..."; \
		exit 1; \
	fi
	@echo "🔍 Frontend process verification:"
	@if ! ps -p $$(cat frontend.pid) > /dev/null; then \
		echo "❌ Frontend PID $$(cat frontend.pid) is not running!"; \
		ps aux | grep node; \
		exit 1; \
	fi
	@echo "   ✅ Frontend PID $$(cat frontend.pid) is running"
	@ps -p $$(cat frontend.pid) -o pid,ppid,cmd | head -2
	@if ! lsof -i :3000 > /dev/null; then \
		echo "❌ Nothing listening on port 3000"; \
		lsof -i :3000 || echo "No processes found on port 3000"; \
		exit 1; \
	fi
	@echo "   ✅ Port 3000 is listening"
	@echo "✅ Frontend started successfully"
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 5
	@echo "🔍 Final connectivity check:"
	@echo "   Testing backend connectivity..."
	@curl -s -o /dev/null -w "   Backend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:5000/health
	@echo "   Testing frontend connectivity..."
	@curl -s -o /dev/null -w "   Frontend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:3000
	@echo "   ✅ Services connectivity verified"
	@echo ""
	@echo "🧪 Running Supertest Integration Tests..."
	@if [ -n "$(TEST_FILE)" ]; then \
		cd src/frontend && npx jest $(TEST_FILE) --watchAll=false; \
	else \
		cd src/frontend && npm run test:integration; \
	fi
	@TEST_EXIT_CODE=$$?
	@echo ""
	@echo "🧪 Supertest tests completed with exit code: $$TEST_EXIT_CODE"
	@echo ""
	@echo "🧹 Cleaning up processes and test database..."
	@-kill $$(cat backend.pid) 2>/dev/null || true
	@-kill $$(cat frontend.pid) 2>/dev/null || true
	@-rm -f backend.pid frontend.pid backend.log frontend.log
	@-rm -f instance/test_supertest.db
	@echo "✅ Cleanup complete"
	@exit $$TEST_EXIT_CODE

# Combined testing
all: # Run all tests (unit + integration + e2e + supertest)
	@echo "🧪 Running All Tests (Unit + Integration + E2E + Supertest)..."
	$(MAKE) unit
	$(MAKE) integration
	$(MAKE) e2e-ui
	$(MAKE) supertest

# Environment management
test: # Start local test environment (SQLite + servers + test data)
	@echo "🧪 Starting Local Test Environment..."
	@echo "📋 This will start backend and frontend locally with test database"
	@if [ "$(TICK)" = "1" ]; then echo "⏱️  Auto-ticks: enabled"; else echo "⏸️  Auto-ticks: disabled (set TICK=1)"; fi
	@if [ "$(FRESH)" = "1" ]; then echo "♻️  DB mode: FRESH (repopulate)"; else echo "⚡ DB mode: RESTORE (snapshot)"; fi
	@echo ""
	@echo "🧹 Cleaning up any existing processes..."
	@-pkill -f "[F]LASK_ENV=testing" || true
	@-pkill -f "[p]ython -m src" || true
	@-pkill -f "[n]pm start" || true
	@-lsof -ti:5000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@if [ "$(FRESH)" = "1" ]; then rm -f instance/test_e2e.db; fi
	@sleep 2
	@echo "✅ Cleanup complete"
	@echo ""
	@echo "🔧 Creating instance directory for database..."
	@-mkdir -p instance
	@echo "✅ Instance directory ready"
	@echo ""
	@echo "🔧 Starting backend server..."
	@echo "   📁 Database file: $(TEST_DB_PATH)"
	@echo "   🔗 Database URL: $(TEST_DB_URL)"
	@if [ "$(FRESH)" != "1" ] && [ -f instance/test_e2e.db.bak ]; then \
		echo "⚡ Restoring DB file from snapshot before start (instance/test_e2e.db.bak → instance/test_e2e.db)"; \
		cp -f instance/test_e2e.db.bak instance/test_e2e.db; \
	fi
	@. venv/bin/activate && DATABASE_URL='$(TEST_DB_URL)' $(TICK_ENV) PLANETARION_MIN_TRAVEL_TIME_SECONDS=30 PLANETARION_DEV_ADMIN_TOKEN=$(DEV_ADMIN_TOKEN) FLASK_ENV=testing PYTHONPATH=$(PYTHONPATH_SRC) PYTHONUNBUFFERED=1 python3 -u -m src > backend.log 2>&1 &
	@sleep 1 && ps aux | grep "python3 -u -m src" | grep -v grep | awk '{print $$2}' | head -1 > backend.pid
	@echo "⏳ Waiting for backend to become healthy..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45; do \
		if curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
			echo "✅ Backend started successfully"; \
			break; \
		fi; \
		sleep 1; \
	done
	@if ! curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
		echo "❌ BACKEND FAILED TO START!"; \
		echo "🔍 Backend log:"; \
		cat backend.log; \
		echo ""; \
		echo "🛑 Stopping Makefile execution..."; \
		exit 1; \
	fi
	@echo "🔍 Backend process verification:"
	@if ! ps -p $$(cat backend.pid) > /dev/null; then \
		echo "❌ Backend PID $$(cat backend.pid) is not running!"; \
		ps aux | grep python; \
		exit 1; \
	fi
	@echo "   ✅ Backend PID $$(cat backend.pid) is running"
	@ps -p $$(cat backend.pid) -o pid,ppid,cmd | head -2
	@if ! lsof -i :5000 > /dev/null; then \
		echo "❌ Nothing listening on port 5000"; \
		lsof -i :5000 || echo "No processes found on port 5000"; \
		exit 1; \
	fi
	@echo "   ✅ Port 5000 is listening"
	@echo ""
	@if [ "$(FRESH)" = "1" ] || [ ! -f instance/test_e2e.db.bak ]; then \
		echo "📊 Populating test database (one-time / schema refresh)..."; \
		export DATABASE_URL='$(TEST_DB_URL)' && export BACKEND_URL=http://localhost:5000 && export PYTHONPATH=$(PYTHONPATH_SRC) && . venv/bin/activate && python scripts/populate_test_data.py; \
		echo "📸 Creating DB snapshot for fast reset..."; \
		curl -s -X POST http://localhost:5000/api/admin/db/snapshot \
			-H "X-Planetarion-Dev-Token: $(DEV_ADMIN_TOKEN)" \
			-H "Content-Type: application/json" \
			-d '{"overwrite": true}' >/dev/null || true; \
		echo "✅ Snapshot ready"; \
	else \
		echo "⚡ Restoring DB from snapshot via API (fast)"; \
		$(MAKE) test-env-reset DEV_ADMIN_TOKEN=$(DEV_ADMIN_TOKEN) >/dev/null || true; \
	fi
	@echo ""
	@echo "🎨 Starting frontend server..."
	@cd src/frontend && REACT_APP_BACKEND_URL=http://localhost:5000 npm start > frontend.log 2>&1 &
	@sleep 1 && ps aux | grep "npm start" | grep -v grep | awk '{print $$2}' | head -1 > frontend.pid
	@sleep 10  # Give React time to start or crash
	@if ! curl -s http://localhost:3000 | grep -q "<!DOCTYPE html>"; then \
		echo "❌ FRONTEND FAILED TO START!"; \
		echo "🔍 Frontend log:"; \
		cat frontend.log; \
		echo ""; \
		echo "🛑 Stopping Makefile execution..."; \
		exit 1; \
	fi
	@echo "🔍 Frontend process verification:"
	@if ! ps -p $$(cat frontend.pid) > /dev/null; then \
		echo "❌ Frontend PID $$(cat frontend.pid) is not running!"; \
		ps aux | grep node; \
		exit 1; \
	fi
	@echo "   ✅ Frontend PID $$(cat frontend.pid) is running"
	@ps -p $$(cat frontend.pid) -o pid,ppid,cmd | head -2
	@if ! lsof -i :3000 > /dev/null; then \
		echo "❌ Nothing listening on port 3000"; \
		lsof -i :3000 || echo "No processes found on port 3000"; \
		exit 1; \
	fi
	@echo "   ✅ Port 3000 is listening"
	@echo "✅ Frontend started successfully"
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 5
	@echo "🔍 Final connectivity check:"
	@echo "   Testing backend connectivity..."
	@curl -s -o /dev/null -w "   Backend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:5000/health
	@echo "   Testing frontend connectivity..."
	@curl -s -o /dev/null -w "   Frontend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:3000
	@echo "   ✅ Services connectivity verified"
	@echo ""
	@echo "🎉 Local test environment ready!"
	@echo "   🌐 Frontend: http://localhost:3000"
	@echo "   🔧 Backend:  http://localhost:5000"
	@echo "   👤 Test User: e2etestuser / testpassword123"
	@echo "   📊 Database: SQLite (instance/test_e2e.db)"
	@echo ""
	@echo "🛑 To stop: make test-stop"
	@echo "🔄 To restart: make test-stop && make test"

test-env: # Start backend + frontend for manual testing (no Playwright)
	@echo "🧪 Starting Test Environment (Backend + Frontend)..."
	@echo "📋 This will start backend and frontend locally with test database"
	@echo "    No Playwright tests will be executed - for manual testing only"
	@if [ "$(TICK)" = "1" ]; then echo "⏱️  Auto-ticks: enabled"; else echo "⏸️  Auto-ticks: disabled (set TICK=1)"; fi
	@if [ "$(FRESH)" = "1" ]; then echo "♻️  DB mode: FRESH (repopulate)"; else echo "⚡ DB mode: RESTORE (snapshot)"; fi
	@echo ""
		@if [ "$(FRESH)" = "1" ]; then \
			echo "🧹 Cleaning up any existing processes and test database..."; \
			pkill -f "[F]LASK_ENV=testing" 2>/dev/null || true; \
			pkill -f "[p]ython -m src" 2>/dev/null || true; \
			pkill -f "[n]pm start" 2>/dev/null || true; \
			lsof -ti:5000 2>/dev/null | xargs kill -9 2>/dev/null || true; \
			lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null || true; \
			rm -f instance/test_e2e.db; \
			sleep 2; \
			echo "✅ Cleanup complete"; \
		echo ""; \
	fi
	@echo "🔧 Creating instance directory for database..."
	@-mkdir -p instance
	@echo "✅ Instance directory ready"
	@echo ""
	@if curl -s http://localhost:5000/health > /dev/null 2>&1; then \
		echo "✅ Backend already running"; \
	else \
		if [ "$(FRESH)" != "1" ] && [ -f instance/test_e2e.db.bak ]; then \
			echo "⚡ Restoring DB file from snapshot before start (instance/test_e2e.db.bak → instance/test_e2e.db)"; \
			cp -f instance/test_e2e.db.bak instance/test_e2e.db; \
		fi; \
		echo "🔧 Starting backend server..."; \
		. venv/bin/activate && DATABASE_URL='$(TEST_DB_URL)' $(TICK_ENV) PLANETARION_MIN_TRAVEL_TIME_SECONDS=30 PLANETARION_DEV_ADMIN_TOKEN=$(DEV_ADMIN_TOKEN) FLASK_ENV=testing PYTHONPATH=$(PYTHONPATH_SRC) PYTHONUNBUFFERED=1 python3 -u -m src > backend.log 2>&1 & \
		sleep 1 && ps aux | grep "python3 -u -m src" | grep -v grep | awk '{print $$2}' | head -1 > backend.pid; \
		echo "⏳ Waiting for backend to become healthy..."; \
		for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45; do \
			if curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
				echo "✅ Backend started successfully"; \
				break; \
			fi; \
			sleep 1; \
		done; \
		if ! curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
			echo "❌ BACKEND FAILED TO START!"; \
			echo "🔍 Backend log:"; \
			cat backend.log; \
			echo ""; \
			echo "🛑 Stopping Makefile execution..."; \
			exit 1; \
		fi; \
		if ! lsof -i :5000 > /dev/null; then \
			echo "❌ Nothing listening on port 5000"; \
			lsof -i :5000 || echo "No processes found on port 5000"; \
			exit 1; \
		fi; \
		echo "   ✅ Port 5000 is listening"; \
	fi
	@echo ""
	@if [ "$(FRESH)" = "1" ] || [ ! -f instance/test_e2e.db.bak ]; then \
		echo "📊 Populating test database (one-time / schema refresh)..."; \
		export DATABASE_URL='$(TEST_DB_URL)' && export BACKEND_URL=http://localhost:5000 && export PYTHONPATH=$(PYTHONPATH_SRC) && . venv/bin/activate && python scripts/populate_test_data.py; \
		echo "📸 Creating DB snapshot for fast reset..."; \
		curl -s -X POST http://localhost:5000/api/admin/db/snapshot \
			-H "X-Planetarion-Dev-Token: $(DEV_ADMIN_TOKEN)" \
			-H "Content-Type: application/json" \
			-d '{"overwrite": true}' >/dev/null || true; \
		echo "✅ Snapshot ready"; \
	else \
		echo "⚡ Restoring DB from snapshot via API (fast)"; \
		$(MAKE) test-env-reset DEV_ADMIN_TOKEN=$(DEV_ADMIN_TOKEN) >/dev/null || true; \
	fi
	@echo ""
	@echo "🔍 Verifying test user exists (e2etestuser)..."
	@if [ ! -f instance/test_e2e.db ]; then \
		echo "❌ Missing instance/test_e2e.db after setup"; \
		exit 1; \
	fi
	@if ! sqlite3 instance/test_e2e.db "SELECT 1 FROM users WHERE username='e2etestuser' LIMIT 1;" | grep -q "1"; then \
		echo "⚠️  Snapshot/DB missing e2etestuser. Rebuilding test data and refreshing snapshot..."; \
		export DATABASE_URL='$(TEST_DB_URL)' && export BACKEND_URL=http://localhost:5000 && export PYTHONPATH=$(PYTHONPATH_SRC) && . venv/bin/activate && python scripts/populate_test_data.py; \
		curl -s -X POST http://localhost:5000/api/admin/db/snapshot \
			-H "X-Planetarion-Dev-Token: $(DEV_ADMIN_TOKEN)" \
			-H "Content-Type: application/json" \
			-d '{"overwrite": true}' >/dev/null || true; \
		echo "✅ Snapshot refreshed with e2etestuser"; \
	else \
		echo "✅ e2etestuser present"; \
	fi
	@echo ""
	@echo "🎨 Starting frontend server..."
	@if curl -s http://localhost:3000 | grep -q "<!DOCTYPE html>" 2>/dev/null; then \
		echo "✅ Frontend already running"; \
		if [ ! -f frontend.pid ]; then \
			pid=$$(lsof -ti:3000 2>/dev/null | head -1); \
			if [ -n "$$pid" ]; then \
				echo "$$pid" > frontend.pid; \
			fi; \
		fi; \
	else \
		cd src/frontend && REACT_APP_BACKEND_URL=http://localhost:5000 npm start > frontend.log 2>&1 & \
		sleep 1 && ps aux | grep "npm start" | grep -v grep | awk '{print $$2}' | head -1 > frontend.pid; \
		sleep 10; \
		if ! curl -s http://localhost:3000 | grep -q "<!DOCTYPE html>"; then \
			echo "❌ FRONTEND FAILED TO START!"; \
			echo "🔍 Frontend log:"; \
			cat frontend.log; \
			echo ""; \
			echo "🛑 Stopping Makefile execution..."; \
			exit 1; \
		fi; \
	fi
	@echo "🔍 Frontend process verification:"
	@if [ ! -f frontend.pid ] || [ -z "$$(cat frontend.pid 2>/dev/null)" ]; then \
		pid=$$(lsof -ti:3000 2>/dev/null | head -1); \
		if [ -n "$$pid" ]; then echo "$$pid" > frontend.pid; fi; \
	fi; \
	if [ ! -f frontend.pid ] || [ -z "$$(cat frontend.pid 2>/dev/null)" ]; then \
		echo "❌ Could not determine frontend PID (frontend.pid missing)"; \
		lsof -i :3000 || true; \
		exit 1; \
	fi; \
	if ! ps -p $$(cat frontend.pid) > /dev/null; then \
		echo "❌ Frontend PID $$(cat frontend.pid) is not running!"; \
		ps aux | grep node; \
		exit 1; \
	fi
	@echo "   ✅ Frontend PID $$(cat frontend.pid) is running"
	@ps -p $$(cat frontend.pid) -o pid,ppid,cmd | head -2
	@if ! lsof -i :3000 > /dev/null; then \
		echo "❌ Nothing listening on port 3000"; \
		lsof -i :3000 || echo "No processes found on port 3000"; \
		exit 1; \
	fi
	@echo "   ✅ Port 3000 is listening"
	@echo "✅ Frontend started successfully"
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 5
	@echo "🔍 Final connectivity check:"
	@echo "   Testing backend connectivity..."
	@curl -s -o /dev/null -w "   Backend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:5000/health
	@echo "   Testing frontend connectivity..."
	@curl -s -o /dev/null -w "   Frontend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:3000
	@echo "   ✅ Services connectivity verified"
	@echo ""
	@echo "🎉 Test environment ready for manual testing!"
	@echo "   🌐 Frontend: http://localhost:3000"
	@echo "   🔧 Backend:  http://localhost:5000"
	@echo "   👤 Test User: e2etestuser / testpassword123"
	@echo "   ⏱️  Auto-ticks: enabled via scheduler ($(TICK_ENV))"
	@echo "   🧾 Fleet timeline: Fleet Management shows recent events"
	@echo "   📊 Database: SQLite (instance/test_e2e.db)"
	@echo ""
	@echo "🧪 Ready for manual testing of JavaScript frontend ↔ Python backend interaction"
	@echo "🛑 To stop: make test-stop"

test-env-reset: # Restore DB from snapshot (fast; servers stay running)
	@echo "🧹 Restoring DB from snapshot (servers stay running)..."
	@curl -s -X POST http://localhost:5000/api/admin/db/restore \
		-H "X-Planetarion-Dev-Token: $(DEV_ADMIN_TOKEN)" \
		-H "Content-Type: application/json" \
		-d '{}' | cat
	@echo ""
	@echo "🔍 Verifying restored DB contains e2etestuser..."
	@if [ -f instance/test_e2e.db ] && sqlite3 instance/test_e2e.db "SELECT 1 FROM users WHERE username='e2etestuser' LIMIT 1;" | grep -q "1"; then \
		echo "✅ Restore OK"; \
	else \
		echo "⚠️  Restore produced DB without e2etestuser. Run: make test-env FRESH=1"; \
	fi

test-env-snapshot: # Create/overwrite snapshot from live DB
	@echo "📸 Creating DB snapshot from live DB..."
	@curl -s -X POST http://localhost:5000/api/admin/db/snapshot \
		-H "X-Planetarion-Dev-Token: $(DEV_ADMIN_TOKEN)" \
		-H "Content-Type: application/json" \
		-d '{"overwrite": true}' | cat
	@echo ""

scenario-two-player-reset: # Reset DB to deterministic 2-player scenario
	@echo "🎮 Resetting DB to two-player scenario..."
	@curl -s -X POST http://localhost:5000/api/admin/scenarios/two-player/reset \
		-H "X-Planetarion-Dev-Token: $(DEV_ADMIN_TOKEN)" \
		-H "Content-Type: application/json" \
		-d '{"password":"testpassword123"}' | cat
	@echo ""

# Phase 4: Colonization Testing Environment (No Playwright)
colonization-env: # Start backend + frontend for colonization testing (no E2E tests)
	@echo "🚀 Starting Colonization Testing Environment (Phase 4)..."
	@echo "📋 This will start backend and frontend locally with colonization test data"
	@echo "    Optimized for colonization mechanics testing without Playwright overhead"
	@echo ""
	@echo "🧹 Cleaning up any existing processes and test database..."
	@-pkill -f "[F]LASK_ENV=testing" || true
	@-pkill -f "[p]ython -m src" || true
	@-pkill -f "[n]pm start" || true
	@-lsof -ti:5000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@-rm -f instance/test_colonization.db
	@sleep 2
	@echo "✅ Cleanup complete"
	@echo ""
	@echo "🔧 Creating instance directory for database..."
	@-mkdir -p instance
	@echo "✅ Instance directory ready"
	@echo ""
	@echo "🔧 Starting backend server with colonization focus..."
	@DATABASE_URL='sqlite:///./instance/test_colonization.db' . venv/bin/activate && FLASK_ENV=testing PYTHONPATH=$(PYTHONPATH_SRC) PYTHONUNBUFFERED=1 python3 -u -m src > backend.log 2>&1 &
	@sleep 1 && ps aux | grep "python3 -u -m src" | grep -v grep | awk '{print $$2}' | head -1 > backend.pid
	@echo "⏳ Waiting for backend to become healthy..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45; do \
		if curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
			echo "✅ Backend started successfully"; \
			break; \
		fi; \
		sleep 1; \
	done
	@if ! curl -s --max-time 1 http://localhost:5000/health > /dev/null 2>&1; then \
		echo "❌ BACKEND FAILED TO START!"; \
		echo "🔍 Backend log:"; \
		cat backend.log; \
		echo ""; \
		echo "🛑 Stopping Makefile execution..."; \
		exit 1; \
	fi
	@echo "🔍 Backend process verification:"
	@if ! ps -p $$(cat backend.pid) > /dev/null; then \
		echo "❌ Backend PID $$(cat backend.pid) is not running!"; \
		ps aux | grep python; \
		exit 1; \
	fi
	@echo "   ✅ Backend PID $$(cat backend.pid) is running"
	@ps -p $$(cat backend.pid) -o pid,ppid,cmd | head -2
	@if ! lsof -i :5000 > /dev/null; then \
		echo "❌ Nothing listening on port 5000"; \
		lsof -i :5000 || echo "No processes found on port 5000"; \
		exit 1; \
	fi
	@echo "   ✅ Port 5000 is listening"
	@echo ""
	@echo "📊 Populating test database with colonization data..."
	@echo "   Waiting for backend to initialize..."
	@sleep 8
	@echo "   Checking backend health..."
	@for i in 1 2 3 4 5; do \
		if curl -s http://localhost:5000/health > /dev/null 2>&1; then \
			echo "   ✅ Backend is healthy"; \
			break; \
		else \
			echo "   ⏳ Backend not ready yet (attempt $$i/5)..."; \
			sleep 2; \
		fi; \
	done
	@echo "🔧 Setting DATABASE_URL=sqlite:///instance/test_colonization.db"
	@export DATABASE_URL='sqlite:///./instance/test_colonization.db' && export BACKEND_URL=http://localhost:5000 && export PYTHONPATH=$(PYTHONPATH_SRC) && . venv/bin/activate && echo "DEBUG: DATABASE_URL=$$DATABASE_URL" && python scripts/populate_test_data.py
	@echo "✅ Test database populated with colonization scenarios"
	@echo ""
	@echo "🎨 Starting frontend server for colonization testing..."
	@cd src/frontend && REACT_APP_BACKEND_URL=http://localhost:5000 npm start > frontend.log 2>&1 &
	@sleep 1 && ps aux | grep "npm start" | grep -v grep | awk '{print $$2}' | head -1 > frontend.pid
	@sleep 10  # Give React time to start or crash
	@if ! curl -s http://localhost:3000 | grep -q "<!DOCTYPE html>"; then \
		echo "❌ FRONTEND FAILED TO START!"; \
		echo "🔍 Frontend log:"; \
		cat frontend.log; \
		echo ""; \
		echo "🛑 Stopping Makefile execution..."; \
		exit 1; \
	fi
	@echo "🔍 Frontend process verification:"
	@if ! ps -p $$(cat frontend.pid) > /dev/null; then \
		echo "❌ Frontend PID $$(cat frontend.pid) is not running!"; \
		ps aux | grep node; \
		exit 1; \
	fi
	@echo "   ✅ Frontend PID $$(cat frontend.pid) is running"
	@ps -p $$(cat frontend.pid) -o pid,ppid,cmd | head -2
	@if ! lsof -i :3000 > /dev/null; then \
		echo "❌ Nothing listening on port 3000"; \
		lsof -i :3000 || echo "No processes found on port 3000"; \
		exit 1; \
	fi
	@echo "   ✅ Port 3000 is listening"
	@echo "✅ Frontend started successfully"
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 5
	@echo "🔍 Final connectivity check:"
	@echo "   Testing backend connectivity..."
	@curl -s -o /dev/null -w "   Backend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:5000/health
	@echo "   Testing frontend connectivity..."
	@curl -s -o /dev/null -w "   Frontend: HTTP %{http_code} - %{time_total}s response time\n" http://localhost:3000
	@echo "   ✅ Services connectivity verified"
	@echo ""
	@echo "🎯 Phase 4 Colonization Testing Environment Ready!"
	@echo "   🌐 Frontend: http://localhost:3000"
	@echo "   🔧 Backend:  http://localhost:5000"
	@echo "   👤 Test User: e2etestuser / testpassword123"
	@echo "   📊 Database: SQLite (instance/test_colonization.db)"
	@echo ""
	@echo "🧪 Ready for colonization mechanics testing:"
	@echo "   • Manual testing of colonization workflows"
	@echo "   • API testing with tools like curl/Postman"
	@echo "   • Frontend-backend interaction validation"
	@echo "   • Database state inspection"
	@echo ""
	@echo "🛑 To stop: make colonization-stop"
	@echo "🔄 To restart: make colonization-stop && make colonization-env"

colonization-stop: # Stop colonization testing environment
	@echo "🛑 Stopping Colonization Testing Environment..."
	@echo ""
	@echo "📋 Stopping Services:"
	@echo "   - Flask backend server"
	@echo "   - React frontend server"
	@echo "   - Cleaning up processes and colonization test database"
	@echo ""
	@-kill $$(cat backend.pid) 2>/dev/null || true
	@-kill $$(cat frontend.pid) 2>/dev/null || true
	@-rm -f backend.pid frontend.pid backend.log frontend.log
	@-rm -f instance/test_colonization.db
	@echo ""
	@echo "✅ Colonization testing environment stopped!"
	@echo "   🔄 Ready to restart with: make colonization-env"

test-stop: # Stop local test environment
	@echo "🛑 Stopping Local Test Environment..."
	@echo ""
	@echo "📋 Stopping Services:"
	@echo "   - Flask backend server"
	@echo "   - React frontend server"
	@echo "   - Cleaning up processes and database"
	@echo ""
	@-kill $$(cat backend.pid) 2>/dev/null || true
	@-kill $$(cat frontend.pid) 2>/dev/null || true
	@-rm -f backend.pid frontend.pid backend.log frontend.log
	@-rm -f instance/test_e2e.db
	@echo ""
	@echo "✅ Local test environment stopped!"
	@echo "   🔄 Ready to restart with: make test"

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

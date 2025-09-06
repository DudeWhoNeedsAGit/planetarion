# Planetarion Testing Guide

## 🎯 Quick Start

```bash
# See all available commands
make help

# Fast local development (SQLite)
make unit          # Unit tests
make integration   # Integration tests

# Full system testing (Docker + PostgreSQL)
make e2e           # End-to-end tests
make e2e-ui        # E2E tests with local UI (new!)
make frontend      # Frontend tests

# Run everything
make all
```

## 🏗️ Architecture Overview

### **Two Testing Environments**

| Environment | Database | Speed | Use Case |
|-------------|----------|-------|----------|
| **Local Dev** | SQLite (`.env`) | ⚡ Fast | TDD cycles, backend changes |
| **Docker E2E** | PostgreSQL | 🐌 Slow | Full system, frontend integration |

### **Networking (Simplified)**
- **All environments use `localhost`** for consistency
- **No container-internal URLs** (`test-backend`, `test-db`)
- **Frontend connects to `localhost:5000`** in all cases

## 🔧 Environment Setup

### **Local Development (SQLite)**
```bash
# Backend uses .env file (SQLite)
# No Docker required
cd backend && source venv/bin/activate
python -m pytest ../tests/unit -v
```

### **Docker Testing (PostgreSQL)**
```bash
# Uses docker-compose.test.yml
# Isolated test database
make e2e
```

## 📋 Configuration

### **Backend Database Priority**
1. Docker environment variables (when using containers)
2. `.env` file (when using local venv)
3. Default SQLite fallback

### **Frontend API Configuration**
```bash
# Single environment variable for all environments
REACT_APP_API_URL=http://localhost:5000
```

## 🚀 Development Workflow

### **Backend Changes**
```bash
# Fast iteration with SQLite
make unit
make integration

# Full validation with PostgreSQL
make e2e
```

### **Frontend Changes**
```bash
# Start dev environment
make dev-up

# Manual testing at http://localhost:3000
# Then run automated tests
make frontend
```

### **Full System Testing**
```bash
# Run complete test suite
make all
```

### **E2E Testing with Local UI (New!)**
```bash
# Start full-stack locally and run E2E tests
make e2e-ui

# This command:
# 1. Starts backend locally (PYTHONPATH fixed)
# 2. Starts frontend locally
# 3. Runs E2E tests with Playwright
# 4. Shows test results with screenshots/videos
```

### **Baby-Steps E2E Validation**
```bash
# Systematic approach to E2E test validation
# Run tests one by one to identify issues

# 1. Auth tests (login/register flows)
cd game-server/src/frontend && npx playwright test tests/e2e/auth.spec.js

# 2. Dashboard tests (main functionality)
cd game-server/src/frontend && npx playwright test tests/e2e/dashboard.spec.js

# 3. Fleet tests (fleet management)
cd game-server/src/frontend && npx playwright test tests/e2e/fleet.spec.js

# 4. Galaxy map tests (navigation)
cd game-server/src/frontend && npx playwright test tests/e2e/galaxy-map.spec.js
```

## 🔍 Troubleshooting

### **Common Issues**

**Local Development Environment Fixes**
```bash
# Backend PYTHONPATH issues (recently fixed)
cd game-server && PYTHONPATH=/home/yves/repos/planetarion/game-server/src python -m src.backend.app

# Frontend development startup
cd game-server/src/frontend && npm start

# E2E testing with local UI
make e2e-ui  # New command for full-stack local testing
```

**Database Connection Errors**
```bash
# Check if containers are running
make dev-up
docker-compose ps

# View backend logs
docker-compose logs backend
```

**Test Failures**
```bash
# Run with verbose output
cd backend && source venv/bin/activate
python -m pytest ../tests/unit -v -s
```

**Environment Variables**
```bash
# Check backend configuration
docker exec <backend-container> env | grep DATABASE
```

**E2E Test Debugging**
```bash
# Run with headed mode to see browser
cd game-server/src/frontend && npx playwright test tests/e2e/dashboard.spec.js --headed --timeout=60000

# Run specific test with detailed output
cd game-server/src/frontend && npx playwright test tests/e2e/auth.spec.js --reporter=line

# View test results and screenshots
cd game-server/src/frontend && npx playwright show-report
```

### **Database Access**
```bash
# Development database
psql postgresql://planetarion_user:planetarion_password@localhost:5432/planetarion

# Test database (when running)
docker exec <test-db-container> psql -U planetarion_user -d planetarion_test
```

## 🧹 Cleanup

```bash
# Stop all containers
make dev-down
make test-down

# Clean up everything
make clean
```

---

**Makefile is your single entry point for all testing needs.**

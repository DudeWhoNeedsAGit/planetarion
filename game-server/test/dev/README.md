# Development Testing Scripts

Fast TDD workflow for Planetarion development without Docker overhead.

## 🎯 Purpose

These scripts provide a **30-60 second TDD cycle** for active development, eliminating the slow Docker redeployment process. Perfect for rapid iteration during feature development.

## 📁 Available Scripts

### Environment Management
- `setup.sh` - One-time development environment setup
- `start.sh` - Start development services with hot reload
- `stop.sh` - Stop all running services cleanly

### Testing Scripts
- `tdd.sh` - Complete TDD cycle (backend + frontend)
- `backend.sh` - Backend API testing only
- `frontend.sh` - Frontend component testing only

## 🚀 Quick Start

### First Time Setup
```bash
./test/dev/setup.sh
```

### Daily Development Workflow
```bash
# Start services (keep running)
./test/dev/start.sh

# TDD loop (repeat as needed)
./test/dev/tdd.sh

# Stop when done
./test/dev/stop.sh
```

### Focused Development
```bash
# Backend development
./test/dev/backend.sh

# Frontend development
./test/dev/frontend.sh
```

## 📊 Performance

- **Setup**: ~2-3 minutes (one time)
- **Service Start**: ~10 seconds
- **TDD Cycle**: ~30-60 seconds
- **Focused Tests**: ~10-30 seconds

## 🔧 Script Details

### setup.sh
**Purpose**: Initialize development environment
**What it does**:
- Creates Python virtual environment
- Installs backend dependencies
- Installs frontend dependencies
- Sets up development database
- Creates necessary directories

**Usage**:
```bash
./test/dev/setup.sh
```

### start.sh
**Purpose**: Start development services
**What it does**:
- Starts Flask backend on port 5000
- Starts React frontend on port 3000
- Enables hot reload for both services
- Provides service URLs and status

**Usage**:
```bash
./test/dev/start.sh
# Press Ctrl+C to stop
```

### stop.sh
**Purpose**: Clean shutdown of services
**What it does**:
- Stops Flask processes
- Stops React processes
- Stops npm processes
- Graceful termination

**Usage**:
```bash
./test/dev/stop.sh
```

### tdd.sh
**Purpose**: Complete TDD cycle
**What it does**:
- Runs backend API integration tests
- Runs frontend component tests
- Provides timing and results summary
- Non-zero exit code on failures

**Usage**:
```bash
./test/dev/tdd.sh
```

### backend.sh
**Purpose**: Backend-focused testing
**What it does**:
- Tests authentication APIs
- Tests planet management APIs
- Tests fleet management APIs
- Tests tick system
- Detailed results for each API group

**Usage**:
```bash
./test/dev/backend.sh
```

### frontend.sh
**Purpose**: Frontend-focused testing
**What it does**:
- Tests Navigation component
- Tests Dashboard component
- Tests FleetManagement component
- Uses React Testing Library
- Mocked API calls

**Usage**:
```bash
./test/dev/frontend.sh
```

## 🎯 Development Workflow

### Backend Development
```bash
# Start services
./test/dev/start.sh

# Make backend changes
# Test specific APIs
./test/dev/backend.sh

# Full validation
./test/dev/tdd.sh
```

### Frontend Development
```bash
# Start services
./test/dev/start.sh

# Make frontend changes
# Test specific components
./test/dev/frontend.sh

# Full validation
./test/dev/tdd.sh
```

### Full-Stack Development
```bash
# Start services
./test/dev/start.sh

# Make changes to backend/frontend
# Run complete TDD cycle
./test/dev/tdd.sh

# Repeat as needed
```

## 🔧 Configuration

### Ports
- **Backend API**: `http://localhost:5000`
- **Frontend Dev**: `http://localhost:3000`

### Environment
- **Python**: Virtual environment in `game-server/backend/venv/`
- **Node.js**: Dependencies in `game-server/frontend/node_modules/`
- **Database**: SQLite in `game-server/backend/instance/dev.db`

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check port availability
lsof -i :3000  # Frontend
lsof -i :5000  # Backend

# Kill processes
./test/dev/stop.sh

# Try again
./test/dev/start.sh
```

### Tests Fail
```bash
# Run with verbose output
cd game-server && python -m pytest tests/integration/test_auth.py -v -s

# Check database
cd game-server/backend && python -c "from database import db; db.create_all()"
```

### Permission Issues
```bash
# Make scripts executable
chmod +x test/dev/*.sh
```

## 📈 Best Practices

### Keep Services Running
- Start services once with `./test/dev/start.sh`
- Keep them running during development
- Use `./test/dev/tdd.sh` for validation
- Stop with `./test/dev/stop.sh` when done

### Use Focused Testing
- Use `./test/dev/backend.sh` when working on APIs
- Use `./test/dev/frontend.sh` when working on UI
- Use `./test/dev/tdd.sh` for complete validation

### Before Commits
- Always run `./test/dev/tdd.sh` before committing
- Ensure all tests pass
- Check for any new failures

## 🔄 Integration with IDE

### VSCode Tasks
Add these to your `.vscode/tasks.json`:
```json
{
  "tasks": [
    {
      "label": "TDD Loop",
      "type": "shell",
      "command": "./test/dev/tdd.sh",
      "group": "test"
    },
    {
      "label": "Start Dev Services",
      "type": "shell",
      "command": "./test/dev/start.sh",
      "group": "build"
    }
  ]
}
```

### Keyboard Shortcuts
- **Ctrl+Shift+T**: Run TDD loop
- **Ctrl+Shift+B**: Start dev services

## 📊 Test Coverage

### Backend Tests
- ✅ Authentication (login, register, JWT)
- ✅ Planet Management (CRUD, resources, structures)
- ✅ Fleet Operations (create, send, recall)
- ✅ Tick System (resource generation, timing)

### Frontend Tests
- ✅ Navigation Component (routing, sections)
- ✅ Dashboard Component (resource display, updates)
- ✅ Fleet Management (ship construction, missions)

## 🎉 Success Metrics

- **Test Cycle Time**: <60 seconds
- **Service Start Time**: <10 seconds
- **Test Reliability**: 100% pass rate
- **Developer Productivity**: Rapid iteration without Docker waits

## 📚 Related Documentation

- [Main Test Suite](../README.md)
- [CI/CD Testing](../ci/README.md)
- [Integration Testing](../integration/README.md)
- [Component Testing](../components/README.md)

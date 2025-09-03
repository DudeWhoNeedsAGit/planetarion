# Planetarion Test Automation Suite

Fast and comprehensive testing framework for Planetarion development with multiple testing modes optimized for different scenarios.

## 📁 Directory Structure

```
test/
├── dev/           # Development testing (fast, local, no Docker)
├── ci/            # CI/CD testing (Docker, comprehensive)
├── integration/   # API integration tests
├── components/    # Frontend component tests
├── utils/         # Helper scripts and utilities
└── README.md      # This file
```

## 🎯 Testing Modes

### Development Mode (`/test/dev/`)
**Purpose**: Fast TDD workflow for active development
**Performance**: 30-60 second test cycles
**Use Case**: Daily development, rapid iteration
**Technology**: Direct Python/Node execution, no Docker

### CI/CD Mode (`/test/ci/`)
**Purpose**: Comprehensive testing for production
**Performance**: 2-5 minutes (with Docker setup)
**Use Case**: Pre-deployment, automated pipelines
**Technology**: Docker containers, full environment

### Integration Testing (`/test/integration/`)
**Purpose**: API contract testing and data flow validation
**Performance**: 20-60 seconds
**Use Case**: Backend API validation, cross-service testing
**Technology**: pytest, direct API calls

### Component Testing (`/test/components/`)
**Purpose**: Isolated frontend component testing
**Performance**: 10-30 seconds
**Use Case**: UI component validation, unit testing
**Technology**: React Testing Library, Jest

## 🚀 Quick Start

### Development Setup
```bash
# One-time setup
./test/dev/setup.sh

# Start development environment
./test/dev/start.sh

# Run TDD loop
./test/dev/tdd.sh
```

### CI/CD Pipeline
```bash
# Full test suite
./test/ci/full.sh

# API only testing
./test/ci/api.sh
```

## 📊 Performance Comparison

| Mode | Setup Time | Test Cycle | Use Case | Docker |
|------|------------|------------|----------|--------|
| **Development** | <5s | 30-60s | Daily dev | ❌ |
| **CI/CD** | 2-5min | 5+min | Production | ✅ |
| **Integration** | <5s | 20-60s | API testing | ❌ |
| **Components** | <5s | 10-30s | UI testing | ❌ |

## 🛠️ Available Scripts

### Development Mode
- `setup.sh` - One-time environment setup
- `start.sh` - Start development services
- `stop.sh` - Stop all services
- `tdd.sh` - Complete TDD cycle
- `backend.sh` - Backend API testing
- `frontend.sh` - Frontend component testing

### CI/CD Mode
- `full.sh` - Complete test suite with Docker
- `api.sh` - API testing in Docker
- `frontend.sh` - Frontend E2E testing

### Integration Testing
- `auth.sh` - Authentication flow testing
- `resources.sh` - Resource system testing
- `fleet.sh` - Fleet operations testing

### Utilities
- `db-setup.sh` - Database initialization
- `db-reset.sh` - Database cleanup
- `health.sh` - Service health checks

## 🎯 Development Workflow

### Daily Development
1. **Setup** (one time): `./test/dev/setup.sh`
2. **Start Services**: `./test/dev/start.sh`
3. **TDD Loop**: `./test/dev/tdd.sh` (repeat as needed)
4. **Focused Testing**: `./test/dev/backend.sh` or `./test/dev/frontend.sh`
5. **Cleanup**: `./test/dev/stop.sh`

### Before Commit
1. **Run TDD**: `./test/dev/tdd.sh`
2. **Integration Tests**: `./test/integration/auth.sh`
3. **Component Tests**: `./test/components/navigation.sh`

### CI/CD Pipeline
1. **Full Suite**: `./test/ci/full.sh`
2. **API Tests**: `./test/ci/api.sh`
3. **Results**: Check exit codes and logs

## 🔧 Configuration

### Environment Variables
```bash
# Backend
export FLASK_ENV=development
export DATABASE_URL=sqlite:///instance/dev.db

# Frontend
export REACT_APP_API_URL=http://localhost:5000

# Testing
export TEST_DATABASE_URL=sqlite:///:memory:
```

### Port Configuration
- **Backend API**: `http://localhost:5000`
- **Frontend Dev**: `http://localhost:3000`
- **Test Database**: In-memory SQLite

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check port availability
lsof -i :3000  # Frontend
lsof -i :5000  # Backend

# Kill conflicting processes
./test/dev/stop.sh
```

### Tests Fail
```bash
# Run with verbose output
cd game-server && python -m pytest tests/integration/test_auth.py -v -s

# Check database
python -c "from backend.database import db; db.create_all()"
```

### Permission Issues
```bash
# Make scripts executable
chmod +x test/**/*.sh
```

## 📈 Best Practices

### Development Mode
- Use for active development and TDD
- Keep services running for hot reload
- Run focused tests for specific features
- Use `./test/dev/tdd.sh` for complete validation

### CI/CD Mode
- Use for pre-deployment validation
- Run in clean Docker environment
- Include in automated pipelines
- Monitor for performance regressions

### Integration Testing
- Test API contracts and data flow
- Validate cross-service communication
- Use for backend-focused development
- Run before frontend integration

### Component Testing
- Test UI components in isolation
- Mock external dependencies
- Focus on user interactions
- Use for frontend refactoring

## 🤝 Contributing

### Adding New Tests
1. Choose appropriate directory (`dev/`, `ci/`, `integration/`, `components/`)
2. Follow naming conventions (`feature.sh`)
3. Add documentation to script headers
4. Update this README

### Script Standards
- Include error handling and logging
- Use consistent exit codes (0=success, 1=failure)
- Add help text and usage examples
- Make scripts executable (`chmod +x`)

## 📚 Additional Resources

- [Planetarion Development Guide](../README.md)
- [API Documentation](../game-server/README.md)
- [Testing Best Practices](../.clinerules/workflow.md)
- [Memory Bank](../memory-bank/)

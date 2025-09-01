# Planetarion Testing Suite 🪐

Comprehensive testing setup for the Planetarion game server using Docker for isolated, reproducible testing.

## 🚀 Quick Start

```bash
# Run all tests
./run-tests.sh

# Run only backend tests
./run-tests.sh backend

# Run only E2E tests
./run-tests.sh e2e

# Clean up test containers
./run-tests.sh clean
```

## 📋 Test Structure

```
game-server/
├── tests/
│   ├── conftest.py              # Shared pytest fixtures
│   ├── unit/
│   │   ├── test_models.py       # Model unit tests
│   │   └── test_services.py     # Service unit tests
│   └── integration/
│       ├── test_auth.py         # Auth API tests
│       ├── test_planets.py      # Planet API tests
│       ├── test_fleet.py        # Fleet API tests
│       └── test_tick.py         # Tick API tests
├── frontend/tests/e2e/
│   ├── auth.spec.js            # Auth E2E tests
│   ├── dashboard.spec.js       # Dashboard E2E tests
│   └── fleet.spec.js           # Fleet E2E tests
├── scripts/
│   └── populate_test_data.py   # Test data generator
└── Docker testing files...
```

## 🐳 Docker Testing Architecture

### Test Services

- **`test-db`**: PostgreSQL test database
- **`test-backend`**: Flask API with testing dependencies
- **`test-frontend`**: React app with Playwright E2E testing

### Docker Files

- `docker-compose.test.yml`: Test service orchestration
- `backend/Dockerfile.test`: Backend testing container
- `frontend/Dockerfile.test`: Frontend E2E testing container

## 🧪 Test Categories

### Unit Tests
- **Models**: User, Planet, Fleet, Alliance, TickLog
- **Services**: Tick system, resource generation, fleet movement
- **Coverage**: CRUD operations, relationships, constraints

### Integration Tests
- **API Endpoints**: Auth, planets, fleets, ticks
- **Database**: Transactions, foreign keys, data integrity
- **Business Logic**: Game mechanics, validation

### End-to-End Tests
- **User Flows**: Registration → Login → Dashboard
- **UI Interactions**: Navigation, forms, real-time updates
- **Browser Compatibility**: Chrome headless testing

## 📊 Test Data

### Realistic Test Data Generation

The `scripts/populate_test_data.py` script generates:

- **200 Users**: Various usernames, emails, passwords
- **Planets**: 1-5 planets per user with random resources
- **Fleets**: Random ship compositions and missions
- **Alliances**: Multiple members with relationships
- **Tick Logs**: Resource changes and fleet events

```bash
# Generate test data (when containers are running)
docker-compose -f docker-compose.test.yml exec test-backend python scripts/populate_test_data.py
```

## 🛠️ Manual Testing

### Backend Tests Only

```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d test-db

# Run backend tests
docker-compose -f docker-compose.test.yml run --rm test-backend

# View test output
docker-compose -f docker-compose.test.yml logs test-backend
```

### E2E Tests Only

```bash
# Start all services
docker-compose -f docker-compose.test.yml up -d

# Run E2E tests
docker-compose -f docker-compose.test.yml run --rm test-frontend

# Debug with headed browser
docker-compose -f docker-compose.test.yml run --rm test-frontend npx playwright test --headed
```

### Local Development Testing

```bash
# Backend unit tests
cd backend
python -m pytest tests/unit/ -v

# Backend integration tests
python -m pytest tests/integration/ -v

# Frontend E2E tests
cd ../frontend
npm run test:e2e
```

## 🔧 Configuration

### Environment Variables

```bash
# Backend test environment
DATABASE_URL=postgresql://planetarion_user:planetarion_password@test-db:5432/planetarion_test
FLASK_ENV=testing
JWT_SECRET_KEY=test-jwt-secret-key-for-testing-only

# Frontend test environment
REACT_APP_API_URL=http://test-backend:5000
```

### Playwright Configuration

- **Browser**: Chromium (headless)
- **Timeout**: 30 seconds per test
- **Retries**: 2 on CI, 0 locally
- **Parallel**: Fully parallel execution

## 📈 Test Reports

### Backend Test Reports
```bash
# With coverage
docker-compose -f docker-compose.test.yml run --rm test-backend pytest tests/ --cov=. --cov-report=html

# View coverage report
open backend/htmlcov/index.html
```

### E2E Test Reports
```bash
# Playwright HTML report
docker-compose -f docker-compose.test.yml run --rm test-frontend npx playwright show-report

# Screenshots and videos (on failure)
ls frontend/test-results/
```

## 🐛 Debugging Tests

### Backend Tests

```bash
# Run specific test
docker-compose -f docker-compose.test.yml run --rm test-backend pytest tests/unit/test_models.py::TestUserModel::test_user_creation -v

# Debug with pdb
docker-compose -f docker-compose.test.yml run --rm test-backend pytest tests/unit/test_models.py -s --pdb
```

### E2E Tests

```bash
# Run single test
docker-compose -f docker-compose.test.yml run --rm test-frontend npx playwright test auth.spec.js --headed

# Debug mode
docker-compose -f docker-compose.test.yml run --rm test-frontend npx playwright test --debug

# Generate trace
docker-compose -f docker-compose.test.yml run --rm test-frontend npx playwright test --trace on
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd game-server
          ./run-tests.sh all
```

### Docker Hub Integration

```bash
# Build test images
docker build -f backend/Dockerfile.test -t planetarion-backend:test backend/
docker build -f frontend/Dockerfile.test -t planetarion-frontend:test frontend/

# Push to registry
docker tag planetarion-backend:test myregistry.com/planetarion-backend:test
docker push myregistry.com/planetarion-backend:test
```

## 🧹 Maintenance

### Cleanup

```bash
# Remove test containers and volumes
./run-tests.sh clean

# Remove test images
docker rmi $(docker images | grep test | awk '{print $3}')

# Clean test data
docker volume rm game-server_test_postgres_data
```

### Updating Dependencies

```bash
# Update backend dependencies
echo "pytest==7.4.1" >> backend/requirements.txt
echo "Faker==20.0.0" >> backend/requirements.txt

# Update frontend dependencies
cd frontend
npm update @playwright/test

# Rebuild test containers
docker-compose -f docker-compose.test.yml build --no-cache
```

## 📚 Best Practices

### Writing Tests

1. **Use descriptive test names**
2. **Test one thing per test function**
3. **Use fixtures for setup/teardown**
4. **Mock external dependencies**
5. **Test edge cases and error conditions**

### Test Organization

1. **Unit tests**: Fast, isolated, no external dependencies
2. **Integration tests**: Test component interactions
3. **E2E tests**: Full user workflows, slowest but most valuable

### Performance

1. **Parallel execution**: Tests run in parallel by default
2. **Database isolation**: Each test gets a clean database
3. **Resource cleanup**: Automatic cleanup prevents resource leaks

## 🆘 Troubleshooting

### Common Issues

**Database connection failed**
```bash
# Check if test-db is running
docker-compose -f docker-compose.test.yml ps

# View database logs
docker-compose -f docker-compose.test.yml logs test-db
```

**E2E tests can't connect to backend**
```bash
# Check service connectivity
docker-compose -f docker-compose.test.yml exec test-frontend curl http://test-backend:5000/health

# Verify environment variables
docker-compose -f docker-compose.test.yml exec test-frontend env | grep REACT_APP
```

**Playwright browser issues**
```bash
# Reinstall browsers
docker-compose -f docker-compose.test.yml exec test-frontend npx playwright install --force

# Check system dependencies
docker-compose -f docker-compose.test.yml exec test-frontend apt-get update && apt-get install -y libnss3
```

## 🎯 Test Coverage Goals

- **Backend**: >90% code coverage
- **Frontend**: >80% user flows covered
- **API**: All endpoints tested
- **Error Handling**: Edge cases and failures

## 📞 Support

For testing issues:
1. Check the test output logs
2. Review Docker container logs
3. Verify environment configuration
4. Check network connectivity between services

---

**Happy Testing! 🧪✨**

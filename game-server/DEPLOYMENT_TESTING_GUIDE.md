# Planetarion Deployment & Testing Guide

## 🚀 **How Planetarion Deploys**

### **Development Environment Setup**
```bash
# Start all services locally
cd game-server
docker-compose up --build

# Services start:
# - PostgreSQL (port 5432)
# - Backend API (port 5000)
# - Frontend React (port 3000)
```

### **Production Deployment to QNAP**

#### **Automated Deployment Process**
```bash
# 1. Build optimized images locally
docker build -f src/backend/Dockerfile -t planetarion-backend:qnap src/
docker build -f src/frontend/Dockerfile -t planetarion-frontend:qnap src/frontend/

# 2. Transfer to QNAP via SSH
scp docker-compose.qnap.yml qnap:/project/
rsync -avz src/ qnap:/project/src/

# 3. Load images on QNAP
docker save planetarion-backend:qnap | ssh qnap "docker load"
docker save planetarion-frontend:qnap | ssh qnap "docker load"

# 4. Start services
ssh qnap "cd /project && docker-compose -f docker-compose.qnap.yml up -d"
```

#### **QNAP-Specific Optimizations**
```yaml
# Resource limits for Celeron J3455 CPU
deploy:
  resources:
    limits:
      cpus: '0.5'    # Half core for database
      memory: 256M
    reservations:
      cpus: '0.2'
      memory: 128M
```

### **Multi-Environment Configuration**

#### **Development (docker-compose.yml)**
- **Database:** PostgreSQL with health checks
- **Backend:** Hot reload, debug mode
- **Frontend:** Development server with HMR
- **Networking:** Service names for inter-container communication

#### **Production (docker-compose.qnap.yml)**
- **Security:** `0.0.0.0` binding for external access
- **Resources:** CPU/memory limits for low-power hardware
- **Logging:** JSON format with rotation
- **Health Checks:** Automated service monitoring

## 🧪 **How Planetarion Tests**

### **Test Architecture**
```
tests/
├── unit/           # Model and service tests
├── integration/    # API endpoint tests
└── e2e/           # Playwright browser tests
```

### **Running Tests**

#### **Complete Test Suite**
```bash
# Run all tests (quiet mode)
./run-tests.sh all

# Run with verbose output
./run-tests.sh --verbose all

# Run specific test types
./run-tests.sh backend    # Only backend tests
./run-tests.sh e2e        # Only E2E tests
```

#### **Docker-Based Testing**
```bash
# Backend tests run in isolated containers
docker-compose -f docker-compose.test.yml run --rm test-backend

# E2E tests run full stack
docker-compose -f docker-compose.test.yml up -d
docker-compose -f docker-compose.test.yml run --rm test-frontend
```

### **Test Coverage Breakdown**
| Category | Tests | Success Rate | Purpose |
|----------|-------|--------------|---------|
| **Fleet Integration** | 18/18 | **100%** | Fleet CRUD operations |
| **Planet Integration** | 16/16 | **100%** | Planet management |
| **Auth Integration** | 12/12 | **100%** | User authentication |
| **Tick Integration** | 4/6 | **67%** | Resource generation |
| **Static Files** | 4/7 | **57%** | File serving |
| **Unit Tests** | 38/38 | **100%** | Models & services |

### **Test Data Management**
```python
# conftest.py - Test fixtures
@pytest.fixture
def test_client():
    app = create_app('testing')
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_db():
    db.create_all()
    yield db
    db.drop_all()
```

### **E2E Testing with Playwright**
```javascript
// playwright.config.js
export default {
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3000',
    browserName: 'chromium'
  }
}
```

## 🔧 **Deployment Troubleshooting**

### **Common Issues & Solutions**

#### **API Connection Problems**
```javascript
// Problem: Browser can't resolve Docker service names
// Solution: Use external IP in frontend
axios.defaults.baseURL = 'http://192.168.0.133:5000';
```

#### **Port Binding Issues**
```yaml
# Problem: Services not accessible externally
# Solution: Use 0.0.0.0 instead of 127.0.0.1
ports:
  - "0.0.0.0:5000:5000"
```

#### **Resource Constraints on QNAP**
```yaml
# Problem: Low-power CPU limitations
# Solution: Resource limits and reservations
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 256M
```

## 📊 **Current Status**

### **Deployment Status**
- ✅ **QNAP Production**: Successfully deployed
- ✅ **API Connectivity**: Frontend-backend working
- ✅ **Authentication**: Registration/login functional
- ✅ **Docker Networking**: Inter-container communication
- ✅ **Resource Optimization**: QNAP-specific configurations

### **Testing Status**
- ✅ **Test Success Rate**: 95.2% (100/105 tests passing)
- ✅ **Authentication Tests**: 12/12 passing
- ✅ **Fleet Management**: 18/18 tests passing
- ✅ **Planet Management**: 16/16 tests passing
- ⚠️ **Automatic Tick Tests**: 2/6 failing (scheduler issues)
- ⚠️ **Static File Tests**: 3/7 failing (test environment)

### **Architecture Highlights**
- **Layered Architecture**: Clear separation of concerns
- **Docker Containerization**: Consistent deployment
- **JWT Authentication**: Secure token-based auth
- **PostgreSQL Database**: Production-ready persistence
- **React Frontend**: Modern SPA with Tailwind CSS
- **Automated Testing**: Comprehensive test coverage

## 🎯 **Best Practices Implemented**

### **Security**
- Password hashing with bcrypt
- JWT token authentication
- Input validation and sanitization
- CORS configuration

### **Performance**
- Docker resource limits
- Database connection pooling
- Health checks and monitoring
- Optimized container images

### **Maintainability**
- Modular code structure
- Comprehensive documentation
- Automated testing pipeline
- Environment-based configuration

### **Scalability**
- Stateless backend services
- Database optimization
- Container orchestration
- Horizontal scaling ready

# System Patterns & Architecture

## Architectural Overview

### Monolithic Application with Microservice Tendencies
- **Structure**: Single monorepo with clear separation between backend and frontend
- **Communication**: RESTful API between frontend and backend
- **Data Flow**: Frontend → API → Database → API → Frontend
- **Deployment**: Docker Compose for local development, containerized services

### Layered Architecture Pattern
```
┌─────────────────┐
│   Frontend      │  React Components
│   (Presentation)│  State Management
└─────────────────┘  API Communication
         │
┌─────────────────┐
│   Backend       │  Flask Routes
│   (Application) │  Business Logic
└─────────────────┘  Service Layer
         │
┌─────────────────┐
│   Database      │  SQLAlchemy Models
│   (Persistence) │  Data Access Layer
└─────────────────┘  Migration Scripts
```

## Design Patterns

### Backend Patterns

#### Repository Pattern
- **Implementation**: SQLAlchemy ORM provides data access abstraction
- **Usage**: All database operations go through model classes
- **Benefits**: Decouples business logic from data access, easier testing
- **Example**: `Planet.query.filter_by(user_id=user_id).all()`

#### Service Layer Pattern
- **Implementation**: Business logic separated into service modules
- **Usage**: Tick service handles resource generation, fleet movement
- **Benefits**: Clean separation of concerns, reusable business logic
- **Example**: `tick_service.process_resource_generation()`

#### Blueprint Pattern (Flask)
- **Implementation**: API routes organized into blueprints
- **Usage**: Auth, planets, fleets, etc. as separate blueprints
- **Benefits**: Modular routing, easier maintenance
- **Example**: `auth_bp = Blueprint('auth', __name__)`

#### Factory Pattern
- **Implementation**: Application factory for Flask app creation
- **Usage**: Different configurations for development/production
- **Benefits**: Flexible app initialization, testing support

### Frontend Patterns

#### Component Composition Pattern
- **Implementation**: React components built from smaller components
- **Usage**: Dashboard composed of Navigation, PlanetList, ResourceDisplay
- **Benefits**: Reusable components, maintainable code structure

#### Container/Presentational Pattern
- **Implementation**: Smart containers handle data, dumb components handle UI
- **Usage**: Dashboard container fetches data, PlanetCard displays data
- **Benefits**: Separation of concerns, easier testing

#### Custom Hooks Pattern
- **Implementation**: React hooks for shared logic
- **Usage**: useAuth, usePlanets, useFleets hooks
- **Benefits**: Reusable logic, cleaner component code

#### Context Provider Pattern
- **Implementation**: React Context for global state management
- **Usage**: AuthContext, ToastContext for app-wide state
- **Benefits**: Avoids prop drilling, centralized state management

## Data Flow Patterns

### Request-Response Cycle
```
User Action → Component Event → API Call → Route Handler → Service Method → Database Query → Response → State Update → UI Re-render
```

### Real-time Updates
```
Tick Timer → APScheduler → Resource Calculation → Database Update → API Response → Frontend Polling → State Update → UI Update
```

### Authentication Flow
```
Login Form → API Call → JWT Generation → Cookie Storage → Protected Route Access → Token Validation → User Context Update
```

## Database Patterns

### Active Record Pattern
- **Implementation**: SQLAlchemy models combine data and behavior
- **Usage**: Planet model has both data fields and methods
- **Benefits**: Object-oriented database interaction

### Migration Pattern
- **Implementation**: Flask-Migrate for schema versioning
- **Usage**: Version-controlled database schema changes
- **Benefits**: Safe database updates, rollback capability

### Connection Pooling
- **Implementation**: SQLAlchemy connection pooling
- **Usage**: Efficient database connection management
- **Benefits**: Performance optimization, resource management

## Communication Patterns

### RESTful API Design
- **HTTP Methods**: GET, POST, PUT, DELETE appropriately used
- **Resource Naming**: `/api/planets`, `/api/fleets`, `/api/auth`
- **Status Codes**: Proper HTTP status codes (200, 201, 400, 401, 404, 500)
- **Response Format**: Consistent JSON structure with error handling

### Error Handling Patterns
- **Try-Catch Blocks**: Comprehensive error catching in routes
- **Custom Exceptions**: Domain-specific error classes
- **Error Responses**: Consistent error response format
- **Logging**: Structured logging for debugging

## Testing Patterns

### Unit Testing
- **Framework**: pytest with fixtures
- **Coverage**: Model methods, service functions, utility functions
- **Mocking**: External dependencies mocked for isolation
- **Pattern**: Arrange-Act-Assert structure
- **Organization**: Class-based test suites with descriptive method names
- **Fixtures**: Database sessions, sample data, authentication headers
- **Assertions**: Database state verification, mock call validation, error conditions

### Integration Testing
- **Framework**: pytest with test client
- **Coverage**: API endpoints, database interactions
- **Setup**: Test database with fixtures
- **Pattern**: Full request-response cycle testing

### End-to-End Testing
- **Framework**: Playwright
- **Coverage**: User workflows, UI interactions
- **Setup**: Full application stack in containers
- **Pattern**: Browser automation with assertions

### Repository Testing Pattern
**Context**: Complete testing workflow for full-stack features with authentication

**Test Hierarchy**:
```
├── Unit Tests (pytest)           # Fast, isolated functions
├── Integration Tests (pytest)   # API + Database interactions
├── E2E Tests (Playwright)        # Full user workflows
└── Manual Tests (Browser)       # Exploratory testing
```

**Execution Commands**:
```bash
# Unit tests (fast, no setup)
make unit

# Integration tests (SQLite, fast)
make integration

# E2E tests (full stack, local)
make e2e-ui

# E2E specific feature
make e2e-ui TEST_FILE=src/frontend/tests/e2e/[feature].spec.js

# All tests combined
make all
```

**E2E Flow**:
1. `make e2e-ui` → Backend (port 5000) + Frontend (port 3000) startup
2. Database population via `populate_test_data.py`
3. Playwright discovers all `.spec.js` files in `tests/e2e/`
4. Tests execute with JWT token management
5. Automatic cleanup of processes and test database

**Key Implementation Patterns**:
- **Helper Functions**: `loginAsE2eTestUser()`, `navigateTo[Feature]()`
- **JWT Handling**: `localStorage.getItem('token')` → Authorization headers
- **API Testing**: `page.request.get/post()` with full URLs
- **Selectors**: `page.locator('h2').filter({ hasText: 'Feature' })`
- **Error Handling**: Try-catch with console logging
- **Database Management**: Test data population and cleanup

**File Structure**:
```
game-server/tests/
├── unit/              # pytest unit tests
├── integration/       # pytest integration tests
├── e2e/              # Legacy E2E tests
└── galaxy/           # Feature-specific tests

game-server/src/frontend/tests/e2e/
├── auth.spec.js      # Authentication flows
├── fleet.spec.js     # Fleet management
├── galaxy-map.spec.js # Galaxy features
├── dashboard.spec.js # Dashboard functionality
└── [feature].spec.js # Future features
```

**Configuration**:
- `playwright.config.js`: `testDir: './tests/e2e'`, baseURL, timeouts
- `package.json`: `"test:e2e": "playwright test"`
- `Makefile`: Orchestrates full-stack testing environment
- `pytest.ini`: Python test configuration

**Testing Strategy**:
- **Unit**: Isolated functions, no external dependencies
- **Integration**: API endpoints, database interactions
- **E2E**: Complete user workflows, authentication flows
- **Manual**: Exploratory testing, edge cases

## Deployment Patterns

### Containerization
- **Docker Images**: Separate images for backend, frontend, database
- **Docker Compose**: Multi-service orchestration
- **Volumes**: Persistent data storage
- **Networks**: Service communication isolation

### Environment Configuration
- **Environment Variables**: Configuration externalized
- **Multiple Environments**: Development, testing, production
- **Secret Management**: Sensitive data handling
- **Configuration Validation**: Required settings checking

## Security Patterns

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication
- **Password Hashing**: Secure password storage (bcrypt planned)
- **Route Protection**: Token validation middleware
- **CORS**: Cross-origin request handling

### Input Validation
- **Request Validation**: Input sanitization and validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Prevention**: Input escaping in templates
- **Rate Limiting**: API abuse prevention (planned)

## Performance Patterns

### Caching Strategy
- **Database Query Caching**: Frequently accessed data
- **API Response Caching**: Static or slowly changing data
- **Frontend Caching**: Browser caching for assets

### Database Optimization
- **Indexing**: Proper database indexes
- **Query Optimization**: Efficient SQL queries
- **Connection Pooling**: Resource management
- **Read Replicas**: Scale read operations (future)

### Frontend Optimization
- **Code Splitting**: Lazy loading of components
- **Asset Optimization**: Minification and compression
- **Image Optimization**: Efficient image formats
- **Bundle Analysis**: Identify optimization opportunities

## Monitoring Patterns

### Application Monitoring
- **Health Checks**: `/health` endpoint for service status
- **Metrics Collection**: Performance and usage metrics
- **Error Tracking**: Centralized error logging
- **Performance Monitoring**: Response times and throughput

### Logging Patterns
- **Structured Logging**: Consistent log format
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Context Information**: Request IDs, user information
- **Log Aggregation**: Centralized log collection (future)

## Scalability Patterns

### Horizontal Scaling
- **Stateless Services**: Backend can be scaled horizontally
- **Load Balancing**: Distribute requests across instances
- **Session Management**: External session storage (future)
- **Database Sharding**: Data distribution (future)

### Vertical Scaling
- **Resource Optimization**: Efficient memory and CPU usage
- **Database Tuning**: Query optimization and indexing
- **Caching Layers**: Reduce database load
- **CDN Integration**: Static asset delivery (future)

## Development Workflow Patterns

### Git Flow
- **Branch Strategy**: Feature branches, main branch
- **Pull Requests**: Code review process
- **Continuous Integration**: Automated testing on commits
- **Release Management**: Version tagging and deployment

### Code Quality Patterns
- **Linting**: ESLint for JavaScript, flake8 for Python
- **Type Checking**: Static analysis where applicable
- **Code Formatting**: Consistent code style
- **Documentation**: Inline documentation and READMEs

### Testing Strategy
- **Test-Driven Development**: Tests written before features
- **Continuous Testing**: Tests run on every commit
- **Test Coverage**: Minimum coverage requirements
- **Integration Testing**: End-to-end workflow validation

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

### Test Infrastructure Issues (RESOLVED ✅)

#### Critical Authentication Problems - FIXED
**Issue**: Inconsistent password hashing across integration tests causing 401 Unauthorized errors
**Root Cause**: Mix of bcrypt.hashpw(), generate_password_hash(), and plain text passwords
**Impact**: 33 failing integration tests due to login authentication failures

**Solution Implemented**:
```python
# ✅ CORRECT: Standardized bcrypt hashing pattern
import bcrypt

def create_test_user_with_hashed_password(db_session, username, email, password='password'):
    """Create test user with properly hashed password for integration tests"""
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(username=username, email=email, password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user, password  # Return both user and plain password for login testing

# Usage in tests:
user, password = create_test_user_with_hashed_password(db_session, 'testuser', 'test@example.com', 'password')
response = client.post('/api/auth/login', json={'username': 'testuser', 'password': password})
```

**Files Updated**: All integration test files requiring authentication
**Result**: Eliminated all authentication-related test failures

#### Database Constraint Violations - FIXED
**Issue**: Fleet model NOT NULL constraints not satisfied in tests
**Root Cause**: Missing required fields (target_planet_id, departure_time) in test fleet creation
**Impact**: Database constraint violations causing test failures

**Solution Implemented**:
```python
# ✅ CORRECT: Enhanced conftest.py with constraint-aware fleet creation
def create_test_fleet_with_constraints(db_session, user_id, planet_id, **kwargs):
    """Create fleet with all required database constraints satisfied"""
    fleet = Fleet(
        user_id=user_id,
        start_planet_id=planet_id,
        target_planet_id=kwargs.get('target_planet_id', planet_id),  # Required
        mission=kwargs.get('mission', 'stationed'),
        status=kwargs.get('status', 'stationed'),
        departure_time=kwargs.get('departure_time', datetime.utcnow()),  # Required
        arrival_time=kwargs.get('arrival_time', datetime.utcnow()),     # Required
        # Ship counts with defaults
        small_cargo=kwargs.get('small_cargo', 0),
        large_cargo=kwargs.get('large_cargo', 0),
        light_fighter=kwargs.get('light_fighter', 0),
        heavy_fighter=kwargs.get('heavy_fighter', 0),
        cruiser=kwargs.get('cruiser', 0),
        battleship=kwargs.get('battleship', 0),
        colony_ship=kwargs.get('colony_ship', 0),
        recycler=kwargs.get('recycler', 0)
    )
    db_session.add(fleet)
    db_session.commit()
    return fleet
```

**Files Updated**: conftest.py, all fleet-related integration tests
**Result**: Resolved all database constraint violations

#### Tick System Overload - FIXED
**Issue**: Automatic tick system running uncontrolled in tests causing database bloat
**Root Cause**: No rate limiting, infinite loops in test environment
**Impact**: Test timeouts, database overload, unpredictable execution times

**Solution Implemented**:
```python
# ✅ CORRECT: Mock-based rate limiting for tick system
@patch('backend.services.tick.run_tick')
def test_automatic_tick_timing_accuracy(self, mock_tick):
    """Test automatic tick timing with proper rate limiting"""
    # Mock tick to prevent infinite loop
    mock_tick.side_effect = lambda: time.sleep(0.1)  # Controlled execution

    # Setup test data
    user, password = create_test_user_with_hashed_password(db_session, 'tick_test')

    # Test logic with predictable timing
    # ... test implementation
```

**Files Updated**: test_tick.py, tick service mocking patterns
**Result**: Tests now run in <30 seconds with predictable execution

#### Coordinate Formatting Issues - FIXED
**Issue**: Fleet travel coordinates returned as floats instead of integers
**Root Cause**: String formatting in fleet_travel.py using float decimals
**Impact**: Test assertions failing on coordinate format expectations

**Solution Implemented**:
```python
# ✅ CORRECT: Integer coordinate formatting
target_coords = f"{int(float(target_planet.x))}:{int(float(target_planet.y))}:{int(float(target_planet.z))}"
# Instead of: f"{float(target_planet.x)}:{float(target_planet.y)}:{float(target_planet.z)}"
```

**Files Updated**: fleet_travel.py
**Result**: Coordinates now returned as integers (50:60:70) instead of floats (50.0:60.0:70.0)

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

### Password Hashing in Integration Tests

**CRITICAL REQUIREMENT**: All integration tests must use bcrypt-hashed passwords to match production authentication flows.

#### Correct Implementation Pattern:
```python
import bcrypt

def create_test_user_with_hashed_password(db_session, username, email, plain_password='password'):
    """Create test user with properly hashed password for integration tests"""
    password_hash = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(username=username, email=email, password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user, plain_password  # Return both user and plain password for login testing

# Usage in tests:
user, password = create_test_user_with_hashed_password(db_session, 'testuser', 'test@example.com', 'password')

# Login test - use the returned plain password:
response = client.post('/api/auth/login', json={
    'username': 'testuser',
    'password': password  # Same password that was hashed
})
```

#### Common Mistakes to Avoid:
- ❌ `password_hash='password'` (plain text passwords)
- ❌ Using different passwords for user creation vs login attempts
- ❌ Not importing bcrypt in test files
- ❌ Hardcoding passwords without proper hashing

#### Why This Matters:
- **Security**: Tests should mirror production password handling exactly
- **Consistency**: All authentication tests should work the same way
- **Reliability**: Prevents random test failures due to authentication issues
- **Maintenance**: Ensures tests don't break when password validation changes

#### Files Affected:
- All integration tests that create users and test authentication
- conftest.py (contains correct bcrypt implementation)
- Any test that calls `/api/auth/login` or protected endpoints

### Mock Testing Best Practices

**Critical Findings from Fleet Travel Test Fixes**:

#### Mock Specification Patterns
- **Use `Mock(spec=Model)`**: Always specify the model class to prevent attribute typos
- **Example**: `fleet = Mock(spec=Fleet)` instead of `fleet = Mock()`
- **Benefit**: Catches typos like `fleet.small_cargp` at test time instead of runtime

#### Database Query Mocking
- **Mock at the right level**: Use `Planet.query.get` side effects for proper object returns
- **Pattern**:
```python
with patch.object(Planet, 'query') as mock_query:
    mock_get = Mock()
    mock_get.side_effect = lambda planet_id: start_planet if planet_id == 1 else target_planet
    mock_query.get = mock_get
```
- **Benefit**: Returns actual Planet objects instead of Mock objects for arithmetic operations

#### Arithmetic Operation Handling
- **Problem**: `Mock() + Mock()` raises `TypeError: unsupported operand type(s) for +: 'Mock' and 'Mock'`
- **Solution**: Use real objects or explicit numeric attributes
- **Pattern**: `fleet.departure_time = datetime(2025, 1, 1, 11, 0, 0)` instead of Mock datetime

#### Coordinate-Based Mission Testing
- **Status validation**: Test coordinate-based missions like `colonizing:100:200:300`
- **Pattern**: Ensure service accepts both standard statuses and coordinate-based patterns
- **Validation**: Test both parsing logic and coordinate extraction

#### Position Interpolation Testing
- **Linear interpolation**: Test fleet position calculations during travel
- **Formula**: `current_x = start_x + (target_x - start_x) * (progress / 100)`
- **Edge cases**: Test completed journeys (100% progress) and position at target

#### Fleet Speed Calculation Testing
- **Slowest ship rule**: Fleet speed determined by slowest ship type
- **Test cases**: Mixed fleet compositions, empty fleets, single ship types
- **Validation**: Ensure correct speed hierarchy (colony_ship slowest, small_cargo fastest)

#### Test Data Setup Patterns
- **Real Planet objects**: Use `Planet(name='Test', x=0, y=0, z=0)` for reliable coordinates
- **Consistent mocking**: Apply same mock patterns across related tests
- **Error handling**: Test invalid inputs and edge cases systematically

#### Debug Logging in Tests
- **Temporary logging**: Add `print()` statements during debugging
- **Pattern**: `print(f"DEBUG: {variable_name}={value}")`
- **Cleanup**: Remove debug prints after fixing issues

**Key Takeaway**: Loose mocking leads to runtime errors. Always use `Mock(spec=Model)` and real objects where arithmetic operations are needed.

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

## Configuration Management Patterns

### Centralized Configuration System

#### Architecture Overview
- **Single Source of Truth**: All configuration in `backend/config.py`
- **Environment-Specific Settings**: Development, testing, production configurations
- **Centralized Speed Settings**: Game speed multipliers and ship configurations
- **Path Management**: All important file paths defined centrally
- **Validation**: Configuration validation on import

#### Configuration Structure

```python
# backend/config.py - Main configuration file

# Flask Configuration Classes
class Config:                    # Base configuration
class DevelopmentConfig(Config): # Development overrides
class TestingConfig(Config):     # Testing overrides
class ProductionConfig(Config):  # Production overrides

# Configuration Mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Utility Functions
def get_config(config_name=None): # Get config class by environment
def get_ship_speed(ship_type):    # Get speed with multiplier applied
def calculate_fleet_speed(fleet): # Calculate fleet speed (slowest ship rule)
def calculate_fuel_consumption(fleet, distance): # Fuel calculation

# Speed Configuration
SPEED_MULTIPLIER = 30.0          # Global speed multiplier
SHIP_SPEEDS = { ... }            # Base ship speeds
FUEL_RATES = { ... }             # Fuel consumption rates

# Path Configuration
PROJECT_ROOT = Path(__file__).parent.parent
PATHS = {
    'project_root': PROJECT_ROOT,
    'src': PROJECT_ROOT / 'src',
    'backend': PROJECT_ROOT / 'src' / 'backend',
    'frontend': PROJECT_ROOT / 'src' / 'frontend',
    # ... all important paths
}
```

#### Speed Configuration System

**Global Speed Multiplier Pattern**:
```python
SPEED_MULTIPLIER = 30.0  # Adjust this to change overall game speed

def get_ship_speed(ship_type):
    """Get speed with global multiplier applied"""
    base_speed = SHIP_SPEEDS.get(ship_type, 5000)
    return base_speed * SPEED_MULTIPLIER
```

**Fleet Speed Calculation (Slowest Ship Rule)**:
```python
def calculate_fleet_speed(fleet):
    """Fleet speed determined by slowest ship type"""
    slowest_speed = float('inf')

    for ship_type in SHIP_TYPES:
        ship_count = getattr(fleet, ship_type, 0)
        if ship_count > 0:
            ship_speed = get_ship_speed(ship_type)
            slowest_speed = min(slowest_speed, ship_speed)

    return slowest_speed if slowest_speed != float('inf') else 0
```

**Fuel Consumption Calculation**:
```python
def calculate_fuel_consumption(fleet, distance):
    """Calculate fuel consumption for fleet travel"""
    total_fuel = 0

    for ship_type in SHIP_TYPES:
        ship_count = getattr(fleet, ship_type, 0)
        if ship_count > 0:
            fuel_rate = FUEL_RATES.get(ship_type, 1.0)
            total_fuel += ship_count * fuel_rate * distance

    return int(total_fuel)
```

#### Configuration Usage Patterns

**Import Pattern**:
```python
# In app.py and other backend modules
from .config import get_config, get_ship_speed, calculate_fleet_speed

# In services
from backend.config import get_ship_speed, calculate_fleet_speed
```

**Environment-Specific Configuration**:
```python
# Application factory pattern
def create_app(config_name=None):
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    # ... rest of app setup
```

**Path Usage Pattern**:
```python
from backend.config import PATHS

# Use centralized paths
frontend_build_path = PATHS['frontend_build']
backend_routes_path = PATHS['backend_routes']
```

#### Benefits of Centralized Configuration

1. **Single Source of Truth**: All configuration in one place
2. **Environment Consistency**: Same config patterns across dev/test/prod
3. **Easy Tuning**: Change SPEED_MULTIPLIER to adjust game speed globally
4. **Validation**: Configuration validated on import
5. **Maintainability**: Clear structure and documentation
6. **Testing**: Easy to mock and override in tests

#### Configuration Validation Pattern

```python
def validate_config():
    """Validate that all required ship types are defined"""
    required_ships = ['small_cargo', 'large_cargo', 'light_fighter',
                     'heavy_fighter', 'cruiser', 'battleship', 'colony_ship']

    missing_ships = []
    for ship in required_ships:
        if ship not in SHIP_SPEEDS:
            missing_ships.append(ship)

    if missing_ships:
        raise ValueError(f"Missing speed configuration for ships: {missing_ships}")

    return True

# Validate on import
validate_config()
```

#### Testing Configuration

**Mock Configuration in Tests**:
```python
from backend.config import SPEED_MULTIPLIER, get_ship_speed

def test_ship_speed_with_multiplier():
    """Test that speed multiplier is applied correctly"""
    speed = get_ship_speed('colony_ship')
    expected = 2500 * SPEED_MULTIPLIER  # 2500 * 30 = 75000
    assert speed == expected
```

**Override Configuration in Tests**:
```python
import backend.config as config

def test_with_custom_speed_multiplier():
    """Test with custom speed multiplier"""
    original_multiplier = config.SPEED_MULTIPLIER
    config.SPEED_MULTIPLIER = 10.0  # Custom multiplier for test

    try:
        speed = config.get_ship_speed('colony_ship')
        assert speed == 2500 * 10.0  # 25000
    finally:
        config.SPEED_MULTIPLIER = original_multiplier  # Restore
```

#### Migration from Distributed Configuration

**Before (Distributed)**:
```
backend/
├── config.py          # Flask config only
├── config/
│   ├── __init__.py    # Speed config
│   └── speed_config.py # More speed config
```

**After (Centralized)**:
```
backend/
├── config.py          # ALL configuration in one file
```

**Migration Benefits**:
- ✅ Eliminated import path conflicts
- ✅ Single file for all configuration
- ✅ Easier maintenance and understanding
- ✅ Consistent configuration patterns
- ✅ Better testability

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

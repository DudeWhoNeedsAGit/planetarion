# Technology Context

## Backend Technology Stack

### Core Framework
- **Flask 2.3.3**: Lightweight WSGI web application framework
- **Flask-RESTful**: Extension for building REST APIs
- **Flask-Migrate**: Database migration management
- **Flask-CORS**: Cross-origin resource sharing support

### Database Layer
- **SQLAlchemy 2.0**: Python SQL toolkit and ORM
- **PostgreSQL 15**: Primary production database
- **SQLite**: Development and testing database
- **Alembic**: Database migration tool (via Flask-Migrate)

### Authentication & Security
- **PyJWT**: JSON Web Token implementation
- **Werkzeug**: Password hashing utilities
- **bcrypt**: Secure password hashing (planned implementation)

### Task Scheduling
- **APScheduler**: Advanced Python Scheduler for background tasks
- **Background Tasks**: Automated resource generation every 5 seconds

### Development Tools
- **pytest**: Testing framework with fixtures and plugins
- **coverage**: Code coverage measurement
- **black**: Code formatting
- **flake8**: Linting and style checking

## Frontend Technology Stack

### Core Framework
- **React 18.2.0**: JavaScript library for building user interfaces
- **React DOM**: React rendering library for web
- **React Router**: Declarative routing for React applications

### State Management
- **React Hooks**: Built-in state management (useState, useEffect)
- **Context API**: React's built-in state sharing mechanism
- **Custom Hooks**: Reusable stateful logic

### Styling & UI
- **Tailwind CSS 3.3.3**: Utility-first CSS framework
- **PostCSS**: CSS processing tool
- **Autoprefixer**: CSS vendor prefixing
- **Tailwind Config**: Custom theme and color scheme

### HTTP Communication
- **Axios 1.4.0**: Promise-based HTTP client
- **Fetch API**: Browser native HTTP requests (fallback)

### Build Tools
- **Create React App**: Build setup and development server
- **Webpack**: Module bundler (via CRA)
- **Babel**: JavaScript transpiler
- **ESLint**: JavaScript linting

### Testing Framework
- **Playwright**: End-to-end testing framework (currently slow due to Docker)
- **React Testing Library**: Testing utilities for React
- **Jest**: JavaScript testing framework (via CRA)
- **pytest**: Python testing framework for backend and integration tests

### Testing Strategy Evolution
- **Current Issue**: E2E tests are slow (2-5 minutes) due to Docker + Chromium startup
- **Recommended**: API Integration Tests for faster iteration (20-60 seconds)
- **Alternative**: Component unit tests for isolated UI testing (10-30 seconds)
- **Future**: Mock Service Worker for offline UI testing

## Infrastructure & Deployment

### Containerization
- **Docker**: Container platform for application packaging
- **Docker Compose**: Multi-container application definition
- **Dockerfile**: Backend and frontend container definitions
- **Docker Compose Override**: Environment-specific configurations

### Development Environment
- **Python 3.11**: Backend runtime environment
- **Node.js 18**: Frontend runtime environment
- **npm**: JavaScript package manager
- **pip**: Python package manager

### Production Considerations
- **Gunicorn**: WSGI HTTP Server for Flask
- **Nginx**: Reverse proxy and static file serving
- **PM2**: Process manager for Node.js applications
- **PostgreSQL**: Production database server

## Development Workflow Tools

### Version Control
- **Git**: Distributed version control system
- **GitHub**: Code hosting and collaboration platform
- **Conventional Commits**: Standardized commit message format

### Code Quality
- **Pre-commit Hooks**: Automated code quality checks
- **GitHub Actions**: CI/CD pipeline (planned)
- **Code Coverage**: Test coverage reporting
- **Documentation**: Markdown-based project documentation

### Testing Infrastructure
- **Docker Test Containers**: Isolated testing environment
- **Test Databases**: Separate database instances for testing
- **Mock Services**: Simulated external dependencies
- **Parallel Testing**: Concurrent test execution

## API Design & Communication

### RESTful API Standards
- **HTTP Methods**: GET, POST, PUT, DELETE
- **Status Codes**: Standard HTTP response codes
- **Content-Type**: application/json
- **Authentication**: Bearer token (JWT)

### API Documentation
- **OpenAPI/Swagger**: API specification format (planned)
- **Interactive Docs**: API testing interface (planned)
- **Endpoint Documentation**: Inline code documentation

### Real-time Communication
- **Polling**: Current implementation for real-time updates
- **WebSockets**: Planned for future real-time features
- **Server-Sent Events**: Alternative for push notifications

## Database Schema & Models

### Core Models
- **User**: Authentication and profile data
- **Planet**: Player colonies with resources and structures
- **Fleet**: Ship collections with mission capabilities
- **Alliance**: Player grouping system (planned)
- **TickLog**: Resource generation audit trail

### Relationships
- **One-to-Many**: User → Planets, User → Fleets
- **Many-to-Many**: Users ↔ Alliances (planned)
- **Self-referencing**: Fleet missions between planets

### Data Integrity
- **Foreign Keys**: Referential integrity constraints
- **Unique Constraints**: Prevent duplicate data
- **Check Constraints**: Data validation at database level
- **Indexes**: Query performance optimization

## Security Implementation

### Authentication Flow
- **Registration**: User account creation with validation
- **Login**: Credential verification and JWT issuance
- **Token Validation**: Middleware for protected routes
- **Logout**: Token invalidation

### Data Protection
- **Password Hashing**: Secure storage (bcrypt implementation pending)
- **Input Sanitization**: XSS and injection prevention
- **CORS Configuration**: Cross-origin request policies
- **Rate Limiting**: API abuse prevention (planned)

### Session Management
- **JWT Tokens**: Stateless authentication tokens
- **Token Expiration**: Automatic session timeout
- **Refresh Tokens**: Extended session management (planned)
- **Secure Cookies**: HTTP-only cookie storage

## Performance Considerations

### Backend Optimization
- **Database Connection Pooling**: Efficient connection management
- **Query Optimization**: Indexed queries and efficient SQL
- **Caching Layer**: Redis integration (planned)
- **Async Processing**: Background task handling

### Frontend Optimization
- **Code Splitting**: Lazy loading of components
- **Asset Bundling**: Optimized webpack configuration
- **Image Optimization**: Efficient image formats and compression
- **Service Workers**: Offline capability (planned)

### Monitoring & Observability
- **Application Metrics**: Response times and error rates
- **Database Monitoring**: Query performance and connection health
- **Log Aggregation**: Centralized logging system
- **Health Checks**: Service availability monitoring

## Third-Party Integrations

### Development Dependencies
- **Faker**: Test data generation
- **Flask-Testing**: Flask-specific testing utilities
- **Coverage.py**: Code coverage reporting
- **Pytest fixtures**: Test data and setup management

### Production Dependencies
- **Gunicorn**: Production WSGI server
- **Psycopg2**: PostgreSQL adapter for Python
- **Redis**: Caching and session storage (planned)
- **Sentry**: Error tracking and monitoring (planned)

## Environment Management

### Development Environment
- **Local Setup**: Docker Compose for full stack development
- **Hot Reloading**: Automatic code reloading during development
- **Debug Mode**: Enhanced error reporting and debugging tools
- **Test Databases**: Isolated testing environments

### Staging Environment
- **Mirror Production**: Identical setup to production
- **Automated Deployment**: CI/CD pipeline integration
- **Data Seeding**: Test data population scripts
- **Performance Testing**: Load testing and optimization

### Production Environment
- **Container Orchestration**: Docker Swarm or Kubernetes (planned)
- **Load Balancing**: Request distribution across instances
- **Database Clustering**: High availability database setup
- **Backup Strategy**: Automated data backup and recovery

## Future Technology Roadmap

### Short Term (3-6 months)
- **WebSocket Integration**: Real-time communication
- **Redis Caching**: Performance optimization
- **API Documentation**: OpenAPI specification
- **Monitoring Dashboard**: Application metrics

### Medium Term (6-12 months)
- **Microservices Migration**: Service decomposition
- **GraphQL API**: Flexible data fetching
- **Mobile Application**: React Native implementation
- **Advanced Analytics**: Player behavior tracking

### Long Term (1-2 years)
- **Serverless Architecture**: AWS Lambda or similar
- **Machine Learning**: AI-powered game features
- **Blockchain Integration**: In-game economy
- **VR/AR Features**: Immersive gaming experience

## Technology Decision Rationale

### Flask over Django
- **Lightweight**: Minimal overhead for API-focused application
- **Flexibility**: Choose only needed components
- **Performance**: Faster startup and lower memory usage
- **Learning Curve**: Simpler for team adoption

### React over Vue/Angular
- **Ecosystem**: Largest community and library ecosystem
- **Flexibility**: Can be used for web and mobile
- **Performance**: Virtual DOM and efficient rendering
- **Job Market**: High demand for React developers

### PostgreSQL over MySQL
- **JSON Support**: Native JSON column types
- **Advanced Features**: Full-text search, geospatial data
- **ACID Compliance**: Strong data consistency guarantees
- **Open Source**: No licensing costs

### Docker over Virtual Machines
- **Lightweight**: Faster startup and resource efficient
- **Portability**: Consistent environments across platforms
- **Scalability**: Easy horizontal scaling
- **Developer Experience**: Simplified development workflow

### Tailwind over Bootstrap/Material-UI
- **Utility-First**: Rapid UI development without custom CSS
- **Bundle Size**: Only includes used styles
- **Customization**: Highly configurable design system
- **Performance**: No JavaScript framework overhead

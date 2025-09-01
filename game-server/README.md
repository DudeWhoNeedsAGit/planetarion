# 🌌 Planetarion Game Server

A complete full-stack space strategy game inspired by classic browser-based games like OGame and Ikariam. This monorepo contains a Flask backend API, React frontend with Tailwind CSS, PostgreSQL database, and comprehensive game mechanics including resource management, fleet operations, and real-time updates.

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [API Documentation](#-api-documentation)
- [Database Schema](#-database-schema)
- [Frontend Components](#-frontend-components)
- [Testing](#-testing)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

## 🎯 Project Overview

Planetarion is a real-time space strategy game where players:
- **Colonize Planets**: Expand their empire across the galaxy
- **Manage Resources**: Mine metal, crystal, and deuterium
- **Build Structures**: Upgrade mines, power plants, and research facilities
- **Command Fleets**: Send ships for transport, attack, or exploration
- **Research Technology**: Unlock advanced capabilities
- **Form Alliances**: Cooperate with other players

The game features automatic resource generation, fleet movement calculations, and a comprehensive economy system.

## 🏗️ Architecture

```
planetarion/
├── backend/                 # Flask API Server
│   ├── app.py              # Main Flask application
│   ├── models.py           # SQLAlchemy database models
│   ├── database.py         # Database connection and session management
│   ├── routes/             # API route handlers
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── users.py        # User management
│   │   ├── planets.py      # Basic planet CRUD (admin/public)
│   │   ├── planet_user.py  # User-authenticated planet operations
│   │   ├── fleet.py        # Fleet management and operations
│   │   └── shipyard.py     # Ship building and construction
│   ├── services/           # Business logic
│   │   └── tick.py         # Resource generation system
│   ├── instance/           # SQLite test database storage
│   ├── scripts/            # Utility scripts for development
│   ├── .env               # Environment variables
│   └── requirements.txt    # Python dependencies
├── frontend/               # React Application
│   ├── src/
│   │   ├── App.js          # Main application component
│   │   ├── Dashboard.js    # Main game interface
│   │   ├── Login.js        # Authentication component
│   │   ├── Register.js     # User registration
│   │   ├── Overview.js     # Empire overview
│   │   ├── FleetManagement.js # Fleet operations
│   │   └── Navigation.js   # Navigation component
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── database/               # Database migrations
├── docker-compose.yml      # Container orchestration
├── test_system.py         # Comprehensive test suite
└── README.md              # This file
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 2.3.3 with Flask-RESTful
- **Database**: SQLite with SQLAlchemy ORM (development) / PostgreSQL (production)
- **Authentication**: JWT (JSON Web Tokens)
- **Migrations**: Flask-Migrate
- **Scheduling**: APScheduler for automated tasks
- **CORS**: Flask-CORS for cross-origin requests

### Frontend
- **Framework**: React 18.2.0 with Hooks
- **Styling**: Tailwind CSS 3.3.3
- **HTTP Client**: Axios 1.4.0
- **Routing**: React Router (hash-based)
- **Build Tool**: Create React App
- **Serving**: Static files served by Flask backend

### Infrastructure
- **Containerization**: Docker & Docker Compose (optional)
- **Database**: SQLite (automatic setup) / PostgreSQL (production)
- **Reverse Proxy**: Nginx (for production)
- **Process Manager**: PM2 (for production)
- **Static File Serving**: Flask handles React build files

### Development Tools
- **Testing**: Python unittest, React Testing Library
- **Linting**: ESLint, Prettier
- **Version Control**: Git with conventional commits
- **Documentation**: Markdown with API docs

## ✨ Features

### Core Gameplay
- ✅ **User Authentication**: JWT-based login/registration
- ✅ **Planet Management**: Multiple planet colonization
- ✅ **Resource System**: Metal, Crystal, Deuterium mining
- ✅ **Building Upgrades**: Mines, power plants, research labs
- ✅ **Fleet Operations**: Ship construction and movement
- ✅ **Real-time Updates**: Automatic resource generation every 5 seconds
- ✅ **Tick System**: High-frequency resource production (5-second intervals)

### User Interface
- ✅ **Responsive Design**: Works on desktop and mobile
- ✅ **Dark Theme**: Space-themed UI with custom colors
- ✅ **Interactive Dashboard**: Planet selection and management
- ✅ **Fleet Management**: Create, send, and recall fleets
- ✅ **Navigation System**: Section-based routing
- ✅ **Real-time Feedback**: Loading states and error handling

### Technical Features
- ✅ **RESTful API**: Complete CRUD operations
- ✅ **Database Persistence**: PostgreSQL with migrations
- ✅ **Containerization**: Docker Compose setup
- ✅ **Automated Testing**: Comprehensive test suite
- ✅ **Error Handling**: Graceful failure management
- ✅ **Security**: Input validation and sanitization

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ with pip
- Node.js 18+ with npm (optional, for frontend development)
- Git

### One-Command Setup
```bash
git clone https://github.com/DudeWhoNeedsAGit/planetarion.git
cd planetarion/game-server/backend
pip install -r requirements.txt
python app.py
```

### Access Points
- **Full Game**: http://localhost:5001 (login + dashboard)
- **Backend API**: http://localhost:5001/api/*
- **Database**: SQLite (automatic setup)

### Alternative: Development Setup
```bash
# Backend
cd game-server/backend
pip install -r requirements.txt
python app.py

# Frontend (optional, in separate terminal)
cd game-server/frontend
npm install
npm run build
```

## 📦 Installation

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/DudeWhoNeedsAGit/planetarion.git
   cd planetarion/game-server
   ```

2. **Start all services**
   ```bash
   docker compose up --build -d
   ```

3. **Check service status**
   ```bash
   docker compose ps
   ```

4. **View logs**
   ```bash
   docker compose logs -f
   ```

### Option 2: Local Development

#### Backend Setup
```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://planetarion_user:planetarion_password@localhost:5432/planetarion
export FLASK_ENV=development
export SECRET_KEY=your-secret-key-here

# Run the application
python app.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### Database Setup
```bash
# Create database
createdb planetarion
createuser planetarion_user
psql -c "ALTER USER planetarion_user PASSWORD 'planetarion_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE planetarion TO planetarion_user;"

# Run migrations
cd backend
flask db upgrade
```

## 📁 Project Structure

```
game-server/
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── models.py           # SQLAlchemy database models
│   ├── routes/             # API route handlers
│   │   ├── users.py        # User management endpoints
│   │   └── planets.py      # Planet management endpoints
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container config
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   ├── index.js        # React entry point
│   │   └── index.css       # Global styles with Tailwind
│   ├── public/
│   │   └── index.html      # HTML template
│   ├── package.json        # Node.js dependencies
│   ├── tailwind.config.js  # Tailwind CSS configuration
│   └── Dockerfile          # Frontend container config
├── database/               # Database migrations and schema
├── docker-compose.yml      # Container orchestration
└── README.md              # This file
```

## 🔧 Development

### Running Individual Services

**Backend Only:**
```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql://planetarion_user:planetarion_password@localhost:5432/planetarion
python app.py
```

**Frontend Only:**
```bash
cd frontend
npm install
npm start
```

### Database Management

**Create and run migrations:**
```bash
docker-compose exec backend flask db init
docker-compose exec backend flask db migrate
docker-compose exec backend flask db upgrade
```

**Access database directly:**
```bash
docker-compose exec db psql -U planetarion_user -d planetarion
```

## 📡 API Documentation

### Authentication Endpoints

#### POST `/api/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string"
  }
}
```

#### POST `/api/auth/login`
Authenticate an existing user.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string"
  }
}
```

#### GET `/api/auth/me`
Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Planet Management Endpoints

#### GET `/api/planet`
Get all planets belonging to the authenticated user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Home Planet",
    "coordinates": "1:1:1",
    "resources": {
      "metal": 1000,
      "crystal": 500,
      "deuterium": 0
    },
    "structures": {
      "metal_mine": 1,
      "crystal_mine": 1,
      "deuterium_synthesizer": 0,
      "solar_plant": 1,
      "fusion_reactor": 0
    },
    "production_rates": {
      "metal_per_hour": 30,
      "crystal_per_hour": 20,
      "deuterium_per_hour": 0
    }
  }
]
```

#### PUT `/api/planet/buildings`
Upgrade buildings on a planet.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "planet_id": 1,
  "buildings": {
    "metal_mine": 2,
    "crystal_mine": 2
  }
}
```

**Response:**
```json
{
  "resources": {
    "metal": 800,
    "crystal": 400,
    "deuterium": 0
  },
  "structures": {
    "metal_mine": 2,
    "crystal_mine": 2,
    "deuterium_synthesizer": 0,
    "solar_plant": 1,
    "fusion_reactor": 0
  }
}
```

### Fleet Management Endpoints

#### GET `/api/fleet`
Get all fleets belonging to the authenticated user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "mission": "attack",
    "status": "stationed",
    "start_planet_id": 1,
    "target_planet_id": 2,
    "ships": {
      "small_cargo": 5,
      "light_fighter": 3,
      "heavy_fighter": 0,
      "cruiser": 0,
      "battleship": 0
    },
    "departure_time": null,
    "arrival_time": null
  }
]
```

#### POST `/api/fleet`
Create a new fleet.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "start_planet_id": 1,
  "ships": {
    "small_cargo": 10,
    "light_fighter": 5
  }
}
```

**Response:**
```json
{
  "fleet": {
    "id": 2,
    "mission": null,
    "status": "stationed",
    "start_planet_id": 1,
    "target_planet_id": null,
    "ships": {
      "small_cargo": 10,
      "light_fighter": 5,
      "heavy_fighter": 0,
      "cruiser": 0,
      "battleship": 0
    }
  }
}
```

#### POST `/api/fleet/send`
Send an existing fleet on a mission.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "fleet_id": 2,
  "target_planet_id": 3,
  "mission": "attack"
}
```

**Response:**
```json
{
  "fleet": {
    "id": 2,
    "mission": "attack",
    "status": "traveling",
    "start_planet_id": 1,
    "target_planet_id": 3,
    "departure_time": "2025-01-01T12:00:00Z",
    "arrival_time": "2025-01-01T12:30:00Z"
  }
}
```

#### POST `/api/fleet/recall/{fleet_id}`
Recall a traveling fleet.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "fleet": {
    "id": 2,
    "mission": "attack",
    "status": "returning",
    "arrival_time": "2025-01-01T12:45:00Z"
  }
}
```

### System Endpoints

#### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

#### POST `/api/tick`
Manually trigger a game tick (resource generation).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "changes": [
    {
      "planet_id": 1,
      "resource_changes": {
        "metal": 30,
        "crystal": 20,
        "deuterium": 0
      }
    }
  ]
}
```

## 🎨 Frontend Features

- **Responsive Design**: Works on desktop and mobile
- **Real-time Data**: Fetches live data from the backend
- **Space Theme**: Dark theme with space-inspired colors
- **Resource Display**: Shows metal, crystal, and deuterium for each planet

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

**Fields:**
- `id` (Primary Key, Auto-increment)
- `username` (Unique, 80 chars max)
- `email` (Unique, 120 chars max)
- `password_hash` (128 chars max)
- `created_at` (Timestamp, auto-generated)
- `last_login` (Timestamp, nullable)

### Planets Table
```sql
CREATE TABLE planets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    z INTEGER NOT NULL,
    user_id INTEGER REFERENCES users(id),
    -- Resources
    metal BIGINT DEFAULT 1000,
    crystal BIGINT DEFAULT 500,
    deuterium BIGINT DEFAULT 0,
    -- Structures
    metal_mine INTEGER DEFAULT 1,
    crystal_mine INTEGER DEFAULT 1,
    deuterium_synthesizer INTEGER DEFAULT 0,
    solar_plant INTEGER DEFAULT 1,
    fusion_reactor INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id` (Primary Key, Auto-increment)
- `name` (100 chars max)
- `x, y, z` (Coordinates, integers)
- `user_id` (Foreign Key to users table)
- **Resources:**
  - `metal` (BigInteger, default 1000)
  - `crystal` (BigInteger, default 500)
  - `deuterium` (BigInteger, default 0)
- **Structures:**
  - `metal_mine` (Integer, default 1)
  - `crystal_mine` (Integer, default 1)
  - `deuterium_synthesizer` (Integer, default 0)
  - `solar_plant` (Integer, default 1)
  - `fusion_reactor` (Integer, default 0)
- `created_at` (Timestamp, auto-generated)

### Fleets Table
```sql
CREATE TABLE fleets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    mission VARCHAR(50),
    start_planet_id INTEGER REFERENCES planets(id),
    target_planet_id INTEGER REFERENCES planets(id),
    -- Ships
    small_cargo INTEGER DEFAULT 0,
    large_cargo INTEGER DEFAULT 0,
    light_fighter INTEGER DEFAULT 0,
    heavy_fighter INTEGER DEFAULT 0,
    cruiser INTEGER DEFAULT 0,
    battleship INTEGER DEFAULT 0,
    -- Timing
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP
);
```

**Fields:**
- `id` (Primary Key, Auto-increment)
- `user_id` (Foreign Key to users table)
- `mission` (50 chars max: 'attack', 'transport', 'deploy', etc.)
- `start_planet_id` (Foreign Key to planets table)
- `target_planet_id` (Foreign Key to planets table)
- **Ships:**
  - `small_cargo` (Integer, default 0)
  - `large_cargo` (Integer, default 0)
  - `light_fighter` (Integer, default 0)
  - `heavy_fighter` (Integer, default 0)
  - `cruiser` (Integer, default 0)
  - `battleship` (Integer, default 0)
- **Timing:**
  - `departure_time` (Timestamp, nullable)
  - `arrival_time` (Timestamp, nullable)

### TickLog Table (Future Enhancement)
```sql
CREATE TABLE tick_logs (
    id SERIAL PRIMARY KEY,
    planet_id INTEGER REFERENCES planets(id),
    tick_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metal_change BIGINT DEFAULT 0,
    crystal_change BIGINT DEFAULT 0,
    deuterium_change BIGINT DEFAULT 0
);
```

### Alliances Table (Future Enhancement)
```sql
CREATE TABLE alliances (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    tag VARCHAR(10) UNIQUE NOT NULL,
    founder_id INTEGER REFERENCES users(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🖥️ Frontend Components

### Core Components

#### App.js
**Purpose:** Main application component handling routing and authentication state
**Key Features:**
- JWT token management
- Route protection
- Hash-based navigation
- Global state management

**State Management:**
```javascript
const [user, setUser] = useState(null);
const [currentView, setCurrentView] = useState('dashboard');
const [loading, setLoading] = useState(true);
```

#### Dashboard.js
**Purpose:** Main game interface with section-based navigation
**Key Features:**
- Planet management
- Building upgrades
- Resource display
- Section routing (Overview, Planets, Fleets, etc.)

**Sections:**
- Overview: Empire statistics and quick stats
- Planets: Planet selection and building management
- Fleets: Fleet creation and mission control
- Research: Technology tree (placeholder)
- Alliance: Diplomacy features (placeholder)
- Messages: Communication system (placeholder)

#### Login.js & Register.js
**Purpose:** User authentication components
**Features:**
- Form validation
- JWT token handling
- Error display
- Redirect after successful auth

### Specialized Components

#### Overview.js
**Purpose:** Empire overview and statistics dashboard
**Displays:**
- Total planets, resources, and production
- Resource breakdown by type
- Recent activity feed
- Quick action buttons

#### FleetManagement.js
**Purpose:** Complete fleet operations interface
**Features:**
- Fleet creation with ship selection
- Fleet sending with mission types
- Fleet recall functionality
- Real-time ETA countdown
- Ship composition display

#### Navigation.js
**Purpose:** Section-based navigation component
**Features:**
- Tab-based navigation
- Active section highlighting
- Responsive design
- Icon integration

### Utility Components

#### Modal Components
- `CreateFleetModal`: Fleet creation form
- `SendFleetModal`: Fleet mission assignment
- Various confirmation dialogs

### Styling & Theming

#### Tailwind Configuration
```javascript
// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        'space-dark': '#0a0a0a',
        'space-blue': '#1e3a8a',
        'metal': '#64748b',
        'crystal': '#06b6d4',
        'deuterium': '#8b5cf6',
      },
    },
  },
  plugins: [],
}
```

#### Custom Color Scheme
- **Space Dark** (`#0a0a0a`): Primary background
- **Space Blue** (`#1e3a8a`): Headers and navigation
- **Metal** (`#64748b`): Resource displays
- **Crystal** (`#06b6d4`): Interactive elements
- **Deuterium** (`#8b5cf6`): Special features

### Component Architecture

#### State Management
- Local component state with React hooks
- Props drilling for parent-child communication
- Axios for API communication
- JWT token persistence in localStorage

#### Error Handling
- Try-catch blocks for API calls
- User-friendly error messages
- Loading states for async operations
- Graceful fallbacks for failed requests

#### Performance Optimizations
- React.memo for expensive re-renders
- useCallback for event handlers
- useMemo for computed values
- Lazy loading for large components

## 🔒 Security Notes

- This is a development setup with default credentials
- Passwords are stored as plain text (implement proper hashing for production)
- CORS is enabled for development (restrict in production)
- Database credentials are in plain text (use environment variables)

## 🚦 Troubleshooting

### Common Issues

**Port conflicts:**
- Ensure ports 3000, 5000, and 5432 are available
- Check `docker ps` for running containers

**Database connection issues:**
- Wait for database health check to pass
- Check logs: `docker-compose logs db`

**Frontend can't connect to backend:**
- Ensure backend is running and healthy
- Check CORS settings in Flask app

### Logs

**View all logs:**
```bash
docker-compose logs
```

**View specific service logs:**
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

## 🔄 Updates and Maintenance

**Rebuild after code changes:**
```bash
docker-compose up --build
```

**Clean restart:**
```bash
docker-compose down
docker-compose up --build
```

**Update dependencies:**
```bash
# Backend
cd backend && pip freeze > requirements.txt

# Frontend
cd frontend && npm update
```

## 🧪 Testing

### Automated Test Suite

The project includes a comprehensive test suite (`test_system.py`) that validates all major functionality:

#### Running Tests
```bash
# Run all tests
python test_system.py

# Run specific test category
python -c "from test_system import PlanetarionTester; t = PlanetarionTester(); t.test_health_check()"

# Run with verbose output
python test_system.py --verbose
```

#### Test Coverage
- ✅ **Health Check**: API availability validation
- ✅ **User Registration**: Account creation flow
- ✅ **User Login**: Authentication verification
- ✅ **User Profile**: Data retrieval testing
- ✅ **Planet Management**: CRUD operations for planets
- ✅ **Building Upgrades**: Resource validation and structure updates
- ✅ **Fleet Operations**: Creation, sending, and recall functionality
- ✅ **Tick System**: Resource generation verification

#### Test Architecture
```python
class PlanetarionTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user = None
        self.planets = []
        self.fleets = []

    def test_health_check(self):
        """Test basic health check endpoint"""
        # Implementation...

    def test_user_registration(self):
        """Test user registration"""
        # Implementation...

    # ... additional test methods
```

### Manual Testing

#### API Testing with cURL
```bash
# Health check
curl http://localhost:5000/health

# User registration
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass"}'

# Get planets (requires auth)
curl -X GET http://localhost:5000/api/planet \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Frontend Testing
```bash
# Start frontend in development mode
cd frontend
npm start

# Build for production
npm run build

# Run tests
npm test
```

#### Database Testing
```bash
# Access database directly
docker compose exec db psql -U planetarion_user -d planetarion

# Check table contents
SELECT * FROM users;
SELECT * FROM planets;
SELECT * FROM fleets;
```

## 💻 Development

### Code Organization

#### Backend Structure
```
backend/
├── app.py                 # Main Flask application
├── models.py             # SQLAlchemy database models
├── routes/               # API route handlers
│   ├── auth.py          # Authentication endpoints
│   ├── planets.py       # Planet management
│   ├── fleets.py        # Fleet operations
│   └── __init__.py      # Package initialization
├── services/            # Business logic
│   └── tick.py          # Resource generation
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── .env                # Environment variables
```

#### Frontend Structure
```
frontend/
├── src/
│   ├── App.js              # Main application
│   ├── Dashboard.js        # Game interface
│   ├── Login.js           # Authentication
│   ├── Register.js        # User registration
│   ├── Overview.js        # Empire overview
│   ├── FleetManagement.js # Fleet operations
│   ├── Navigation.js      # Navigation component
│   └── index.js           # React entry point
├── public/
│   └── index.html         # HTML template
├── package.json          # Node.js dependencies
├── tailwind.config.js    # Tailwind configuration
└── Dockerfile            # Container config
```

### Development Workflow

#### Setting Up Development Environment
```bash
# Clone repository
git clone https://github.com/DudeWhoNeedsAGit/planetarion.git
cd planetarion/game-server

# Start all services
docker compose up --build -d

# Check logs
docker compose logs -f
```

#### Making Code Changes

1. **Backend Changes**
   ```bash
   # Modify backend code
   vim backend/app.py

   # Restart backend service
   docker compose restart backend

   # Check logs
   docker compose logs backend
   ```

2. **Frontend Changes**
   ```bash
   # Modify frontend code
   vim frontend/src/App.js

   # Frontend auto-reloads with hot module replacement
   # No restart needed for development
   ```

3. **Database Changes**
   ```bash
   # Modify models
   vim backend/models.py

   # Create migration
   docker compose exec backend flask db migrate -m "Add new field"

   # Apply migration
   docker compose exec backend flask db upgrade
   ```

#### Adding New Features

1. **New API Endpoint**
   ```python
   # backend/routes/example.py
   from flask import Blueprint, request, jsonify
   from app import db
   from models import ExampleModel

   example_bp = Blueprint('example', __name__)

   @example_bp.route('/api/example', methods=['GET'])
   def get_examples():
       examples = ExampleModel.query.all()
       return jsonify([e.to_dict() for e in examples])
   ```

2. **New React Component**
   ```javascript
   // frontend/src/ExampleComponent.js
   import React, { useState, useEffect } from 'react';
   import axios from 'axios';

   function ExampleComponent() {
     const [data, setData] = useState([]);

     useEffect(() => {
       fetchData();
     }, []);

     const fetchData = async () => {
       try {
         const response = await axios.get('/api/example');
         setData(response.data);
       } catch (error) {
         console.error('Error fetching data:', error);
       }
     };

     return (
       <div className="bg-gray-800 rounded-lg p-6">
         <h3 className="text-xl font-bold mb-4 text-white">Example Component</h3>
         {/* Component content */}
       </div>
     );
   }

   export default ExampleComponent;
   ```

### Environment Variables

#### Backend Environment
```bash
# .env file
DATABASE_URL=postgresql://planetarion_user:planetarion_password@db:5432/planetarion
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
```

#### Frontend Environment
```bash
# .env file
REACT_APP_API_URL=http://localhost:5000
REACT_APP_DEBUG=true
```

### Debugging

#### Backend Debugging
```bash
# View backend logs
docker compose logs backend -f

# Access backend container
docker compose exec backend bash

# Debug with Python debugger
docker compose exec backend python -m pdb app.py
```

#### Frontend Debugging
```bash
# View browser console
# Open Developer Tools in browser

# Check network requests
# Use Network tab in Developer Tools

# Debug React components
# Use React Developer Tools extension
```

#### Database Debugging
```bash
# Access database
docker compose exec db psql -U planetarion_user -d planetarion

# View table structure
\d users;
\d planets;
\d fleets;

# Query data
SELECT * FROM users;
SELECT COUNT(*) FROM planets;
```

### Performance Monitoring

#### System Resources
```bash
# Monitor Docker containers
docker stats

# Check disk usage
docker system df

# View container logs
docker compose logs --tail=100
```

#### Application Metrics
```python
# Add to backend for monitoring
from flask import Flask
import psutil
import time

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'uptime': time.time() - psutil.boot_time()
    }
```

## 🚀 Deployment

### Production Deployment

#### Docker Compose Production
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: planetarion
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - planetarion

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/planetarion
      FLASK_ENV: production
      SECRET_KEY: ${SECRET_KEY}
    networks:
      - planetarion

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    networks:
      - planetarion

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
      - frontend
    networks:
      - planetarion

volumes:
  postgres_data:

networks:
  planetarion:
    driver: bridge
```

#### Environment Variables for Production
```bash
# .env.prod
DB_USER=planetarion_prod
DB_PASSWORD=secure_password_here
SECRET_KEY=production_secret_key
JWT_SECRET_KEY=production_jwt_secret
DOMAIN=yourdomain.com
SSL_CERT_PATH=/path/to/ssl/cert
```

### Scaling Considerations

#### Horizontal Scaling
```yaml
# Multiple backend instances
services:
  backend:
    build: ./backend
    deploy:
      replicas: 3
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/planetarion

  loadbalancer:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx-loadbalancer.conf:/etc/nginx/nginx.conf
```

#### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_planets_user_id ON planets(user_id);
CREATE INDEX idx_fleets_user_id ON fleets(user_id);
CREATE INDEX idx_fleets_status ON fleets(status);

-- Partition large tables by date
CREATE TABLE tick_logs_y2025 PARTITION OF tick_logs
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### Backup Strategy
```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
docker compose exec db pg_dump -U planetarion_user planetarion > $BACKUP_DIR/planetarion_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/planetarion_$DATE.sql

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "planetarion_*.sql.gz" -mtime +7 -delete
```

## 📈 Future Enhancements

### Phase 1: Core Features
- [ ] **Password Hashing**: Implement bcrypt for secure password storage
- [ ] **Email Verification**: User email verification system
- [ ] **Password Reset**: Forgot password functionality
- [ ] **User Profiles**: Extended user profile management

### Phase 2: Advanced Gameplay
- [ ] **Combat System**: Fleet vs fleet combat mechanics
- [ ] **Research Tree**: Technology research and advancement
- [ ] **Ship Building**: Shipyard construction system
- [ ] **Defense Systems**: Planetary defense structures

### Phase 3: Social Features
- [ ] **Alliance System**: Player alliances and diplomacy
- [ ] **Messaging System**: Private and alliance messaging
- [ ] **High Scores**: Leaderboards and rankings
- [ ] **Trade System**: Resource trading between players

### Phase 4: Technical Improvements
- [ ] **Real-time Updates**: WebSocket integration for live updates
- [ ] **Caching Layer**: Redis for performance optimization
- [ ] **API Rate Limiting**: Prevent abuse and ensure fair usage
- [ ] **Monitoring**: Application performance monitoring

### Phase 5: Advanced Features
- [ ] **Galaxy Map**: Interactive galaxy visualization
- [ ] **Espionage System**: Spy probes and intelligence gathering
- [ ] **Admin Panel**: Game administration interface
- [ ] **Mobile App**: React Native mobile application

## 🤝 Contributing

### Development Process
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards
```python
# Python: PEP 8 compliant
def function_name(param1: str, param2: int) -> dict:
    """Function docstring describing purpose and parameters."""
    return {"result": param1 * param2}
```

```javascript
// JavaScript: Airbnb style guide
const functionName = (param1, param2) => {
  // Function body
  return { result: param1 * param2 };
};
```

### Testing Requirements
- All new features must include unit tests
- Integration tests for API endpoints
- Frontend component tests for React components
- Minimum 80% code coverage required

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ❓ Questions for ChatGPT

When asking ChatGPT about this project, you can reference:

1. **"How does the JWT authentication work in this Flask-React app?"**
2. **"Explain the database relationships between users, planets, and fleets"**
3. **"How is the resource generation system implemented?"**
4. **"What would be the best way to add a combat system to this game?"**
5. **"How can I optimize the database queries for better performance?"**
6. **"What security improvements should I implement for production?"**
7. **"How would you add real-time updates using WebSockets?"**
8. **"What's the best way to implement the research tree system?"**

---

**Happy gaming! 🚀**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `docker-compose up`
5. Submit a pull request

## 📄 License

This project is for educational purposes. See individual component licenses for details.

---

**Happy gaming! 🚀**

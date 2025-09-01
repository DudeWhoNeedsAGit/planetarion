# 🌌 Planetarion Game Server

A complete monorepo setup for a space strategy game inspired by classic browser-based games. This project includes a Flask backend API, React frontend with Tailwind CSS, and PostgreSQL database, all containerized with Docker Compose.

## 🏗️ Architecture

- **Backend**: Flask API with SQLAlchemy ORM and Flask-Migrate
- **Frontend**: React application with Tailwind CSS styling
- **Database**: PostgreSQL with persistent data storage
- **Containerization**: Docker Compose for easy development and deployment

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.11+ (for local backend development)
- Node.js 18+ (for local frontend development)
- PostgreSQL (for local database)
- Git

### Installation & Setup

#### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd planetarion/game-server
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Database: localhost:5432

#### Option 2: Local Development

1. **Set up PostgreSQL database**
   ```bash
   # Create database and user
   createdb planetarion
   createuser planetarion_user
   psql -c "ALTER USER planetarion_user PASSWORD 'planetarion_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE planetarion TO planetarion_user;"
   ```

2. **Setup backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   export DATABASE_URL=postgresql://planetarion_user:planetarion_password@localhost:5432/planetarion
   python app.py
   ```

3. **Setup frontend (in new terminal)**
   ```bash
   cd frontend
   npm install
   npm start
   ```

### First Time Setup

The database will be automatically initialized when you first run the application. The Flask-Migrate will create all necessary tables.

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

## 📡 API Endpoints

### Users
- `GET /users` - List all users
- `GET /users/<id>` - Get specific user
- `POST /users` - Create new user

### Planets
- `GET /planets` - List all planets
- `GET /planets/<id>` - Get specific planet
- `POST /planets` - Create new planet

### Health Check
- `GET /health` - Service health status

## 🎨 Frontend Features

- **Responsive Design**: Works on desktop and mobile
- **Real-time Data**: Fetches live data from the backend
- **Space Theme**: Dark theme with space-inspired colors
- **Resource Display**: Shows metal, crystal, and deuterium for each planet

## 🗄️ Database Schema

### Users Table
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `password_hash`
- `created_at`
- `last_login`

### Planets Table
- `id` (Primary Key)
- `name`
- `x, y, z` (Coordinates)
- `user_id` (Foreign Key)
- Resources: `metal`, `crystal`, `deuterium`
- Structures: mines, synthesizers, plants, reactors

### Fleets Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `mission` (attack, transport, etc.)
- `start_planet_id`, `target_planet_id`
- Ship counts and timing

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

## 📈 Future Enhancements

- [ ] User authentication and sessions
- [ ] Real-time game ticks and resource production
- [ ] Fleet movement and combat system
- [ ] Galaxy map visualization
- [ ] Research and technology trees
- [ ] Alliance and diplomacy features
- [ ] Admin panel for game management

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

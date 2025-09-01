# Task 01 – Scaffold Project

Create a monorepo with the following structure:
game-server/
├── backend/ # Flask app
│ ├── app.py
│ ├── models.py
│ ├── routes/
│ └── services/
├── frontend/ # React + Tailwind
│ └── src/
├── database/ # migrations, schema
├── docker-compose.yml
└── README.md

Requirements:
- Backend: Flask, SQLAlchemy, Flask-Migrate
- Frontend: React with Tailwind
- Database: Postgres (via docker-compose)
- Ensure containers can run together via `docker-compose up`
- Provide a README with setup instructions
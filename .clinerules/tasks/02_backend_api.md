# Task 02 – Backend API

Implement backend REST API endpoints:

- `/api/auth`
  - POST `/register`
  - POST `/login`
- `/api/planet`
  - GET planet state (resources, buildings)
- `/api/fleet`
  - POST create fleet
  - POST send fleet
  - POST recall fleet
- `/api/tick`
  - POST trigger tick manually (admin/debug only)

Use SQLAlchemy models:
- User (id, username, password hash)
- Planet (id, user_id, resources, buildings placeholder)
- Fleet (id, planet_id, ships, status, target_planet_id, eta)
- Alliance (id, name, members placeholder)
- TickLog (id, tick_number, timestamp)

Include authentication (JWT or session-based).
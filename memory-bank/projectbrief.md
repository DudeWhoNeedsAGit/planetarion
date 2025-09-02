# Project Brief

## Overview
Planetarion is a multiplayer tick-based strategy web game inspired by classic browser-based games like OGame and Ikariam. This monorepo contains a Flask backend API, React frontend with Tailwind CSS, PostgreSQL database, and comprehensive game mechanics.

## Core Concept
Players colonize planets, manage resources (metal, crystal, deuterium), build structures, command fleets, and compete in a persistent universe with automatic resource generation every 5 seconds.

## Technology Stack
- **Backend**: Flask 2.3.3 + SQLAlchemy + JWT authentication
- **Frontend**: React 18.2.0 + Tailwind CSS + Axios
- **Database**: PostgreSQL (production) / SQLite (development)
- **Infrastructure**: Docker Compose + APScheduler + Playwright testing

## Key Features
- Real-time resource generation with tick-based economy
- Fleet operations (creation, movement, combat placeholder)
- Building upgrades and technology research
- User authentication and planet management
- Responsive web interface with space-themed UI

## Current Status
- Backend API fully implemented with all core endpoints
- Frontend React application with complete UI components
- Database schema with all required models
- Docker containerization for development and testing
- Comprehensive test suite (backend and E2E)

## Development Focus
- Keep combat logic stubbed for scaffolding and API contracts
- Prioritize core gameplay loop: resource generation → building upgrades → fleet operations
- Maintain clean, modular code structure across backend and frontend
- Ensure comprehensive test coverage for all implemented features

## Future Enhancements
- Combat system implementation
- Alliance and messaging features
- Advanced research tree
- Real-time WebSocket updates
- Mobile application development

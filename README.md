# 🌌 Planetarion

**A Space Strategy Game Built with Modern Web Technologies**

Planetarion is a real-time multiplayer space strategy game where you build your interstellar empire, manage resources, command fleets, and conquer the galaxy. Inspired by classic browser-based strategy games, it combines economic management, fleet combat, and territorial expansion in a vast universe.

## 🎮 What is Planetarion?

Imagine commanding a space empire where every decision matters:

- **🏭 Build & Expand**: Construct mines, power plants, and research facilities on your planets
- **🚀 Command Fleets**: Build warships, cargo vessels, and exploration ships
- **⚔️ Strategic Combat**: Send fleets to attack enemies or defend your territory
- **📈 Resource Management**: Mine metal, crystal, and deuterium to fuel your empire
- **🤝 Diplomacy**: Form alliances, negotiate trades, and build galactic relationships
- **🔬 Research**: Unlock advanced technologies to gain strategic advantages

## 🚀 Quick Start

Getting started is simple - just follow these steps:

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- At least 4GB of RAM
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/DudeWhoNeedsAGit/planetarion.git
   cd planetarion
   ```

2. **Start the game**
   ```bash
   cd game-server
   docker compose up --build
   ```

3. **Open your browser**
   - Visit **http://localhost:3000** to start playing!
   - The backend API runs on **http://localhost:5000**
   - Database is available on **localhost:5432**

That's it! The game will automatically set up the database and start all services.

## 🎯 Game Features

### Core Gameplay
- ✅ **Planet Colonization**: Expand your empire across the galaxy
- ✅ **Resource Mining**: Metal, crystal, and deuterium extraction
- ✅ **Building Construction**: Upgrade mines, power plants, and research labs
- ✅ **Fleet Management**: Build and command space fleets
- ✅ **Real-time Economy**: Resources generate automatically over time
- ✅ **Strategic Combat**: Fleet vs fleet battles

### User Experience
- ✅ **Modern Web Interface**: Clean, responsive design that works on any device
- ✅ **Real-time Updates**: Live resource counters and fleet movements
- ✅ **Intuitive Controls**: Easy-to-use interface for all game mechanics
- ✅ **Dark Space Theme**: Immersive sci-fi aesthetic
- ✅ **Progress Tracking**: Detailed statistics and empire overview

## 📖 Documentation

For detailed information about the game, development, and technical implementation:

- **[📚 Complete Documentation](./game-server/README.md)** - Everything you need to know
- **[🧪 Testing Guide](./game-server/README.md#testing)** - How to test the game
- **[💻 Development](./game-server/README.md#development)** - Contributing to the project
- **[🚀 Deployment](./game-server/README.md#deployment)** - Production setup

## 🎮 How to Play

### Getting Started
1. **Register an Account**: Create your username and password
2. **Choose Your Home Planet**: Start with your first colony
3. **Build Your Empire**: Construct mines to generate resources
4. **Expand**: Colonize new planets and build more structures
5. **Command Fleets**: Build ships and explore the galaxy
6. **Grow Your Power**: Research technologies and form alliances

### Basic Strategy
- **Resource Management**: Balance metal, crystal, and deuterium production
- **Economic Growth**: Upgrade mines regularly to increase resource output
- **Fleet Building**: Invest in a balanced fleet for defense and expansion
- **Timing**: Use the automatic tick system to your advantage
- **Diplomacy**: Build relationships with other players

## 🛠️ Technology

Planetarion is built with modern web technologies:

- **Frontend**: React with Tailwind CSS for a beautiful, responsive interface
- **Backend**: Flask API with JWT authentication and real-time processing
- **Database**: PostgreSQL for reliable data storage and complex queries
- **Infrastructure**: Docker containers for easy deployment and scaling
- **Real-time**: Automatic resource generation and fleet movement calculations

## 🌟 Why Planetarion?

### For Players
- **Free to Play**: No subscriptions or microtransactions
- **Strategic Depth**: Complex economy and military systems
- **Community**: Play with friends and build alliances
- **Progression**: Long-term empire building with meaningful advancement
- **Fair Competition**: Balanced gameplay mechanics

### For Developers
- **Open Source**: Learn from and contribute to the codebase
- **Modern Stack**: Current web development technologies
- **Well Documented**: Comprehensive guides and API documentation
- **Scalable Architecture**: Built for growth and new features
- **Educational**: Great project for learning full-stack development

## 🤝 Community & Support

- **Issues & Bugs**: [Report on GitHub](https://github.com/DudeWhoNeedsAGit/planetarion/issues)
- **Feature Requests**: [Suggest improvements](https://github.com/DudeWhoNeedsAGit/planetarion/issues)
- **Contributing**: See our [development guide](./game-server/README.md#contributing)
- **Discussions**: Join the conversation on GitHub

## 🗺️ Roadmap

### Currently Available
- ✅ User registration and authentication
- ✅ Planet management and resource mining
- ✅ Building construction and upgrades
- ✅ Fleet creation and basic operations
- ✅ Real-time resource generation
- ✅ Responsive web interface

### Coming Soon
- 🔄 **Combat System**: Fleet vs fleet battles
- 🔄 **Research Tree**: Technology advancement
- 🔄 **Alliance System**: Player diplomacy
- 🔄 **Messaging**: Private and alliance communication
- 🔄 **Galaxy Map**: Interactive universe visualization
- 🔄 **Mobile App**: React Native companion

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🎉 Ready to Conquer the Stars?

**Start your journey to galactic domination today!**

```bash
git clone https://github.com/DudeWhoNeedsAGit/planetarion.git
cd planetarion/game-server
docker compose up --build
```

Then visit **http://localhost:3000** and begin building your empire!

---

*Planetarion - Where Strategy Meets the Stars* 🌌

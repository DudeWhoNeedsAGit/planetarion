from flask import Flask, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
from dotenv import load_dotenv
import bcrypt
import atexit

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=None)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'] = 60  # 1 hour

# Initialize extensions
from database import db, migrate
db.init_app(app)
migrate.init_app(app, db)
CORS(app)
jwt = JWTManager(app)

# Initialize scheduler
scheduler = BackgroundScheduler()

# Import models
from models import User, Planet, Fleet, Alliance, TickLog

# HTML template for the login page
LOGIN_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Planetarion - Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .space-bg {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        }
        .glow {
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        }
        .star {
            position: absolute;
            background: white;
            border-radius: 50%;
            animation: twinkle 2s infinite;
        }
        @keyframes twinkle {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }
    </style>
</head>
<body class="space-bg min-h-screen flex items-center justify-center relative overflow-hidden">
    <!-- Animated stars background -->
    <div class="absolute inset-0">
        <div class="star w-1 h-1" style="top: 10%; left: 20%; animation-delay: 0s;"></div>
        <div class="star w-1 h-1" style="top: 30%; left: 70%; animation-delay: 1s;"></div>
        <div class="star w-1 h-1" style="top: 60%; left: 40%; animation-delay: 2s;"></div>
        <div class="star w-1 h-1" style="top: 80%; left: 80%; animation-delay: 0.5s;"></div>
        <div class="star w-1 h-1" style="top: 20%; left: 60%; animation-delay: 1.5s;"></div>
        <div class="star w-1 h-1" style="top: 70%; left: 10%; animation-delay: 2.5s;"></div>
    </div>

    <div class="relative z-10 w-full max-w-md px-6">
        <!-- Logo and Title -->
        <div class="text-center mb-8">
            <div class="text-6xl mb-4">🌌</div>
            <h1 class="text-4xl font-bold text-white mb-2">Planetarion</h1>
            <p class="text-gray-400">Conquer the galaxy, build your empire</p>
        </div>

        <!-- Login Form -->
        <div class="bg-gray-800 bg-opacity-90 backdrop-blur-sm rounded-lg p-8 glow">
            <h2 class="text-2xl font-bold text-white text-center mb-6">Welcome Back</h2>

            <!-- Error Message -->
            <div id="error-message" class="hidden bg-red-600 text-white p-3 rounded mb-4 text-sm">
                Invalid username or password
            </div>

            <!-- Success Message -->
            <div id="success-message" class="hidden bg-green-600 text-white p-3 rounded mb-4 text-sm">
                Login successful! Redirecting...
            </div>

            <form id="login-form" class="space-y-6">
                <div>
                    <label for="username" class="block text-sm font-medium text-gray-300 mb-2">
                        Username
                    </label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        required
                        class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter your username"
                    >
                </div>

                <div>
                    <label for="password" class="block text-sm font-medium text-gray-300 mb-2">
                        Password
                    </label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        required
                        class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter your password"
                    >
                </div>

                <button
                    type="submit"
                    id="login-btn"
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                >
                    Login to Your Empire
                </button>
            </form>

            <!-- Links -->
            <div class="mt-6 text-center space-y-2">
                <p class="text-gray-400">
                    New to Planetarion?
                    <a href="#register" onclick="showRegister()" class="text-blue-400 hover:text-blue-300 ml-1">
                        Create Account
                    </a>
                </p>
                <p class="text-gray-400">
                    <a href="test_demo.html" target="_blank" class="text-purple-400 hover:text-purple-300">
                        🔧 Open Test Interface
                    </a>
                </p>
            </div>
        </div>

        <!-- Register Form (Hidden by default) -->
        <div id="register-form" class="hidden bg-gray-800 bg-opacity-90 backdrop-blur-sm rounded-lg p-8 mt-6 glow">
            <h2 class="text-2xl font-bold text-white text-center mb-6">Join Planetarion</h2>

            <div id="reg-error-message" class="hidden bg-red-600 text-white p-3 rounded mb-4 text-sm"></div>
            <div id="reg-success-message" class="hidden bg-green-600 text-white p-3 rounded mb-4 text-sm"></div>

            <form id="register-form-element" class="space-y-4">
                <div>
                    <label for="reg-username" class="block text-sm font-medium text-gray-300 mb-2">
                        Username
                    </label>
                    <input
                        type="text"
                        id="reg-username"
                        name="reg-username"
                        required
                        class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Choose a username"
                    >
                </div>

                <div>
                    <label for="reg-email" class="block text-sm font-medium text-gray-300 mb-2">
                        Email
                    </label>
                    <input
                        type="email"
                        id="reg-email"
                        name="reg-email"
                        required
                        class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter your email"
                    >
                </div>

                <div>
                    <label for="reg-password" class="block text-sm font-medium text-gray-300 mb-2">
                        Password
                    </label>
                    <input
                        type="password"
                        id="reg-password"
                        name="reg-password"
                        required
                        class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Create a password"
                    >
                </div>

                <button
                    type="submit"
                    id="register-btn"
                    class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-800"
                >
                    Create Your Empire
                </button>
            </form>

            <div class="mt-4 text-center">
                <a href="#login" onclick="showLogin()" class="text-blue-400 hover:text-blue-300">
                    ← Back to Login
                </a>
            </div>
        </div>

        <!-- Footer -->
        <div class="text-center mt-8 text-gray-500 text-sm">
            <p>© 2025 Planetarion - Build, Conquer, Expand</p>
        </div>
    </div>

    <script>
        let authToken = '';

        function showRegister() {
            document.getElementById('login-form').parentElement.classList.add('hidden');
            document.getElementById('register-form').classList.remove('hidden');
        }

        function showLogin() {
            document.getElementById('register-form').classList.add('hidden');
            document.getElementById('login-form').parentElement.classList.remove('hidden');
        }

        // Login form handler
        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const loginBtn = document.getElementById('login-btn');
            const errorDiv = document.getElementById('error-message');
            const successDiv = document.getElementById('success-message');

            loginBtn.disabled = true;
            loginBtn.textContent = 'Logging in...';
            errorDiv.classList.add('hidden');
            successDiv.classList.add('hidden');

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();

                if (response.ok) {
                    authToken = data.access_token;
                    localStorage.setItem('token', authToken);
                    successDiv.classList.remove('hidden');
                    successDiv.textContent = 'Login successful! Redirecting to game...';

                    // Redirect to game dashboard
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);
                } else {
                    errorDiv.classList.remove('hidden');
                    errorDiv.textContent = data.error || 'Login failed';
                }
            } catch (error) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = 'Network error. Please try again.';
            } finally {
                loginBtn.disabled = false;
                loginBtn.textContent = 'Login to Your Empire';
            }
        });

        // Register form handler
        document.getElementById('register-form-element').addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('reg-username').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;

            const registerBtn = document.getElementById('register-btn');
            const errorDiv = document.getElementById('reg-error-message');
            const successDiv = document.getElementById('reg-success-message');

            registerBtn.disabled = true;
            registerBtn.textContent = 'Creating Account...';
            errorDiv.classList.add('hidden');
            successDiv.classList.add('hidden');

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });

                const data = await response.json();

                if (response.ok) {
                    successDiv.classList.remove('hidden');
                    successDiv.textContent = 'Account created successfully! You now have a starting planet.';

                    // Switch to login form after success
                    setTimeout(() => {
                        showLogin();
                        document.getElementById('username').value = username;
                    }, 3000);
                } else {
                    errorDiv.classList.remove('hidden');
                    errorDiv.textContent = data.error || 'Registration failed';
                }
            } catch (error) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = 'Network error. Please try again.';
            } finally {
                registerBtn.disabled = false;
                registerBtn.textContent = 'Create Your Empire';
            }
        });

        // Check if user is already logged in
        const savedToken = localStorage.getItem('token');
        if (savedToken) {
            authToken = savedToken;
            document.getElementById('success-message').classList.remove('hidden');
            document.getElementById('success-message').textContent = 'Welcome back! You are logged in.';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main login page"""
    return render_template_string(LOGIN_PAGE_HTML)

@app.route('/login')
def login_page():
    """Serve the login page"""
    return render_template_string(LOGIN_PAGE_HTML)

@app.route('/health')
def health():
    return {'status': 'healthy'}

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve React static files"""
    import os
    # Use absolute path to avoid relative path issues
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/build/static'))
    print(f"[DEBUG] Static request: {path}")
    print(f"[DEBUG] Current file: {__file__}")
    print(f"[DEBUG] Dirname: {os.path.dirname(__file__)}")
    print(f"[DEBUG] Static dir: {static_dir}")
    print(f"[DEBUG] Static dir exists: {os.path.exists(static_dir)}")
    print(f"[DEBUG] Full path: {os.path.join(static_dir, path)}")
    print(f"[DEBUG] File exists: {os.path.exists(os.path.join(static_dir, path))}")
    try:
        return send_from_directory(static_dir, path)
    except FileNotFoundError as e:
        print(f"[DEBUG] FileNotFoundError: {e}")
        return jsonify({'error': 'Static file not found'}), 404
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
@app.route('/dashboard/<path:path>')
def serve_dashboard(path=None):
    """Serve the React dashboard"""
    if path:
        # Handle static files
        if path.startswith('static/'):
            return send_from_directory('../frontend/build', path)
        return send_from_directory('../frontend/build', path)
    else:
        return send_from_directory('../frontend/build', 'index.html')

@app.route('/api/tick', methods=['POST'])
def manual_tick():
    """Admin endpoint to manually trigger a tick (for testing/debugging)"""
    # In production, this should have admin authentication
    # For now, it's open for development purposes

    # Simple tick logic - increment resources for all planets
    planets = Planet.query.all()
    tick_changes = []

    for planet in planets:
        # Calculate production for this tick (5 seconds = 1/7200 hour)
        # Use max(1, ...) to ensure at least 1 resource per tick for active mines
        metal_produced = max(1, int(planet.metal_mine * 30 * (1.1 ** planet.metal_mine) / 7200)) if planet.metal_mine > 0 else 0
        crystal_produced = max(1, int(planet.crystal_mine * 20 * (1.1 ** planet.crystal_mine) / 7200)) if planet.crystal_mine > 0 else 0
        deuterium_produced = max(1, int(planet.deuterium_synthesizer * 10 * (1.1 ** planet.deuterium_synthesizer) / 7200)) if planet.deuterium_synthesizer > 0 else 0

        # Update planet resources
        planet.metal += metal_produced
        planet.crystal += crystal_produced
        planet.deuterium += deuterium_produced

        print(f"Manual tick for planet {planet.id}: Metal +{metal_produced}, Crystal +{crystal_produced}, Deuterium +{deuterium_produced}")

        tick_changes.append({
            'planet_id': planet.id,
            'metal_change': metal_produced,
            'crystal_change': crystal_produced,
            'deuterium_change': deuterium_produced
        })

    db.session.commit()

    return jsonify({
        'message': 'Manual tick executed successfully',
        'changes': tick_changes
    })

# Register blueprints after all models are defined
def register_blueprints():
    from routes.auth import auth_bp
    from routes.planet_user import planet_mgmt_bp
    from routes.fleet import fleet_mgmt_bp
    from routes.shipyard import shipyard_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(planet_mgmt_bp)
    app.register_blueprint(fleet_mgmt_bp)
    app.register_blueprint(shipyard_bp)

register_blueprints()

def start_scheduler():
    """Start the tick scheduler"""
    from services.tick import run_tick

    # Wrapper function to provide application context
    def run_tick_with_context():
        with app.app_context():
            run_tick()

    # Add tick job to run every 5 seconds
    scheduler.add_job(
        func=run_tick_with_context,
        trigger=IntervalTrigger(seconds=5),
        id='game_tick',
        name='Game Tick',
        replace_existing=True
    )

    # Start the scheduler
    scheduler.start()
    app.logger.info("Tick scheduler started - ticks will run every 5 seconds")

def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown()
        app.logger.info("Tick scheduler shut down")

# Start scheduler when app starts
with app.app_context():
    # Create all database tables
    db.create_all()
    print("Database tables created successfully")
    start_scheduler()

# Register shutdown handler
atexit.register(shutdown_scheduler)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))  # Default to 5001 if PORT not set
    app.run(host='0.0.0.0', port=port, debug=True)

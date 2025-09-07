# Backend package initialization
# This ensures proper SQLAlchemy model registration

print("📦 Initializing backend package...")

# Import database first
print("🗄️ Importing database...")
from .database import db
print("✅ Database imported")

# Import models (these will register with SQLAlchemy)
print("📋 Importing models...")
try:
    from .models import User, Planet, Fleet, Alliance, TickLog
    __all__ = ['db', 'User', 'Planet', 'Fleet', 'Alliance', 'TickLog']
    print("✅ All models imported successfully")
except ImportError as e:
    # Handle case where models can't be imported yet
    __all__ = ['db']
    print(f"⚠️ Models import failed: {e}")

print("📦 Backend package initialization complete")

# For development server
if __name__ == '__main__':
    print("🚀 Starting development server...")
    from .app import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

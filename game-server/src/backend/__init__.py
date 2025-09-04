# Backend package initialization
# This ensures proper SQLAlchemy model registration

# Import database first
from .database import db

# Import models (these will register with SQLAlchemy)
try:
    from .models import User, Planet, Fleet, Alliance, TickLog
    __all__ = ['db', 'User', 'Planet', 'Fleet', 'Alliance', 'TickLog']
except ImportError:
    # Handle case where models can't be imported yet
    __all__ = ['db']

# For development server
if __name__ == '__main__':
    from .app import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

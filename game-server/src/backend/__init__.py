# Backend package initialization
# This ensures proper SQLAlchemy model registration

# Import database first
from backend.database import db

# Import models (these will register with SQLAlchemy)
try:
    from backend.models import User, Planet, Fleet, Alliance, TickLog
    __all__ = ['db', 'User', 'Planet', 'Fleet', 'Alliance', 'TickLog']
except ImportError:
    # Handle case where models can't be imported yet
    __all__ = ['db']

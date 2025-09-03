# Backend package initialization
# This ensures proper SQLAlchemy model registration

from .database import db
from .models import User, Planet, Fleet, Alliance, TickLog

__all__ = ['db', 'User', 'Planet', 'Fleet', 'Alliance', 'TickLog']

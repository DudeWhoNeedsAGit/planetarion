"""
Planetarion Game Server - Centralized Path Configuration

Single source of truth for all important project paths.
Update this file when directory structure changes.
"""

from pathlib import Path

# Project root - single source of truth (config.py is now in src/)
PROJECT_ROOT = Path(__file__).parent.parent

# All important paths defined centrally
PATHS = {
    # Core directories
    'project_root': PROJECT_ROOT,
    'src': PROJECT_ROOT / 'src',
    'backend': PROJECT_ROOT / 'src' / 'backend',
    'frontend': PROJECT_ROOT / 'src' / 'frontend',
    'database': PROJECT_ROOT / 'src' / 'database',
    'tests': PROJECT_ROOT / 'src' / 'tests',
    'scripts': PROJECT_ROOT / 'scripts',

    # Frontend build paths
    'frontend_build': PROJECT_ROOT / 'src' / 'frontend' / 'build',
    'frontend_static': PROJECT_ROOT / 'src' / 'frontend' / 'build' / 'static',
    'frontend_css': PROJECT_ROOT / 'src' / 'frontend' / 'build' / 'static' / 'css',
    'frontend_js': PROJECT_ROOT / 'src' / 'frontend' / 'build' / 'static' / 'js',

    # Backend paths
    'backend_routes': PROJECT_ROOT / 'src' / 'backend' / 'routes',
    'backend_services': PROJECT_ROOT / 'src' / 'backend' / 'services',
    'backend_templates': PROJECT_ROOT / 'src' / 'backend' / 'templates',

    # Test paths
    'unit_tests': PROJECT_ROOT / 'src' / 'tests' / 'unit',
    'integration_tests': PROJECT_ROOT / 'src' / 'tests' / 'integration',

    # Docker and deployment
    'dockerfiles': PROJECT_ROOT / 'src' / 'backend' / 'Dockerfile',
    'docker_compose': PROJECT_ROOT / 'docker-compose.yml',
}

# Helper functions for common path operations
def get_static_dir() -> Path:
    """Get the frontend static files directory"""
    return PATHS['frontend_static']

def get_project_root() -> Path:
    """Get the project root directory"""
    return PATHS['project_root']

def get_test_dir(test_type: str = 'integration') -> Path:
    """Get test directory by type"""
    if test_type == 'unit':
        return PATHS['unit_tests']
    elif test_type == 'integration':
        return PATHS['integration_tests']
    else:
        return PATHS['tests']

def ensure_path_exists(path: Path) -> Path:
    """Ensure a directory exists, create if necessary"""
    path.mkdir(parents=True, exist_ok=True)
    return path

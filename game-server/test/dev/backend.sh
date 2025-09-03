#!/bin/bash
# Backend-focused testing - Optimized Version

echo "🔧 Testing Backend APIs..."
echo "=========================="

# Set up clean paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/game-server/backend"
TEST_DIR="$PROJECT_ROOT/game-server/tests"

# Initialize venv ONCE
echo "🐍 Initializing Python virtual environment..."
cd "$BACKEND_DIR"
source venv/bin/activate
export PYTHONPATH="$BACKEND_DIR"
cd "$SCRIPT_DIR"

echo "🔐 Authentication APIs..."
python -m pytest $TEST_DIR/integration/test_auth.py -v --tb=short --disable-warnings
AUTH_EXIT=$?

echo ""
echo "🪐 Planet Management APIs..."
python -m pytest $TEST_DIR/integration/test_planets.py -v --tb=short --disable-warnings
PLANET_EXIT=$?

echo ""
echo "🚀 Fleet Management APIs..."
python -m pytest $TEST_DIR/integration/test_fleet.py -v --tb=short --disable-warnings
FLEET_EXIT=$?

echo ""
echo "⏰ Tick System..."
python -m pytest $TEST_DIR/integration/test_tick.py -v --tb=short --disable-warnings
TICK_EXIT=$?

echo ""
echo "📊 Backend Test Results:"
echo "========================"
echo "Auth: $([ $AUTH_EXIT -eq 0 ] && echo '✅' || echo '❌')"
echo "Planet: $([ $PLANET_EXIT -eq 0 ] && echo '✅' || echo '❌')"
echo "Fleet: $([ $FLEET_EXIT -eq 0 ] && echo '✅' || echo '❌')"
echo "Tick: $([ $TICK_EXIT -eq 0 ] && echo '✅' || echo '❌')"

if [ $AUTH_EXIT -eq 0 ] && [ $PLANET_EXIT -eq 0 ] && [ $FLEET_EXIT -eq 0 ] && [ $TICK_EXIT -eq 0 ]; then
    echo ""
    echo "🎉 All backend tests passed!"
    echo "============================"
    echo "💡 Next steps:"
    echo "   - Make backend API changes"
    echo "   - Run './test/dev/backend.sh' again"
    echo "   - Or run full TDD: './test/dev/tdd.sh'"
    exit 0
else
    echo ""
    echo "❌ Some backend tests failed"
    echo "============================"
    echo "🔧 Debug commands:"
    echo "   - Verbose output: python -m pytest tests/integration/ -v -s"
    echo "   - Specific test: python -m pytest tests/integration/test_auth.py::TestAuthEndpoints::test_login_success -v -s"
    echo "   - Check database: python -c \"from database import db; db.create_all()\""
    exit 1
fi

#!/bin/bash
# Backend-focused testing

echo "🔧 Testing Backend APIs..."
echo "=========================="

cd game-server

echo "🔐 Authentication APIs..."
python3 -m pytest tests/integration/test_auth.py -v --tb=short --disable-warnings
AUTH_EXIT=$?

echo ""
echo "🪐 Planet Management APIs..."
python3 -m pytest tests/integration/test_planets.py -v --tb=short --disable-warnings
PLANET_EXIT=$?

echo ""
echo "🚀 Fleet Management APIs..."
python3 -m pytest tests/integration/test_fleet.py -v --tb=short --disable-warnings
FLEET_EXIT=$?

echo ""
echo "⏰ Tick System..."
python3 -m pytest tests/integration/test_tick.py -v --tb=short --disable-warnings
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

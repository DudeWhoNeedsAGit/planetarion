#!/bin/bash
# Frontend-focused testing

echo "🎨 Testing Frontend Components..."
echo "================================="

cd game-server/frontend

echo "🧭 Navigation Component..."
npm test -- --testPathPattern=Navigation --watchAll=false --verbose=false
NAV_EXIT=$?

echo ""
echo "📊 Dashboard Component..."
npm test -- --testPathPattern=Dashboard --watchAll=false --verbose=false
DASH_EXIT=$?

echo ""
echo "🎯 Fleet Management Component..."
npm test -- --testPathPattern=FleetManagement --watchAll=false --verbose=false
FLEET_EXIT=$?

echo ""
echo "📊 Frontend Test Results:"
echo "========================="
echo "Navigation: $([ $NAV_EXIT -eq 0 ] && echo '✅' || echo '❌')"
echo "Dashboard: $([ $DASH_EXIT -eq 0 ] && echo '✅' || echo '❌')"
echo "Fleet: $([ $FLEET_EXIT -eq 0 ] && echo '✅' || echo '❌')"

if [ $NAV_EXIT -eq 0 ] && [ $DASH_EXIT -eq 0 ] && [ $FLEET_EXIT -eq 0 ]; then
    echo ""
    echo "🎉 All frontend tests passed!"
    echo "=============================="
    echo "💡 Next steps:"
    echo "   - Make frontend component changes"
    echo "   - Run './test/dev/frontend.sh' again"
    echo "   - Or run full TDD: './test/dev/tdd.sh'"
    exit 0
else
    echo ""
    echo "❌ Some frontend tests failed"
    echo "=============================="
    echo "🔧 Debug commands:"
    echo "   - Verbose output: npm test -- --verbose"
    echo "   - Specific component: npm test -- --testPathPattern=Navigation --verbose"
    echo "   - Watch mode: npm test -- --testPathPattern=Navigation"
    echo "   - Update snapshots: npm test -- --testPathPattern=Navigation -u"
    exit 1
fi

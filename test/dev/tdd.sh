#!/bin/bash
# Fast TDD loop for development

echo "🧪 Running TDD Cycle..."
echo "======================"

START_TIME=$(date +%s)
FAILED_TESTS=()
TOTAL_TESTS=5

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo ""
    echo "🔍 Running $test_name..."
    echo "------------------------"

    if eval "$test_command"; then
        echo "✅ $test_name PASSED"
        return 0
    else
        echo "❌ $test_name FAILED"
        FAILED_TESTS+=("$test_name")
        return 1
    fi
}

# Backend API tests
run_test "Backend Auth API" "cd game-server && python3 -m pytest tests/integration/test_auth.py -v --tb=short --disable-warnings"
BACKEND_AUTH_EXIT=$?

run_test "Backend Planet API" "cd game-server && python3 -m pytest tests/integration/test_planets.py -v --tb=short --disable-warnings"
BACKEND_PLANET_EXIT=$?

run_test "Backend Tick System" "cd game-server && python3 -m pytest tests/integration/test_tick.py::TestAutomaticTickSystem -v --tb=short --disable-warnings"
BACKEND_TICK_EXIT=$?

# Frontend component tests
run_test "Frontend Navigation" "cd game-server/frontend && npm test -- --testPathPattern=Navigation --watchAll=false --verbose=false"
FRONTEND_NAV_EXIT=$?

run_test "Frontend Dashboard" "cd game-server/frontend && npm test -- --testPathPattern=Dashboard --watchAll=false --verbose=false"
FRONTEND_DASH_EXIT=$?

# Calculate results
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

PASSED_TESTS=$(( (BACKEND_AUTH_EXIT == 0 ? 1 : 0) + (BACKEND_PLANET_EXIT == 0 ? 1 : 0) + (BACKEND_TICK_EXIT == 0 ? 1 : 0) + (FRONTEND_NAV_EXIT == 0 ? 1 : 0) + (FRONTEND_DASH_EXIT == 0 ? 1 : 0) ))
FAILED_COUNT=$((TOTAL_TESTS - PASSED_TESTS))

echo ""
echo "📊 TDD Results Summary"
echo "======================"
echo "⏱️  Duration: ${DURATION}s"
echo "✅ Passed: $PASSED_TESTS/$TOTAL_TESTS"
echo "❌ Failed: $FAILED_COUNT/$TOTAL_TESTS"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed Tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "   - $test"
    done
fi

echo ""
if [ $FAILED_COUNT -eq 0 ]; then
    echo "🎉 All tests passed! Ready to commit."
    echo "===================================="
    echo "💡 Tips:"
    echo "   - Make your code changes"
    echo "   - Run './test/dev/tdd.sh' again"
    echo "   - Repeat until all tests pass"
    exit 0
else
    echo "⚠️  Some tests failed. Fix issues before committing."
    echo "=================================================="
    echo "🔧 Debug commands:"
    echo "   - Backend: cd game-server && python -m pytest tests/integration/ -v -s"
    echo "   - Frontend: cd game-server/frontend && npm test -- --verbose"
    echo "   - Services: ./test/dev/stop.sh && ./test/dev/start.sh"
    exit 1
fi

// Simple test to check if planets page renders correctly
// This tests the frontend component logic without Docker complexity

const fs = require('fs');
const path = require('path');

// Read the Dashboard component
const dashboardPath = path.join(__dirname, 'src/frontend/src/Dashboard.js');
const dashboardCode = fs.readFileSync(dashboardPath, 'utf8');

console.log('🧪 Testing Planets Page Frontend Logic...\n');

// Test 1: Check if planets section exists in renderSection
console.log('1. Checking if planets section exists in Dashboard...');
if (dashboardCode.includes("case 'planets':")) {
  console.log('✅ Planets case found in renderSection');
} else {
  console.log('❌ Planets case NOT found in renderSection');
}

// Test 2: Check if planets API call exists
console.log('\n2. Checking if planets API call exists...');
if (dashboardCode.includes("fetchPlanets")) {
  console.log('✅ fetchPlanets function found');
} else {
  console.log('❌ fetchPlanets function NOT found');
}

// Test 3: Check if planets state management exists
console.log('\n3. Checking planets state management...');
if (dashboardCode.includes("const [planets, setPlanets]")) {
  console.log('✅ Planets state management found');
} else {
  console.log('❌ Planets state management NOT found');
}

// Test 4: Check if planets navigation exists
console.log('\n4. Checking planets navigation...');
const navigationPath = path.join(__dirname, 'src/frontend/src/Navigation.js');
const navigationCode = fs.readFileSync(navigationPath, 'utf8');

if (navigationCode.includes("'Planets'")) {
  console.log('✅ Planets navigation tab found');
} else {
  console.log('❌ Planets navigation tab NOT found');
}

// Test 5: Check for potential JavaScript errors in planets section
console.log('\n5. Checking for potential JavaScript errors in planets section...');
const planetsSection = dashboardCode.match(/case 'planets':([\s\S]*?)case '[^']+':/);
if (planetsSection) {
  const planetsCode = planetsSection[1];

  // Check for common issues
  const issues = [];

  if (!planetsCode.includes('planets.map')) {
    issues.push('❌ No planets.map() found - planets won\'t render');
  }

  if (!planetsCode.includes('selectedPlanet')) {
    issues.push('❌ No selectedPlanet usage found - planet selection may not work');
  }

  if (!planetsCode.includes('Resources')) {
    issues.push('❌ No Resources section found - resource display missing');
  }

  if (!planetsCode.includes('Buildings')) {
    issues.push('❌ No Buildings section found - building management missing');
  }

  if (issues.length === 0) {
    console.log('✅ No obvious JavaScript errors found in planets section');
  } else {
    issues.forEach(issue => console.log(issue));
  }
} else {
  console.log('❌ Could not extract planets section from Dashboard component');
}

// Test 6: Check if planets data structure is correct
console.log('\n6. Checking planets data structure expectations...');
if (dashboardCode.includes('planet.resources.metal')) {
  console.log('✅ Planet resources structure looks correct');
} else {
  console.log('❌ Planet resources structure may be incorrect');
}

if (dashboardCode.includes('planet.structures.metal_mine')) {
  console.log('✅ Planet structures structure looks correct');
} else {
  console.log('❌ Planet structures structure may be incorrect');
}

console.log('\n🏁 Frontend Logic Test Complete!');
console.log('\n💡 If all checks pass, the planets page should work correctly.');
console.log('💡 If any checks fail, there may be an issue with the frontend implementation.');

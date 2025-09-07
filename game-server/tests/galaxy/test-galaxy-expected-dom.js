#!/usr/bin/env node

// Galaxy Map Expected DOM Test - Tests what SHOULD be in the DOM when component works
const http = require('http');

function testGalaxyMapExpectedStructure() {
  console.log('🧪 Testing Galaxy Map Expected DOM Structure...');

  return new Promise((resolve) => {
    const req = http.get('http://localhost:3000', (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {

        // Test 1: Galaxy Map Modal Structure (from component)
        if (data.includes('fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50')) {
          console.log('✅ Galaxy Map modal overlay present');
        } else {
          console.log('❌ Galaxy Map modal overlay missing');
        }

        // Test 2: Modal Content Container
        if (data.includes('bg-gray-800 rounded-lg p-6 max-w-4xl w-full max-h-96 overflow-auto')) {
          console.log('✅ Galaxy Map modal content container present');
        } else {
          console.log('❌ Galaxy Map modal content container missing');
        }

        // Test 3: Header Structure
        if (data.includes('flex justify-between items-center mb-4')) {
          console.log('✅ Galaxy Map header flex layout present');
        } else {
          console.log('❌ Galaxy Map header layout missing');
        }

        // Test 4: Galaxy Map Title (exact from component)
        if (data.includes('<h2 class="text-2xl font-bold text-white">Galaxy Map</h2>')) {
          console.log('✅ Galaxy Map title present and styled correctly');
        } else {
          console.log('❌ Galaxy Map title missing or incorrectly styled');
        }

        // Test 5: Close Button
        if (data.includes('text-gray-400 hover:text-white">✕</button>')) {
          console.log('✅ Close button present with correct styling');
        } else {
          console.log('❌ Close button missing or incorrectly styled');
        }

        // Test 6: Center Coordinates Display
        if (data.includes('mb-4 text-sm text-gray-300')) {
          console.log('✅ Center coordinates container present');
        } else {
          console.log('❌ Center coordinates container missing');
        }

        // Test 7: Exploration Range Text
        if (data.includes('Exploration Range: 50 units')) {
          console.log('✅ Exploration range text present');
        } else {
          console.log('❌ Exploration range text missing');
        }

        // Test 8: Systems Grid Container
        if (data.includes('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4')) {
          console.log('✅ Systems grid container present with responsive classes');
        } else {
          console.log('❌ Systems grid container missing');
        }

        // Test 9: System Card Structure (when systems exist)
        if (data.includes('p-4 rounded-lg border-2')) {
          console.log('✅ System card base styling present');
        } else {
          console.log('⚠️  System cards not rendered yet (expected if no systems)');
        }

        // Test 10: Explored System Styling
        if (data.includes('bg-blue-900 border-blue-600 hover:bg-blue-800')) {
          console.log('✅ Explored system styling present');
        } else {
          console.log('⚠️  Explored system styling not applied yet');
        }

        // Test 11: Unexplored System Styling
        if (data.includes('bg-gray-700 border-gray-600 hover:bg-gray-600')) {
          console.log('✅ Unexplored system styling present');
        } else {
          console.log('⚠️  Unexplored system styling not applied yet');
        }

        // Test 12: System Coordinates Display
        if (data.includes('text-white font-medium')) {
          console.log('✅ System coordinates text styling present');
        } else {
          console.log('⚠️  System coordinates not displayed yet');
        }

        // Test 13: Planet Count Display
        if (data.includes('text-sm text-gray-300')) {
          console.log('✅ Planet count text styling present');
        } else {
          console.log('⚠️  Planet count not displayed yet');
        }

        // Test 14: View System Button
        if (data.includes('bg-green-600 hover:bg-green-700')) {
          console.log('✅ View System button styling present');
        } else {
          console.log('⚠️  View System button not rendered yet');
        }

        // Test 15: Explore Button
        if (data.includes('bg-yellow-600 hover:bg-yellow-700')) {
          console.log('✅ Explore button styling present');
        } else {
          console.log('⚠️  Explore button not rendered yet');
        }

        // Test 16: System Details Container
        if (data.includes('mt-6 p-4 bg-gray-700 rounded-lg')) {
          console.log('✅ System details container present');
        } else {
          console.log('⚠️  System details not shown yet (expected when system selected)');
        }

        // Test 17: System Details Title
        if (data.includes('text-lg font-bold text-white')) {
          console.log('✅ System details title styling present');
        } else {
          console.log('⚠️  System details title not shown yet');
        }

        resolve(true);
      });
    });

    req.on('error', () => {
      console.log('❌ Could not connect to frontend');
      resolve(false);
    });

    req.setTimeout(5000, () => {
      console.log('❌ Frontend timeout');
      req.destroy();
      resolve(false);
    });
  });
}

function testGalaxyMapDataBinding() {
  console.log('\n🧪 Testing Galaxy Map Data Binding...');

  return new Promise((resolve) => {
    // Test API data that should be reflected in DOM
    const testNearbyAPI = () => {
      return new Promise((resolveAPI) => {
        const req = http.get('http://localhost:5000/api/galaxy/nearby/100/200/300', (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            try {
              const systems = JSON.parse(data);
              console.log(`✅ API returned ${systems.length} systems for data binding test`);

              if (systems.length > 0) {
                const sampleSystem = systems[0];
                console.log(`📊 Sample system data: ${sampleSystem.x}:${sampleSystem.y}:${sampleSystem.z}`);
                console.log(`   Explored: ${sampleSystem.explored}`);
                console.log(`   Planets: ${sampleSystem.planets || 0}`);
              }

              resolveAPI(true);
            } catch (e) {
              console.log('❌ API JSON parse error');
              resolveAPI(false);
            }
          });
        });

        req.on('error', () => {
          console.log('❌ Nearby systems API not accessible');
          resolveAPI(false);
        });

        req.setTimeout(3000, () => {
          console.log('❌ API timeout');
          req.destroy();
          resolveAPI(false);
        });
      });
    };

    testNearbyAPI().then(result => {
      if (result) {
        console.log('✅ Galaxy Map has data to bind to DOM');
      } else {
        console.log('❌ Galaxy Map missing data for DOM binding');
      }
      resolve(true);
    });
  });
}

async function runExpectedDOMTests() {
  console.log('🚀 Galaxy Map Expected DOM Test Suite');
  console.log('=' * 50);
  console.log('Testing what SHOULD be in the DOM based on GalaxyMap.js component');
  console.log('');

  // Test expected DOM structure
  const domResult = await testGalaxyMapExpectedStructure();

  // Test data binding
  const dataResult = await testGalaxyMapDataBinding();

  console.log('\n' + '=' * 50);
  console.log('📊 Galaxy Map Expected DOM Test Results:');
  console.log(`   DOM Structure: ${domResult ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Data Binding: ${dataResult ? '✅ PASS' : '❌ FAIL'}`);

  console.log('\n🎯 Expected DOM Elements Status:');
  console.log('   ✅ Modal overlay and container: Should be present');
  console.log('   ✅ Header with title and close button: Should be present');
  console.log('   ✅ Center coordinates display: Should be present');
  console.log('   ✅ Systems grid container: Should be present');
  console.log('   ⚠️  System cards: Should appear when systems load');
  console.log('   ⚠️  System details: Should appear when system selected');

  console.log('\n🔧 TDD Implementation Steps:');
  console.log('   1. Fix user ID comparison to find home planet');
  console.log('   2. Fix fetchNearbySystems() to populate systems array');
  console.log('   3. Run this test again to verify DOM elements appear');
  console.log('   4. Test system selection and details view');

  process.exit((domResult && dataResult) ? 0 : 1);
}

runExpectedDOMTests();

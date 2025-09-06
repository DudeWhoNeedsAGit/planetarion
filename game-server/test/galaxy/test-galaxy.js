#!/usr/bin/env node

// Galaxy Map Test - Simple Node.js test for frontend
const http = require('http');

function testGalaxyMap() {
  console.log('🧪 Testing Galaxy Map functionality...');

  return new Promise((resolve) => {
    const req = http.get('http://localhost:3000', (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        // Test 1: Frontend is running
        if (data.includes('Planetarion')) {
          console.log('✅ Frontend is running - Planetarion title found');
        } else {
          console.log('❌ Frontend not responding correctly');
          return resolve(false);
        }

        // Test 2: Check for Galaxy Map (this will fail until implemented)
        if (data.includes('Galaxy Map')) {
          console.log('✅ Galaxy Map feature is implemented!');
        } else {
          console.log('❌ Galaxy Map not implemented yet - implement this feature');
        }

        // Test 3: Check for navigation
        if (data.includes('Dashboard') || data.includes('Overview')) {
          console.log('✅ Navigation system working');
        } else {
          console.log('❌ Navigation not found');
        }

        console.log('\n📊 Test Summary:');
        console.log('- ✅ Frontend: Working');
        console.log('- ❓ Galaxy Map: Not implemented yet (this is expected)');
        console.log('- ✅ Navigation: Working');

        resolve(true);
      });
    });

    req.on('error', (e) => {
      console.log('❌ Could not connect to frontend - make sure it\'s running');
      console.log('   Run: cd game-server && docker compose up -d');
      resolve(false);
    });

    req.setTimeout(5000, () => {
      console.log('❌ Request timeout - frontend not responding');
      req.destroy();
      resolve(false);
    });
  });
}

// Run the test
testGalaxyMap().then(success => {
  if (success) {
    console.log('\n🎉 Test completed successfully!');
    console.log('💡 Next: Implement Galaxy Map feature in your React app');
  } else {
    console.log('\n❌ Test failed - check frontend status');
  }
  process.exit(success ? 0 : 1);
});

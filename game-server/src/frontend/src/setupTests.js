// src/setupTests.js
// Jest setup file (loaded automatically by react-scripts before running tests)

// Polyfill missing Node globals for dependencies like supertest/formidable.
// Some local Node/Jest environments don't expose TextEncoder/TextDecoder by default.
// Keep this at the top so it runs before test modules are evaluated.
// eslint-disable-next-line no-undef
const { TextEncoder, TextDecoder } = require('util');
// eslint-disable-next-line no-undef
global.TextEncoder = global.TextEncoder || TextEncoder;
// eslint-disable-next-line no-undef
global.TextDecoder = global.TextDecoder || TextDecoder;

// Import Jest DOM extensions for better assertions
const jestDom = require('@testing-library/jest-dom');

// Global test configuration
beforeAll(() => {
  // Set test environment
  process.env.NODE_ENV = 'test';

  // Configure console methods for cleaner test output
  const originalConsoleError = console.error;
  console.error = (...args) => {
    // Suppress React warnings in tests unless they're actual errors
    if (typeof args[0] === 'string' && args[0].includes('Warning:')) {
      return;
    }
    originalConsoleError(...args);
  };

  // Set up global test timeouts
  jest.setTimeout(30000); // 30 seconds for integration tests
});

afterAll(() => {
  // Clean up after all tests
  jest.clearAllTimers();
  jest.clearAllMocks();
});

// Mock localStorage for tests
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock fetch for tests that need it
global.fetch = jest.fn();

// Add custom matchers
expect.extend({
  toBeValidFleet(received) {
    const pass = received &&
                 typeof received === 'object' &&
                 received.id &&
                 received.user_id &&
                 received.status &&
                 Array.isArray(received.ships);

    return {
      message: () => `expected ${received} to be a valid fleet object`,
      pass,
    };
  },

  toBeValidPlanet(received) {
    const pass = received &&
                 typeof received === 'object' &&
                 received.id &&
                 received.name &&
                 typeof received.x === 'number' &&
                 typeof received.y === 'number' &&
                 typeof received.z === 'number';

    return {
      message: () => `expected ${received} to be a valid planet object`,
      pass,
    };
  },

  toBeValidUser(received) {
    const pass = received &&
                 typeof received === 'object' &&
                 received.id &&
                 received.username &&
                 received.email;

    return {
      message: () => `expected ${received} to be a valid user object`,
      pass,
    };
  },
});

// Helper function to wait for async operations
global.waitForAsync = (ms = 100) => new Promise(resolve => setTimeout(resolve, ms));

// Helper to create mock API responses
global.createMockResponse = (data, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(JSON.stringify(data)),
});

// Export for use in tests
global.testUtils = {
  waitForAsync: global.waitForAsync,
  createMockResponse: global.createMockResponse,
  localStorageMock,
};

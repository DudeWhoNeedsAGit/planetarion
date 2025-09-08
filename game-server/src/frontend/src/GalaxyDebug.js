// Galaxy Map Debug Utility
// Provides comprehensive debugging for GalaxyMap component

class GalaxyDebugger {
  constructor() {
    this.config = null;
    this.logBuffer = [];
    this.maxBufferSize = 1000;
    this.throttleCache = new Map(); // Cache for throttling repetitive logs
    this.loadConfig();
  }

  async loadConfig() {
    console.log('🔍 Debug: Starting config load...');
    try {
      console.log('🔍 Debug: Fetching /galaxy-debug-config.json...');
      const response = await fetch('/galaxy-debug-config.json');
      console.log('🔍 Debug: Config fetch response:', response.status, response.ok);

      if (response.ok) {
        const configData = await response.json();
        console.log('🔍 Debug: Config data loaded:', configData);
        this.config = configData;
        this.log('INFO', 'GalaxyDebug', 'Configuration loaded successfully', { config: this.config });
      } else {
        console.log('🔍 Debug: Config fetch failed, using fallback');
        // Fallback config if file not found
        this.config = {
          debugEnabled: true,
          logging: { console: true, file: true, filePath: 'galaxy-debug.log' },
          visual: { debugPanel: true, elementBoundaries: true },
          tracing: { componentLifecycle: true, propsValidation: true }
        };
        this.log('WARN', 'GalaxyDebug', 'Using fallback configuration');
      }
    } catch (error) {
      console.error('❌ Debug: Config loading exception:', error.message);
      console.error('❌ Debug: Config loading stack:', error.stack);
      this.log('ERROR', 'GalaxyDebug', 'Failed to load config, using defaults', { error: error.message });
      this.config = { debugEnabled: true, logging: { console: true, file: false } };
    }
    console.log('🔍 Debug: Final config object:', this.config);
  }

  log(level, component, message, data = null) {
    if (!this.config?.debugEnabled) return;

    // Check if this log should be throttled
    if (this.shouldThrottleLog(component, message, data)) {
      return;
    }

    const entry = {
      timestamp: new Date().toISOString(),
      level: level.toUpperCase(),
      component,
      message,
      data,
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // Add to buffer
    this.logBuffer.push(entry);
    if (this.logBuffer.length > this.maxBufferSize) {
      this.logBuffer.shift();
    }

    // Console logging
    if (this.config?.logging?.console && this.shouldLogToConsole(level)) {
      this.logToConsole(entry);
    }

    // File logging
    if (this.config?.logging?.file) {
      this.logToFile(entry);
    }
  }

  shouldLogToConsole(level) {
    const levels = ['ERROR', 'WARN', 'INFO', 'DEBUG'];
    const consoleLevel = this.config?.levels?.console || 'WARN'; // Changed from 'INFO' to 'WARN'
    return levels.indexOf(level) <= levels.indexOf(consoleLevel);
  }

  shouldThrottleLog(component, message, data) {
    const now = Date.now();
    const cacheKey = `${component}:${message}`;

    // Define throttling rules for frequent log types
    const throttleRules = {
      // Throttle sector-grid element creation (once per second)
      'GalaxyMap:Creating sector-grid element': 1000,

      // Throttle sector-grid element rendering (once per second)
      'GalaxyMap:Rendering sector-grid element': 1000,

      // Throttle component updates with empty changes (once per 5 seconds)
      'GalaxyMap:Component updating': data?.changes && Object.keys(data.changes).length === 0 ? 5000 : 0,

      // Throttle galaxy map rendering (once per 2 seconds)
      'GalaxyMap:Rendering galaxy map': 2000,

      // Throttle data flow sector-generation (once per 3 seconds)
      'GalaxyMap:Data flow: sector-generation': 3000,

      // Throttle sector grid generation (once per 2 seconds)
      'GalaxyMap:Generating sector grid': 2000
    };

    const throttleTime = throttleRules[cacheKey];
    if (!throttleTime) {
      return false; // No throttling for this log type
    }

    const lastLogTime = this.throttleCache.get(cacheKey);
    if (!lastLogTime || (now - lastLogTime) >= throttleTime) {
      this.throttleCache.set(cacheKey, now);
      return false; // Allow this log
    }

    return true; // Throttle this log
  }

  logToConsole(entry) {
    const prefix = `[${entry.timestamp}] ${entry.component}`;
    const message = `${entry.message}`;

    switch (entry.level) {
      case 'ERROR':
        console.error(`${prefix} ❌`, message, entry.data || '');
        break;
      case 'WARN':
        console.warn(`${prefix} ⚠️`, message, entry.data || '');
        break;
      case 'INFO':
        console.info(`${prefix} ℹ️`, message, entry.data || '');
        break;
      case 'DEBUG':
        console.debug(`${prefix} 🔍`, message, entry.data || '');
        break;
      default:
        console.log(`${prefix}`, message, entry.data || '');
    }
  }

  async logToFile(entry) {
    try {
      console.log('🔍 Debug: Attempting to send log to backend:', entry);

      // Send log entry to backend API
      const response = await fetch('/api/debug/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(entry)
      });

      console.log('🔍 Debug: API response status:', response.status);
      console.log('🔍 Debug: API response ok:', response.ok);

      if (response.ok) {
        console.log('✅ Debug: Successfully sent log to backend');
        // Successfully sent to backend
        return;
      } else {
        console.error('❌ Debug: Backend logging failed with status:', response.status);
        const errorText = await response.text();
        console.error('❌ Debug: Backend error response:', errorText);
        // Backend failed, fall back to localStorage
        console.warn('Backend logging failed, falling back to localStorage');
        this.fallbackToLocalStorage(entry);
      }
    } catch (error) {
      console.error('❌ Debug: Network error sending log to backend:', error.message);
      console.error('❌ Debug: Error stack:', error.stack);
      // Network error, fall back to localStorage
      console.warn('Network error, falling back to localStorage:', error.message);
      this.fallbackToLocalStorage(entry);
    }
  }

  fallbackToLocalStorage(entry) {
    try {
      const logString = JSON.stringify(entry) + '\n';
      const existingLogs = localStorage.getItem('galaxy-debug-logs') || '';
      const newLogs = existingLogs + logString;

      // Keep only last 50KB to prevent storage bloat
      const truncatedLogs = newLogs.length > 51200 ?
        newLogs.substring(newLogs.length - 51200) : newLogs;

      localStorage.setItem('galaxy-debug-logs', truncatedLogs);
    } catch (error) {
      console.error('Failed to write to fallback debug log:', error);
    }
  }

  // Component lifecycle debugging
  componentMount(componentName, props, file = null, line = null) {
    this.log('INFO', componentName, 'Component mounted', {
      props: this.sanitizeProps(props),
      timestamp: Date.now(),
      file: file || 'unknown',
      line: line || 'unknown'
    });
  }

  componentRender(componentName, props, state, file = null, line = null) {
    this.log('DEBUG', componentName, 'Component rendering', {
      props: this.sanitizeProps(props),
      state: this.sanitizeState(state),
      file: file || 'unknown',
      line: line || 'unknown'
    });
  }

  componentUpdate(componentName, prevProps, nextProps, file = null, line = null) {
    this.log('DEBUG', componentName, 'Component updating', {
      prevProps: this.sanitizeProps(prevProps),
      nextProps: this.sanitizeProps(nextProps),
      changes: this.detectChanges(prevProps, nextProps),
      file: file || 'unknown',
      line: line || 'unknown'
    });
  }

  componentUnmount(componentName, file = null, line = null) {
    this.log('INFO', componentName, 'Component unmounted', {
      file: file || 'unknown',
      line: line || 'unknown'
    });
  }

  // Props validation
  validateProps(componentName, props, expectedProps) {
    const missing = [];
    const invalid = [];

    expectedProps.forEach(expected => {
      if (!(expected.name in props)) {
        missing.push(expected.name);
      } else if (expected.type && typeof props[expected.name] !== expected.type) {
        invalid.push({
          name: expected.name,
          expected: expected.type,
          actual: typeof props[expected.name]
        });
      }
    });

    if (missing.length > 0 || invalid.length > 0) {
      this.log('ERROR', componentName, 'Props validation failed', {
        missing,
        invalid,
        received: Object.keys(props)
      });
      return false;
    }

    this.log('DEBUG', componentName, 'Props validation passed', {
      props: this.sanitizeProps(props)
    });
    return true;
  }

  // Data flow tracing
  traceDataFlow(componentName, operation, input, output, success = true) {
    this.log(success ? 'INFO' : 'ERROR', componentName, `Data flow: ${operation}`, {
      input: this.sanitizeData(input),
      output: this.sanitizeData(output),
      success
    });
  }

  // API call monitoring
  traceApiCall(endpoint, method, requestData, response, error = null) {
    this.log(error ? 'ERROR' : 'INFO', 'API', `API Call: ${method} ${endpoint}`, {
      request: this.sanitizeData(requestData),
      response: error ? { error: error.message } : this.sanitizeData(response),
      duration: response?.duration || 0
    });
  }

  // Visual element debugging
  traceElementCreation(componentName, elementType, elementData) {
    // Skip logging for sector-boundary elements to reduce noise
    if (elementType === 'sector-boundary') {
      return;
    }

    this.log('DEBUG', componentName, `Creating ${elementType} element`, {
      type: elementType,
      data: this.sanitizeData(elementData)
    });
  }

  traceElementRendering(componentName, elementType, rendered) {
    this.log('DEBUG', componentName, `Rendering ${elementType} element`, {
      type: elementType,
      rendered: rendered ? 'success' : 'failed'
    });
  }

  // Utility methods
  sanitizeProps(props) {
    if (!props) return null;
    const sanitized = { ...props };

    // Remove sensitive data
    const sensitiveKeys = ['password', 'token', 'apiKey'];
    sensitiveKeys.forEach(key => {
      if (key in sanitized) {
        sanitized[key] = '[REDACTED]';
      }
    });

    // Truncate large arrays/objects
    Object.keys(sanitized).forEach(key => {
      if (Array.isArray(sanitized[key]) && sanitized[key].length > 10) {
        sanitized[key] = `[Array(${sanitized[key].length})]`;
      } else if (typeof sanitized[key] === 'object' && sanitized[key] !== null) {
        const size = JSON.stringify(sanitized[key]).length;
        if (size > 1000) {
          sanitized[key] = `[Object(${Object.keys(sanitized[key]).length} keys, ${size} bytes)]`;
        }
      }
    });

    return sanitized;
  }

  sanitizeState(state) {
    return this.sanitizeProps(state);
  }

  sanitizeData(data) {
    return this.sanitizeProps(data);
  }

  detectChanges(prev, next) {
    const changes = {};
    const allKeys = new Set([...Object.keys(prev || {}), ...Object.keys(next || {})]);

    allKeys.forEach(key => {
      if (JSON.stringify(prev?.[key]) !== JSON.stringify(next?.[key])) {
        changes[key] = {
          from: prev?.[key],
          to: next?.[key]
        };
      }
    });

    return changes;
  }

  // Export logs for analysis
  exportLogs() {
    const logs = localStorage.getItem('galaxy-debug-logs') || '';
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'galaxy-debug.log';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Clear logs
  clearLogs() {
    localStorage.removeItem('galaxy-debug-logs');
    this.logBuffer = [];
    this.log('INFO', 'GalaxyDebug', 'Debug logs cleared');
  }

  // Get current logs
  getLogs() {
    return this.logBuffer;
  }
}

// Create singleton instance
const galaxyDebugger = new GalaxyDebugger();

// Export for use in components
export default galaxyDebugger;

// Helper functions for easy use
export const debugLog = (level, component, message, data) =>
  galaxyDebugger.log(level, component, message, data);

export const debugComponent = {
  mount: (name, props, file = null, line = null) => galaxyDebugger.componentMount(name, props, file, line),
  render: (name, props, state, file = null, line = null) => galaxyDebugger.componentRender(name, props, state, file, line),
  update: (name, prevProps, nextProps, file = null, line = null) => galaxyDebugger.componentUpdate(name, prevProps, nextProps, file, line),
  unmount: (name, file = null, line = null) => galaxyDebugger.componentUnmount(name, file, line)
};

// Helper function to get current line number (for debugging)
export const getCurrentLine = () => {
  const error = new Error();
  const stack = error.stack;
  const lines = stack.split('\n');
  // Find the line that contains the actual call
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.includes('getCurrentLine') && lines[i + 1]) {
      // Extract line number from the next stack frame
      const match = lines[i + 1].match(/:(\d+):\d+\)$/);
      if (match) {
        return parseInt(match[1]);
      }
    }
  }
  return 'unknown';
};

export const debugProps = (componentName, props, expectedProps) =>
  galaxyDebugger.validateProps(componentName, props, expectedProps);

export const debugDataFlow = (componentName, operation, input, output, success) =>
  galaxyDebugger.traceDataFlow(componentName, operation, input, output, success);

export const debugApi = (endpoint, method, requestData, response, error) =>
  galaxyDebugger.traceApiCall(endpoint, method, requestData, response, error);

export const debugElement = {
  create: (componentName, elementType, elementData) =>
    galaxyDebugger.traceElementCreation(componentName, elementType, elementData),
  render: (componentName, elementType, rendered) =>
    galaxyDebugger.traceElementRendering(componentName, elementType, rendered)
};

"""
Unit tests for debug logging system

Tests the debug logging API endpoints and file writing functionality.
"""

import os
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from backend.routes.debug import (
    debug_bp,
    DEBUG_LOG_DIR,
    log_debug_entry,
    get_debug_logs,
    clear_debug_logs,
    get_debug_stats
)


class TestDebugLogging:
    """Test debug logging functionality"""

    def setup_method(self):
        """Set up test environment"""
        # Create temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_file = os.path.join(self.temp_dir, 'test-debug.log')

        # Mock the DEBUG_LOG_DIR to use our temp directory
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            self.app = None  # We'll set this up in individual tests if needed

    def teardown_method(self):
        """Clean up test environment"""
        # Remove test log files
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_log_debug_entry_success(self):
        """Test successful debug log entry creation"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # Test data
                log_data = {
                    'timestamp': '2025-09-07T22:00:00.000Z',
                    'level': 'INFO',
                    'component': 'TestComponent',
                    'message': 'Test message',
                    'data': {'test': 'value'},
                    'userAgent': 'TestAgent',
                    'url': 'http://test.com'
                }

                # Make request
                response = client.post('/api/debug/log', json=log_data)

                # Verify response
                assert response.status_code == 200
                response_data = json.loads(response.data)
                assert response_data['success'] is True
                assert 'message' in response_data

                # Verify file was created and contains correct data
                assert os.path.exists(os.path.join(self.temp_dir, 'galaxy-debug.log'))

                with open(os.path.join(self.temp_dir, 'galaxy-debug.log'), 'r') as f:
                    content = f.read()
                    log_entry = json.loads(content.strip())

                    assert log_entry['timestamp'] == log_data['timestamp']
                    assert log_entry['level'] == log_data['level']
                    assert log_entry['component'] == log_data['component']
                    assert log_entry['message'] == log_data['message']
                    assert log_entry['data'] == log_data['data']
                    assert 'server_received' in log_entry

    def test_log_debug_entry_missing_fields(self):
        """Test debug log entry with missing required fields"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # Test data with missing required field
                log_data = {
                    'timestamp': '2025-09-07T22:00:00.000Z',
                    'level': 'INFO',
                    # Missing 'component'
                    'message': 'Test message'
                }

                # Make request
                response = client.post('/api/debug/log', json=log_data)

                # Verify response indicates error
                assert response.status_code == 400
                response_data = json.loads(response.data)
                assert 'error' in response_data
                assert 'Missing required field' in response_data['error']

    def test_log_debug_entry_invalid_data(self):
        """Test debug log entry with invalid data"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # Make request with no JSON data
                response = client.post('/api/debug/log')

                # Verify response indicates error
                assert response.status_code == 400
                response_data = json.loads(response.data)
                assert 'error' in response_data

    def test_component_specific_logging(self):
        """Test that major components get their own log files"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # Test GalaxyMap component logging
                log_data = {
                    'timestamp': '2025-09-07T22:00:00.000Z',
                    'level': 'INFO',
                    'component': 'GalaxyMap',
                    'message': 'Component test',
                    'data': {'test': 'galaxy'},
                    'userAgent': 'TestAgent',
                    'url': 'http://test.com'
                }

                response = client.post('/api/debug/log', json=log_data)
                assert response.status_code == 200

                # Verify both main log and component-specific log exist
                main_log = os.path.join(self.temp_dir, 'galaxy-debug.log')
                component_log = os.path.join(self.temp_dir, 'galaxymap-debug.log')

                assert os.path.exists(main_log)
                assert os.path.exists(component_log)

                # Verify content in both files
                with open(main_log, 'r') as f:
                    main_content = json.loads(f.read().strip())
                    assert main_content['component'] == 'GalaxyMap'

                with open(component_log, 'r') as f:
                    component_content = json.loads(f.read().strip())
                    assert component_content['component'] == 'GalaxyMap'

    def test_get_debug_logs(self):
        """Test retrieving debug logs"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # First create some log entries
                log_entries = [
                    {
                        'timestamp': '2025-09-07T22:00:00.000Z',
                        'level': 'INFO',
                        'component': 'TestComponent',
                        'message': 'Test message 1',
                        'userAgent': 'TestAgent',
                        'url': 'http://test.com'
                    },
                    {
                        'timestamp': '2025-09-07T22:01:00.000Z',
                        'level': 'ERROR',
                        'component': 'TestComponent',
                        'message': 'Test error',
                        'userAgent': 'TestAgent',
                        'url': 'http://test.com'
                    }
                ]

                for entry in log_entries:
                    client.post('/api/debug/log', json=entry)

                # Now retrieve logs
                response = client.get('/api/debug/logs')
                assert response.status_code == 200

                response_data = json.loads(response.data)
                assert 'logs' in response_data
                assert 'count' in response_data
                assert response_data['count'] == 2
                assert len(response_data['logs']) == 2

                # Verify log content
                logs = response_data['logs']
                assert logs[0]['message'] == 'Test message 1'
                assert logs[1]['message'] == 'Test error'

    def test_get_debug_logs_empty(self):
        """Test retrieving debug logs when no logs exist"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                response = client.get('/api/debug/logs')
                assert response.status_code == 200

                response_data = json.loads(response.data)
                assert response_data['logs'] == []
                assert response_data['count'] == 0
                assert 'message' in response_data

    def test_clear_debug_logs(self):
        """Test clearing debug log files"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # First create some log entries
                log_data = {
                    'timestamp': '2025-09-07T22:00:00.000Z',
                    'level': 'INFO',
                    'component': 'TestComponent',
                    'message': 'Test message',
                    'userAgent': 'TestAgent',
                    'url': 'http://test.com'
                }

                client.post('/api/debug/log', json=log_data)

                # Verify log file exists
                log_file = os.path.join(self.temp_dir, 'galaxy-debug.log')
                assert os.path.exists(log_file)

                # Clear logs
                response = client.post('/api/debug/clear')
                assert response.status_code == 200

                response_data = json.loads(response.data)
                assert response_data['success'] is True
                assert 'cleared_files' in response_data

                # Verify log file is gone
                assert not os.path.exists(log_file)

    def test_get_debug_stats(self):
        """Test getting debug logging statistics"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # Create some test log entries
                log_data = {
                    'timestamp': '2025-09-07T22:00:00.000Z',
                    'level': 'INFO',
                    'component': 'GalaxyMap',
                    'message': 'Test message',
                    'userAgent': 'TestAgent',
                    'url': 'http://test.com'
                }

                client.post('/api/debug/log', json=log_data)

                # Get stats
                response = client.get('/api/debug/stats')
                assert response.status_code == 200

                response_data = json.loads(response.data)
                assert 'log_directory' in response_data
                assert 'files' in response_data
                assert 'total_entries' in response_data

                # Verify stats content
                assert response_data['total_entries'] == 2  # main log + component log
                assert 'galaxy-debug.log' in response_data['files']
                assert 'galaxymap-debug.log' in response_data['files']

    def test_log_file_rotation(self):
        """Test that log files don't grow indefinitely"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # Create many log entries
                for i in range(150):  # More than typical buffer size
                    log_data = {
                        'timestamp': f'2025-09-07T22:{i:02d}:00.000Z',
                        'level': 'INFO',
                        'component': 'TestComponent',
                        'message': f'Test message {i}',
                        'userAgent': 'TestAgent',
                        'url': 'http://test.com'
                    }
                    client.post('/api/debug/log', json=log_data)

                # Verify log file exists and has reasonable size
                log_file = os.path.join(self.temp_dir, 'galaxy-debug.log')
                assert os.path.exists(log_file)

                file_size = os.path.getsize(log_file)
                # File should exist but not be enormous (under 50KB for this test)
                assert file_size > 0
                assert file_size < 50000

    def test_concurrent_log_writing(self):
        """Test concurrent log writing doesn't cause issues"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # Simulate concurrent requests
                import threading
                import time

                results = []
                errors = []

                def make_log_request(index):
                    try:
                        log_data = {
                            'timestamp': f'2025-09-07T22:{index:02d}:00.000Z',
                            'level': 'INFO',
                            'component': 'TestComponent',
                            'message': f'Concurrent message {index}',
                            'userAgent': 'TestAgent',
                            'url': 'http://test.com'
                        }
                        response = client.post('/api/debug/log', json=log_data)
                        results.append(response.status_code)
                    except Exception as e:
                        errors.append(str(e))

                # Create multiple threads
                threads = []
                for i in range(10):
                    thread = threading.Thread(target=make_log_request, args=(i,))
                    threads.append(thread)

                # Start all threads
                for thread in threads:
                    thread.start()
                    time.sleep(0.01)  # Small delay to create concurrency

                # Wait for all threads
                for thread in threads:
                    thread.join()

                # Verify all requests succeeded
                assert len(results) == 10
                assert all(status == 200 for status in results)
                assert len(errors) == 0

                # Verify log file contains all entries
                log_file = os.path.join(self.temp_dir, 'galaxy-debug.log')
                assert os.path.exists(log_file)

                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    assert len(lines) == 10  # Should have 10 log entries

    def test_log_data_integrity(self):
        """Test that log data integrity is maintained"""
        with patch('backend.routes.debug.DEBUG_LOG_DIR', self.temp_dir):
            from backend.app import create_app

            app = create_app('testing')

            with app.test_client() as client:
                # Test with complex data structures
                complex_data = {
                    'nested': {
                        'array': [1, 2, {'deep': 'value'}],
                        'object': {'key': 'value'},
                        'null': None,
                        'boolean': True,
                        'number': 42
                    },
                    'special_chars': 'Test with "quotes" and \'apostrophes\'',
                    'unicode': 'Test with émojis 🌌 and spëcial chärs'
                }

                log_data = {
                    'timestamp': '2025-09-07T22:00:00.000Z',
                    'level': 'INFO',
                    'component': 'TestComponent',
                    'message': 'Complex data test',
                    'data': complex_data,
                    'userAgent': 'TestAgent',
                    'url': 'http://test.com'
                }

                response = client.post('/api/debug/log', json=log_data)
                assert response.status_code == 200

                # Verify data was written correctly
                log_file = os.path.join(self.temp_dir, 'galaxy-debug.log')
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    log_entry = json.loads(content)

                    assert log_entry['data']['nested']['array'][2]['deep'] == 'value'
                    assert log_entry['data']['special_chars'] == complex_data['special_chars']
                    assert log_entry['data']['unicode'] == complex_data['unicode']


if __name__ == '__main__':
    pytest.main([__file__])

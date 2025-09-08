"""
Debug Logging Routes

This module provides endpoints for debug logging from the frontend.
Logs are written to files on the server for analysis and troubleshooting.
"""

import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

debug_bp = Blueprint('debug', __name__, url_prefix='/api')

# Debug log directory
DEBUG_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug-logs')

# Ensure debug log directory exists
os.makedirs(DEBUG_LOG_DIR, exist_ok=True)

@debug_bp.route('/debug/log', methods=['POST'])
def log_debug_entry():
    """
    Receive and store debug log entries from frontend

    This endpoint accepts debug log entries from the frontend and writes them
    to a file on the server for later analysis.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['timestamp', 'level', 'component', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create log entry
        log_entry = {
            'timestamp': data['timestamp'],
            'level': data['level'],
            'component': data['component'],
            'message': data['message'],
            'data': data.get('data'),
            'userAgent': data.get('userAgent', 'Unknown'),
            'url': data.get('url', 'Unknown'),
            'server_received': datetime.now().isoformat()
        }

        # Write to log file
        log_file_path = os.path.join(DEBUG_LOG_DIR, 'galaxy-debug.log')
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        # Also write to component-specific log if it's a major component
        if data['component'] in ['GalaxyMap', 'Dashboard', 'API']:
            component_log_path = os.path.join(DEBUG_LOG_DIR, f"{data['component'].lower()}-debug.log")
            with open(component_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        return jsonify({'success': True, 'message': 'Debug log entry stored'})

    except Exception as e:
        print(f"Error writing debug log: {str(e)}")
        return jsonify({'error': 'Failed to write debug log', 'details': str(e)}), 500

@debug_bp.route('/debug/logs', methods=['GET'])
def get_debug_logs():
    """
    Retrieve debug logs for analysis

    Returns the contents of the debug log file.
    """
    try:
        log_file_path = os.path.join(DEBUG_LOG_DIR, 'galaxy-debug.log')

        if not os.path.exists(log_file_path):
            return jsonify({'logs': [], 'message': 'No debug logs found'})

        logs = []
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue

        return jsonify({
            'logs': logs,
            'count': len(logs),
            'file_path': log_file_path
        })

    except Exception as e:
        print(f"Error reading debug logs: {str(e)}")
        return jsonify({'error': 'Failed to read debug logs', 'details': str(e)}), 500

@debug_bp.route('/debug/clear', methods=['POST'])
def clear_debug_logs():
    """
    Clear all debug log files
    """
    try:
        log_files = [
            'galaxy-debug.log',
            'galaxymap-debug.log',
            'dashboard-debug.log',
            'api-debug.log'
        ]

        cleared_files = []
        for log_file in log_files:
            file_path = os.path.join(DEBUG_LOG_DIR, log_file)
            if os.path.exists(file_path):
                os.remove(file_path)
                cleared_files.append(log_file)

        return jsonify({
            'success': True,
            'message': f'Cleared {len(cleared_files)} log files',
            'cleared_files': cleared_files
        })

    except Exception as e:
        print(f"Error clearing debug logs: {str(e)}")
        return jsonify({'error': 'Failed to clear debug logs', 'details': str(e)}), 500

@debug_bp.route('/debug/stats', methods=['GET'])
def get_debug_stats():
    """
    Get statistics about debug logging
    """
    try:
        stats = {
            'log_directory': DEBUG_LOG_DIR,
            'files': {},
            'total_entries': 0
        }

        log_files = [
            'galaxy-debug.log',
            'galaxymap-debug.log',
            'dashboard-debug.log',
            'api-debug.log'
        ]

        for log_file in log_files:
            file_path = os.path.join(DEBUG_LOG_DIR, log_file)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = sum(1 for line in f if line.strip())
                stats['files'][log_file] = {
                    'exists': True,
                    'entries': lines,
                    'size_bytes': os.path.getsize(file_path)
                }
                stats['total_entries'] += lines
            else:
                stats['files'][log_file] = {
                    'exists': False,
                    'entries': 0,
                    'size_bytes': 0
                }

        return jsonify(stats)

    except Exception as e:
        print(f"Error getting debug stats: {str(e)}")
        return jsonify({'error': 'Failed to get debug stats', 'details': str(e)}), 500

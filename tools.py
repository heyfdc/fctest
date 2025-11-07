<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Directory Explorer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }

        .breadcrumb {
            background: #f8f9fa;
            padding: 15px 30px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }

        .breadcrumb-item {
            color: #667eea;
            cursor: pointer;
            padding: 5px 10px;
            border-radius: 5px;
            transition: background 0.2s;
        }

        .breadcrumb-item:hover {
            background: #e9ecef;
        }

        .breadcrumb-separator {
            color: #6c757d;
        }

        .controls {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
            text-decoration: none;
            display: inline-block;
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-secondary:hover {
            background: #5a6268;
        }

        .search-box {
            flex: 1;
            min-width: 200px;
            padding: 10px 15px;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.2s;
        }

        .search-box:focus {
            outline: none;
            border-color: #667eea;
        }

        .content {
            padding: 30px;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }

        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }

        .file-list {
            display: grid;
            gap: 10px;
        }

        .file-item {
            display: flex;
            align-items: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            transition: all 0.2s;
            cursor: pointer;
            border: 2px solid transparent;
        }

        .file-item:hover {
            background: #e9ecef;
            border-color: #667eea;
            transform: translateX(5px);
        }

        .file-icon {
            width: 40px;
            height: 40px;
            margin-right: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }

        .file-info {
            flex: 1;
            min-width: 0;
        }

        .file-name {
            font-weight: 600;
            color: #212529;
            margin-bottom: 5px;
            word-break: break-all;
        }

        .file-details {
            font-size: 12px;
            color: #6c757d;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .file-actions {
            display: flex;
            gap: 10px;
        }

        .btn-small {
            padding: 6px 12px;
            font-size: 12px;
        }

        .stats {
            background: #f8f9fa;
            padding: 15px 30px;
            border-top: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
            color: #6c757d;
            font-size: 14px;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }

        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📁 File Directory Explorer</h1>
            <p>Browse and explore your file system</p>
        </div>

        <div class="breadcrumb" id="breadcrumb">
            <span class="breadcrumb-item" onclick="navigateTo('/')">Home</span>
        </div>

        <div class="controls">
            <button class="btn btn-primary" onclick="navigateTo('/')">🏠 Root</button>
            <button class="btn btn-secondary" onclick="goBack()">← Back</button>
            <button class="btn btn-secondary" onclick="refreshCurrent()">🔄 Refresh</button>
            <input type="text" class="search-box" id="searchBox" placeholder="Search files and folders..." onkeyup="filterFiles()">
        </div>

        <div class="content">
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p style="margin-top: 15px;">Loading directory contents...</p>
            </div>
            <div id="error" class="error" style="display: none;"></div>
            <div id="fileList" class="file-list" style="display: none;"></div>
        </div>

        <div class="stats" id="stats">
            <span>Total items: <strong id="totalCount">0</strong></span>
            <span>Files: <strong id="fileCount">0</strong></span>
            <span>Folders: <strong id="folderCount">0</strong></span>
        </div>
    </div>

    <script>
        let currentPath = '/';
        let allFiles = [];

        // Initialize
        window.onload = function() {
            // Get the current path from the URL
            const urlPath = window.location.pathname;
            const basePath = urlPath === '/index.html' || urlPath.endsWith('/index.html') 
                ? '/' 
                : urlPath.replace('/index.html', '').replace(/\/$/, '') || '/';
            loadDirectory(basePath);
        };

        // Load directory contents
        async function loadDirectory(path) {
            currentPath = path;
            updateBreadcrumb(path);
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('error').style.display = 'none';
            document.getElementById('fileList').style.display = 'none';

            try {
                // For local file system, we'll use a simple API endpoint
                // In a real implementation, you'd have a backend API
                const response = await fetch(`/api/list?path=${encodeURIComponent(path)}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                allFiles = data.files || [];
                displayFiles(allFiles);
                updateStats(allFiles);
            } catch (error) {
                // Fallback: try to list files using directory listing
                try {
                    const response = await fetch(path === '/' ? '/' : path);
                    const html = await response.text();
                    parseDirectoryListing(html, path);
                } catch (e) {
                    showError(`Failed to load directory: ${error.message}`);
                }
            }
        }

        // Parse directory listing from HTML (fallback)
        function parseDirectoryListing(html, path) {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const links = doc.querySelectorAll('a');
            const files = [];

            links.forEach(link => {
                const href = link.getAttribute('href');
                const text = link.textContent.trim();
                
                if (href && text && !text.startsWith('Parent Directory') && !text.startsWith('..')) {
                    // Build full path
                    let fullPath;
                    if (path === '/') {
                        fullPath = href.startsWith('/') ? href : '/' + href;
                    } else {
                        fullPath = path.endsWith('/') ? path + href : path + '/' + href;
                    }
                    fullPath = fullPath.replace('//', '/');
                    
                    const isDirectory = href.endsWith('/') || text.endsWith('/');
                    
                    files.push({
                        name: text.replace('/', ''),
                        path: fullPath,
                        type: isDirectory ? 'directory' : 'file',
                        size: null,
                        modified: null
                    });
                }
            });

            allFiles = files;
            displayFiles(files);
            updateStats(files);
        }

        // Display files
        function displayFiles(files) {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('fileList').style.display = 'block';

            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';

            if (files.length === 0) {
                fileList.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📂</div>
                        <h3>This directory is empty</h3>
                    </div>
                `;
                return;
            }

            // Sort: directories first, then files
            const sorted = [...files].sort((a, b) => {
                if (a.type === 'directory' && b.type !== 'directory') return -1;
                if (a.type !== 'directory' && b.type === 'directory') return 1;
                return a.name.localeCompare(b.name);
            });

            sorted.forEach(file => {
                const item = document.createElement('div');
                item.className = 'file-item';
                
                const icon = file.type === 'directory' ? '📁' : getFileIcon(file.name);
                const size = file.size ? formatSize(file.size) : '-';
                const modified = file.modified || '-';

                item.innerHTML = `
                    <div class="file-icon">${icon}</div>
                    <div class="file-info" onclick="${file.type === 'directory' ? `navigateTo('${file.path}')` : `openFile('${file.path}')`}">
                        <div class="file-name">${escapeHtml(file.name)}</div>
                        <div class="file-details">
                            <span>Type: ${file.type}</span>
                            <span>Size: ${size}</span>
                            <span>Modified: ${modified}</span>
                        </div>
                    </div>
                    <div class="file-actions">
                        ${file.type === 'directory' 
                            ? `<button class="btn btn-primary btn-small" onclick="navigateTo('${file.path}')">Open</button>`
                            : `<button class="btn btn-primary btn-small" onclick="openFile('${file.path}')">Open</button>
                               <button class="btn btn-secondary btn-small" onclick="downloadFile('${file.path}')">Download</button>`
                        }
                    </div>
                `;

                fileList.appendChild(item);
            });
        }

        // Get file icon based on extension
        function getFileIcon(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            const icons = {
                'py': '🐍', 'js': '📜', 'html': '🌐', 'css': '🎨', 'json': '📋',
                'txt': '📄', 'md': '📝', 'pdf': '📕', 'zip': '📦', 'jpg': '🖼️',
                'png': '🖼️', 'gif': '🖼️', 'mp4': '🎬', 'mp3': '🎵'
            };
            return icons[ext] || '📄';
        }

        // Format file size
        function formatSize(bytes) {
            if (!bytes || bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }

        // Update breadcrumb
        function updateBreadcrumb(path) {
            const breadcrumb = document.getElementById('breadcrumb');
            breadcrumb.innerHTML = '';

            const parts = path.split('/').filter(p => p);
            breadcrumb.innerHTML = '<span class="breadcrumb-item" onclick="navigateTo(\'/\')">Home</span>';

            let current = '';
            parts.forEach((part, index) => {
                current += '/' + part;
                breadcrumb.innerHTML += '<span class="breadcrumb-separator">/</span>';
                breadcrumb.innerHTML += `<span class="breadcrumb-item" onclick="navigateTo('${current}')">${escapeHtml(part)}</span>`;
            });
        }

        // Navigate to directory
        function navigateTo(path) {
            // Ensure path starts with /
            if (!path.startsWith('/')) {
                path = '/' + path;
            }
            // Normalize path
            path = path.replace(/\/+/g, '/');
            loadDirectory(path);
        }

        // Go back
        function goBack() {
            if (currentPath === '/') return;
            const parts = currentPath.split('/').filter(p => p);
            parts.pop();
            const newPath = parts.length > 0 ? '/' + parts.join('/') : '/';
            navigateTo(newPath);
        }

        // Refresh current directory
        function refreshCurrent() {
            loadDirectory(currentPath);
        }

        // Open file
        function openFile(path) {
            window.open(path, '_blank');
        }

        // Download file
        function downloadFile(path) {
            const link = document.createElement('a');
            link.href = path;
            link.download = path.split('/').pop();
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        // Filter files
        function filterFiles() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            if (!searchTerm) {
                displayFiles(allFiles);
                return;
            }

            const filtered = allFiles.filter(file => 
                file.name.toLowerCase().includes(searchTerm)
            );
            displayFiles(filtered);
        }

        // Update statistics
        function updateStats(files) {
            const total = files.length;
            const fileCount = files.filter(f => f.type === 'file').length;
            const folderCount = files.filter(f => f.type === 'directory').length;

            document.getElementById('totalCount').textContent = total;
            document.getElementById('fileCount').textContent = fileCount;
            document.getElementById('folderCount').textContent = folderCount;
        }

        // Show error
        function showError(message) {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error').style.display = 'block';
            document.getElementById('error').textContent = message;
        }

        // Escape HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>


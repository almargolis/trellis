# Trellis - Production Deployment Guide

This guide uses `<site-name>` as a placeholder for your site's directory name (e.g., `tmih`, `myblog`, etc.). A single server can host multiple Trellis installations for different sites.

## Server Setup

### 1. Clone Repository
```bash
cd /var/www
sudo git clone <your-repository-url> <site-name>
cd <site-name>
```

Example for a site named "tmih":
```bash
cd /var/www
sudo git clone <your-repository-url> tmih
cd tmih
```

### 2. Install Trellis
```bash
# Create virtual environment
sudo python3 -m venv venv
sudo chown -R www-data:www-data venv

# Install Trellis (choose one method):

# Option A: Clone and install from GitHub
sudo -u www-data git clone https://github.com/almargolis/trellis.git
sudo -u www-data venv/bin/pip install -e ./trellis

# Option B: Install from PyPI (when available)
# sudo -u www-data venv/bin/pip install trellis-cms

# Install any additional dependencies
sudo -u www-data venv/bin/pip install python-dotenv
```

### 3. Setup Data Directory
The application needs a writable directory outside the git repository for:
- SQLite database (needs write access for db + journal files)
- Content markdown files (needs write access for editing)

Run the setup script:
```bash
sudo ./setup_production.sh /var/www/<site-name> /var/www/<site-name>_data
```

Or manually:
```bash
# Create data directory
sudo mkdir -p /var/www/<site-name>_data/content
sudo chown -R www-data:www-data /var/www/<site-name>_data
sudo chmod -R 775 /var/www/<site-name>_data

# Copy existing content
sudo cp -r content/* /var/www/<site-name>_data/content/
```

### 4. Configure Environment
Create or update `.env` file:
```bash
sudo nano /var/www/<site-name>/.env
```

Required variables:
```
SECRET_KEY=your-secret-key-here-change-this
SITE_NAME=Your Site Name
SITE_AUTHOR=Your Name
DATA_DIR=/var/www/<site-name>_data
CONTENT_DIR=/var/www/<site-name>_data/content
GITLAB_REPO_PATH=/var/www/<site-name>
```

### 5. Initialize Database
```bash
cd /var/www/<site-name>
sudo -u www-data venv/bin/trellis-init-db
```

### 6. Initialize Search Index
```bash
sudo -u www-data venv/bin/trellis-search --rebuild
```

This builds the full-text search index from your content.

### 7. Create WSGI File
Create `trellis.wsgi` in your site directory:
```bash
sudo nano /var/www/<site-name>/trellis.wsgi
```

Complete WSGI file contents:
```python
#!/usr/bin/env python3
"""
WSGI configuration for Trellis site deployment.
"""
import sys
import os

# Set the project directory
project_home = '/var/www/<site-name>'

# Change to project directory to find .env file
os.chdir(project_home)

# Activate virtual environment
activate_this = os.path.join(project_home, 'venv', 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import and create the Flask application
from trellis import create_app
application = create_app()
```

**Important**: Replace `<site-name>` with your actual site directory name (e.g., `tmih`).

### 8. Set Permissions
```bash
sudo chown -R www-data:www-data /var/www/<site-name>
sudo chmod -R 755 /var/www/<site-name>
sudo chmod -R 775 /var/www/<site-name>_data
```

### 9. SELinux (if enabled)
```bash
sudo chcon -R -t httpd_sys_rw_content_t /var/www/<site-name>_data
sudo chcon -R -t httpd_sys_content_t /var/www/<site-name>
sudo setsebool -P httpd_can_network_connect_db 1
```

### 10. Apache Configuration
Create vhost config at `/etc/apache2/sites-available/<site-name>.conf`:
```apache
<VirtualHost *:80>
    ServerName yourdomain.com

    WSGIDaemonProcess <site-name> user=www-data group=www-data threads=5 python-home=/var/www/<site-name>/venv
    WSGIScriptAlias / /var/www/<site-name>/trellis.wsgi

    # Serve static files directly with Apache (more efficient)
    Alias /static /var/www/<site-name>/trellis/trellis/static
    <Directory /var/www/<site-name>/trellis/trellis/static>
        Require all granted
    </Directory>

    # Serve page-specific assets from content directory
    Alias /assets /var/www/<site-name>_data/content
    <Directory /var/www/<site-name>_data/content>
        Require all granted
    </Directory>

    <Directory /var/www/<site-name>>
        WSGIProcessGroup <site-name>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/<site-name>_error.log
    CustomLog ${APACHE_LOG_DIR}/<site-name>_access.log combined
</VirtualHost>
```

Enable and restart:
```bash
sudo a2ensite <site-name>
sudo systemctl restart apache2
```

## Directory Structure

```
/var/www/<site-name>/          # Git repository (read-only in production)
├── app/
├── content/                  # Template content (don't edit here)
├── venv/
├── .env                      # Configuration
└── trellis.wsgi

/var/www/<site-name>_data/     # Writable data directory
├── trellis_admin.db                   # SQLite database
├── trellis_admin.db-journal          # Database journal
└── content/                 # Actual content files (editable)
    ├── essays/
    ├── projects/
    └── notes/
```

## Updating the Application

```bash
cd /var/www/<site-name>
sudo -u www-data git pull
sudo -u www-data venv/bin/pip install -e .
sudo systemctl restart apache2
```

## Troubleshooting

### Database Permission Errors
```bash
sudo chown www-data:www-data /var/www/<site-name>_data/trellis_admin.db*
sudo chmod 664 /var/www/<site-name>_data/trellis_admin.db*
sudo chmod 775 /var/www/<site-name>_data
```

### Content Save Errors
```bash
sudo chown -R www-data:www-data /var/www/<site-name>_data/content
sudo chmod -R 664 /var/www/<site-name>_data/content/*/*.md
sudo chmod -R 775 /var/www/<site-name>_data/content/*/
```

### Check Logs
```bash
sudo tail -f /var/log/apache2/<site-name>_error.log
```

## Security Notes

1. **Change default admin password** immediately after deployment
2. **Set strong SECRET_KEY** in .env
3. **Use HTTPS** in production (setup Let's Encrypt)
4. **Restrict .env permissions**: `sudo chmod 600 /var/www/<site-name>/.env`
5. **Regular backups** of `/var/www/<site-name>_data/`

# Deployment

Production deployment guide for Trellis CMS.

## Overview

Trellis can be deployed on any server that supports Python 3.9+ and either Apache/WSGI or Nginx/uWSGI.

## Quick Deployment Checklist

- [ ] Python 3.9+ installed
- [ ] Web server (Apache or Nginx)
- [ ] WSGI server (mod_wsgi or uWSGI)
- [ ] SSL certificate configured
- [ ] Firewall rules configured
- [ ] Domain name pointed to server

## Recommended Architecture

**Production Setup:**
```
/var/www/mysite/          # Git repository (code, read-only)
  .env                    # Configuration
  trellis.wsgi           # WSGI entry point
  venv/                  # Python virtual environment

/var/www/mysite_data/    # Data directory (writable)
  trellis_admin.db       # User database
  trellis_content.db     # Content metadata cache
  search_index/          # Whoosh search index
  content/               # Markdown files
    blog/
    projects/
```

**Why separate directories?**
- Code directory is owned by deployment user (read-only for www-data)
- Data directory is owned by www-data (writable by web server)
- Enables clean git pulls without permission issues
- Databases can be written by web server

## Apache + mod_wsgi Deployment

### Install Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install apache2 libapache2-mod-wsgi-py3
sudo apt install git
```

**RHEL/CentOS:**
```bash
sudo dnf install python3 python3-pip
sudo dnf install httpd mod_wsgi
sudo dnf install git
```

### Create Deployment User

```bash
# Optional: Create deployment user separate from www-data
sudo adduser --system --group deploy
sudo usermod -aG www-data deploy
```

### Clone Repository

```bash
cd /var/www
sudo git clone https://github.com/yourusername/your-site.git mysite
cd mysite
```

### Install Trellis

```bash
# Create virtual environment
sudo python3 -m venv venv
sudo chown -R www-data:www-data venv

# Activate and install
sudo -u www-data venv/bin/pip install --upgrade pip

# Install dependencies from GitHub (temporary, until on PyPI)
sudo -u www-data venv/bin/pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdflask
sudo -u www-data venv/bin/pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdcomments

# Install Trellis
sudo -u www-data venv/bin/pip install trellis-cms
```

Or install from local source:
```bash
# Install dependencies from GitHub
sudo -u www-data venv/bin/pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdflask
sudo -u www-data venv/bin/pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdcomments

# Install Trellis in editable mode
sudo -u www-data venv/bin/pip install -e /path/to/trellis
```

!!! note "Future Simplified Installation"
    Once qdflask and qdcomments are published to PyPI, installation will be:
    ```bash
    sudo -u www-data venv/bin/pip install trellis-cms
    ```

### Setup Data Directory

Use the included script:
```bash
sudo ./setup_production.sh /var/www/mysite /var/www/mysite_data
```

Or manually:
```bash
sudo mkdir -p /var/www/mysite_data/content
sudo chown -R www-data:www-data /var/www/mysite_data
sudo chmod -R 775 /var/www/mysite_data
```

### Configure Environment

Create `/var/www/mysite/.env`:

```bash
# Security
SECRET_KEY=your-secret-key-change-this-to-something-random

# Site Information
SITE_NAME=My Digital Garden
SITE_AUTHOR=Your Name

# Paths
DATA_DIR=/var/www/mysite_data
CONTENT_DIR=/var/www/mysite_data/content

# Git Integration
GITLAB_REPO_PATH=/var/www/mysite_data

# Optional: Email (for commenting system)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Optional: Deferred indexing for high-traffic sites
# TRELLIS_DEFERRED_INDEXING=true
```

Generate a secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Secure the file:
```bash
sudo chmod 600 /var/www/mysite/.env
sudo chown www-data:www-data /var/www/mysite/.env
```

### Initialize Database

```bash
cd /var/www/mysite
sudo -u www-data venv/bin/trellis-init-db
```

Default credentials: `admin` / `admin` (change immediately!)

### Copy Content

```bash
# Copy your content to data directory
sudo cp -r content/* /var/www/mysite_data/content/
sudo chown -R www-data:www-data /var/www/mysite_data/content
```

Or sync from another location:
```bash
sudo rsync -av /path/to/your/content/ /var/www/mysite_data/content/
sudo chown -R www-data:www-data /var/www/mysite_data/content
```

### Build Search Index

```bash
sudo -u www-data venv/bin/trellis-search --rebuild
```

### Create WSGI File

Create `/var/www/mysite/trellis.wsgi`:

```python
#!/usr/bin/env python3
import sys
import os

# Project directory
project_home = '/var/www/mysite'

# Change to project directory
os.chdir(project_home)

# Activate virtual environment
activate_this = os.path.join(project_home, 'venv', 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Create Flask application
from trellis import create_app
application = create_app()
```

### Configure Apache

Create `/etc/apache2/sites-available/mysite.conf`:

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com

    # Redirect to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/yourdomain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/yourdomain.com/privkey.pem

    # WSGI Configuration
    WSGIDaemonProcess mysite user=www-data group=www-data threads=5 \
        python-home=/var/www/mysite/venv \
        python-path=/var/www/mysite
    WSGIScriptAlias / /var/www/mysite/trellis.wsgi
    WSGIProcessGroup mysite
    WSGIApplicationGroup %{GLOBAL}

    # Static files
    Alias /static /var/www/mysite/venv/lib/python3.11/site-packages/trellis/static
    <Directory /var/www/mysite/venv/lib/python3.11/site-packages/trellis/static>
        Require all granted
    </Directory>

    # Main application directory
    <Directory /var/www/mysite>
        Require all granted
    </Directory>

    # Security headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"

    # Logging
    ErrorLog ${APACHE_LOG_DIR}/mysite_error.log
    CustomLog ${APACHE_LOG_DIR}/mysite_access.log combined
</VirtualHost>
```

Enable site and modules:
```bash
sudo a2enmod ssl rewrite headers wsgi
sudo a2ensite mysite
sudo apache2ctl configtest
sudo systemctl restart apache2
```

## SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-apache

# Obtain certificate
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured via cron
sudo certbot renew --dry-run
```

## Nginx + uWSGI Deployment

### Install Prerequisites

```bash
sudo apt install nginx uwsgi uwsgi-plugin-python3
```

### Install Trellis

Same as Apache deployment above.

### Configure uWSGI

Create `/etc/uwsgi/apps-available/mysite.ini`:

```ini
[uwsgi]
project = mysite
base = /var/www

# Flask application
chdir = %(base)/%(project)
module = trellis:create_app()
callable = application

# Virtual environment
home = %(base)/%(project)/venv

# Process management
master = true
processes = 4
threads = 2
uid = www-data
gid = www-data

# Socket
socket = /run/uwsgi/%(project).sock
chmod-socket = 660
vacuum = true

# Logging
logto = /var/log/uwsgi/%(project).log

# Environment
env = DATA_DIR=/var/www/%(project)_data
```

Enable:
```bash
sudo ln -s /etc/uwsgi/apps-available/mysite.ini /etc/uwsgi/apps-enabled/
sudo systemctl restart uwsgi
```

### Configure Nginx

Create `/etc/nginx/sites-available/mysite`:

```nginx
upstream mysite_app {
    server unix:/run/uwsgi/mysite.sock;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static {
        alias /var/www/mysite/venv/lib/python3.11/site-packages/trellis/static;
        expires 30d;
    }

    # Application
    location / {
        include uwsgi_params;
        uwsgi_pass mysite_app;
    }

    # Logging
    access_log /var/log/nginx/mysite_access.log;
    error_log /var/log/nginx/mysite_error.log;
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/mysite /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Systemd Service (Alternative)

For running with Gunicorn:

Create `/etc/systemd/system/trellis-mysite.service`:

```ini
[Unit]
Description=Trellis CMS - My Site
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/mysite
Environment="DATA_DIR=/var/www/mysite_data"
EnvironmentFile=/var/www/mysite/.env
ExecStart=/var/www/mysite/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/trellis-mysite.sock \
    --access-logfile /var/log/trellis/mysite-access.log \
    --error-logfile /var/log/trellis/mysite-error.log \
    "trellis:create_app()"

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trellis-mysite
sudo systemctl start trellis-mysite
sudo systemctl status trellis-mysite
```

## Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 'Apache Full'
# or
sudo ufw allow 'Nginx Full'

# firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Post-Deployment Tasks

### Change Admin Password

1. Visit `/auth/login`
2. Login with `admin` / `admin`
3. Go to profile and change password immediately

### Create Additional Users

Visit `/auth/users` (admin only) to create editor accounts.

### Setup Backups

See [Backup Strategy](../maintenance/backup.md) for detailed instructions.

Quick setup:
```bash
# Create backup script
sudo cp /var/www/mysite/docs/backup-trellis.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/backup-trellis.sh

# Schedule daily backups
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-trellis.sh
```

### Setup Monitoring

Install monitoring tools:
```bash
sudo apt install monit
```

Configure Monit for Trellis:
```
check process apache2 with pidfile /var/run/apache2/apache2.pid
  start program = "/bin/systemctl start apache2"
  stop program = "/bin/systemctl stop apache2"
```

## Updating Production

```bash
cd /var/www/mysite

# Backup first
sudo /usr/local/bin/backup-trellis.sh

# Pull latest code
sudo -u deploy git pull origin main

# Update dependencies
sudo -u www-data venv/bin/pip install --upgrade trellis-cms

# Rebuild indexes
sudo -u www-data venv/bin/trellis-search --rebuild

# Restart web server
sudo systemctl restart apache2
# or
sudo systemctl restart nginx
sudo systemctl restart uwsgi
```

## Troubleshooting

### 500 Internal Server Error

Check logs:
```bash
sudo tail -f /var/log/apache2/mysite_error.log
# or
sudo tail -f /var/log/nginx/mysite_error.log
```

Common issues:
- Wrong DATA_DIR path
- Database permissions
- Missing .env file
- Python import errors

### Permission Denied

```bash
# Fix data directory permissions
sudo chown -R www-data:www-data /var/www/mysite_data
sudo chmod -R 775 /var/www/mysite_data

# Fix database permissions
sudo chmod 664 /var/www/mysite_data/*.db
```

### Static Files Not Loading

Check static files path in Apache/Nginx config matches actual location:
```bash
find /var/www/mysite/venv -name "static" -type d
```

Update config with correct path.

### Database Locked

```bash
# Check for stale processes
ps aux | grep trellis

# Check database locks
fuser /var/www/mysite_data/trellis_admin.db
```

## Security Hardening

### File Permissions

```bash
# Code directory (read-only for www-data)
sudo chown -R deploy:www-data /var/www/mysite
sudo chmod -R 750 /var/www/mysite

# Data directory (writable by www-data)
sudo chown -R www-data:www-data /var/www/mysite_data
sudo chmod -R 770 /var/www/mysite_data

# Secure .env
sudo chmod 600 /var/www/mysite/.env
sudo chown www-data:www-data /var/www/mysite/.env
```

### Disable Debug Mode

Ensure `.env` has:
```bash
DEBUG=False
```

Never run with `DEBUG=True` in production!

### Rate Limiting

Install mod_evasive:
```bash
sudo apt install libapache2-mod-evasive
```

Configure in Apache:
```apache
<IfModule mod_evasive20.c>
    DOSHashTableSize 3097
    DOSPageCount 5
    DOSSiteCount 50
    DOSPageInterval 1
    DOSSiteInterval 1
    DOSBlockingPeriod 60
</IfModule>
```

### Fail2Ban

```bash
sudo apt install fail2ban

# Create filter for Trellis
sudo nano /etc/fail2ban/filter.d/trellis.conf
```

Add:
```ini
[Definition]
failregex = Failed login attempt.*<HOST>
ignoreregex =
```

## Performance Optimization

### Enable Caching

In Apache config:
```apache
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType text/javascript "access plus 1 month"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpg "access plus 1 year"
</IfModule>
```

### Compression

```apache
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript
</IfModule>
```

### Database Optimization

```bash
# Vacuum database periodically
sqlite3 /var/www/mysite_data/trellis_admin.db "VACUUM;"
sqlite3 /var/www/mysite_data/trellis_content.db "VACUUM;"
```

## Next Steps

- **[Backup Strategy](../maintenance/backup.md)** - Set up backups
- **[Search Indexing](../maintenance/indexing.md)** - Manage indexes
- **[Architecture](architecture.md)** - Understand the system

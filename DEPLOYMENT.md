# TMIH Flask - Production Deployment Guide

## Server Setup

### 1. Clone Repository
```bash
cd /var/www
sudo git clone https://gitlab.com/BoutiqueEngineering/tmih_flask.git
cd tmih_flask
```

### 2. Create Virtual Environment
```bash
sudo python3 -m venv venv
sudo chown -R www-data:www-data venv
sudo -u www-data venv/bin/pip install -r requirements.txt
```

### 3. Setup Data Directory
The application needs a writable directory outside the git repository for:
- SQLite database (needs write access for db + journal files)
- Content markdown files (needs write access for editing)

Run the setup script:
```bash
sudo ./setup_production.sh /var/www/tmih_flask /var/www/tmih_flask_data
```

Or manually:
```bash
# Create data directory
sudo mkdir -p /var/www/tmih_flask_data/content
sudo chown -R www-data:www-data /var/www/tmih_flask_data
sudo chmod -R 775 /var/www/tmih_flask_data

# Copy existing content
sudo cp -r content/* /var/www/tmih_flask_data/content/
```

### 4. Configure Environment
Create or update `.env` file:
```bash
sudo nano /var/www/tmih_flask/.env
```

Required variables:
```
SECRET_KEY=your-secret-key-here-change-this
DATA_DIR=/var/www/tmih_flask_data
CONTENT_DIR=/var/www/tmih_flask_data/content
GITLAB_REPO_PATH=/var/www/tmih_flask
```

### 5. Initialize Database
```bash
cd /var/www/tmih_flask
sudo -u www-data venv/bin/python init_db.py
```

### 6. Update WSGI File
Edit `tmih_flask.wsgi` to match your paths:
```python
project_home = '/var/www/tmih_flask'
```

### 7. Set Permissions
```bash
sudo chown -R www-data:www-data /var/www/tmih_flask
sudo chmod -R 755 /var/www/tmih_flask
sudo chmod -R 775 /var/www/tmih_flask_data
```

### 8. SELinux (if enabled)
```bash
sudo chcon -R -t httpd_sys_rw_content_t /var/www/tmih_flask_data
sudo chcon -R -t httpd_sys_content_t /var/www/tmih_flask
sudo setsebool -P httpd_can_network_connect_db 1
```

### 9. Apache Configuration
Create vhost config at `/etc/apache2/sites-available/tmih_flask.conf`:
```apache
<VirtualHost *:80>
    ServerName yourdomain.com

    WSGIDaemonProcess tmih_flask user=www-data group=www-data threads=5 python-home=/var/www/tmih_flask/venv
    WSGIScriptAlias / /var/www/tmih_flask/tmih_flask.wsgi

    <Directory /var/www/tmih_flask>
        WSGIProcessGroup tmih_flask
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/tmih_flask_error.log
    CustomLog ${APACHE_LOG_DIR}/tmih_flask_access.log combined
</VirtualHost>
```

Enable and restart:
```bash
sudo a2ensite tmih_flask
sudo systemctl restart apache2
```

## Directory Structure

```
/var/www/tmih_flask/          # Git repository (read-only in production)
├── app/
├── content/                  # Template content (don't edit here)
├── venv/
├── .env                      # Configuration
└── tmih_flask.wsgi

/var/www/tmih_flask_data/     # Writable data directory
├── blog.db                   # SQLite database
├── blog.db-journal          # Database journal
└── content/                 # Actual content files (editable)
    ├── essays/
    ├── projects/
    └── notes/
```

## Updating the Application

```bash
cd /var/www/tmih_flask
sudo -u www-data git pull
sudo -u www-data venv/bin/pip install -r requirements.txt
sudo systemctl restart apache2
```

## Troubleshooting

### Database Permission Errors
```bash
sudo chown www-data:www-data /var/www/tmih_flask_data/blog.db*
sudo chmod 664 /var/www/tmih_flask_data/blog.db*
sudo chmod 775 /var/www/tmih_flask_data
```

### Content Save Errors
```bash
sudo chown -R www-data:www-data /var/www/tmih_flask_data/content
sudo chmod -R 664 /var/www/tmih_flask_data/content/*/*.md
sudo chmod -R 775 /var/www/tmih_flask_data/content/*/
```

### Check Logs
```bash
sudo tail -f /var/log/apache2/tmih_flask_error.log
```

## Security Notes

1. **Change default admin password** immediately after deployment
2. **Set strong SECRET_KEY** in .env
3. **Use HTTPS** in production (setup Let's Encrypt)
4. **Restrict .env permissions**: `sudo chmod 600 /var/www/tmih_flask/.env`
5. **Regular backups** of `/var/www/tmih_flask_data/`

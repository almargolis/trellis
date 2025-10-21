#!/bin/bash
# Production deployment setup script
# Run this on your server after deploying the code

set -e

PROJECT_DIR="${1:-/var/www/tmih_flask}"
DATA_DIR="${2:-/var/www/tmih_flask_data}"

echo "==================================="
echo "TMIH Flask Production Setup"
echo "==================================="
echo "Project Dir: $PROJECT_DIR"
echo "Data Dir: $DATA_DIR"
echo ""

# Create data directory with proper permissions
echo "Creating data directory..."
sudo mkdir -p "$DATA_DIR"
sudo chown -R www-data:www-data "$DATA_DIR"
sudo chmod -R 775 "$DATA_DIR"

# Create subdirectories
echo "Creating subdirectories..."
sudo -u www-data mkdir -p "$DATA_DIR/content"

# Copy existing database if it exists
if [ -f "$PROJECT_DIR/blog.db" ]; then
    echo "Migrating existing database..."
    sudo cp "$PROJECT_DIR/blog.db" "$DATA_DIR/blog.db"
    sudo chown www-data:www-data "$DATA_DIR/blog.db"
    sudo chmod 664 "$DATA_DIR/blog.db"
fi

# Copy content if it exists
if [ -d "$PROJECT_DIR/content" ] && [ "$(ls -A $PROJECT_DIR/content)" ]; then
    echo "Copying content files..."
    sudo cp -r "$PROJECT_DIR/content"/* "$DATA_DIR/content/" 2>/dev/null || true
    sudo chown -R www-data:www-data "$DATA_DIR/content"
    sudo chmod -R 664 "$DATA_DIR/content"/*
fi

# Update .env file
echo "Updating .env configuration..."
if [ -f "$PROJECT_DIR/.env" ]; then
    # Add or update DATA_DIR and CONTENT_DIR
    if grep -q "^DATA_DIR=" "$PROJECT_DIR/.env"; then
        sudo sed -i "s|^DATA_DIR=.*|DATA_DIR=$DATA_DIR|" "$PROJECT_DIR/.env"
    else
        echo "DATA_DIR=$DATA_DIR" | sudo tee -a "$PROJECT_DIR/.env" > /dev/null
    fi

    if grep -q "^CONTENT_DIR=" "$PROJECT_DIR/.env"; then
        sudo sed -i "s|^CONTENT_DIR=.*|CONTENT_DIR=$DATA_DIR/content|" "$PROJECT_DIR/.env"
    else
        echo "CONTENT_DIR=$DATA_DIR/content" | sudo tee -a "$PROJECT_DIR/.env" > /dev/null
    fi
else
    echo "Warning: .env file not found at $PROJECT_DIR/.env"
    echo "Please create it with the following variables:"
    echo "DATA_DIR=$DATA_DIR"
    echo "CONTENT_DIR=$DATA_DIR/content"
fi

# Set SELinux context if SELinux is enabled
if command -v getenforce &> /dev/null && [ "$(getenforce)" != "Disabled" ]; then
    echo "Setting SELinux context..."
    sudo chcon -R -t httpd_sys_rw_content_t "$DATA_DIR"
fi

# Restart Apache
echo "Restarting Apache..."
sudo systemctl restart apache2 || sudo systemctl restart httpd || echo "Could not restart Apache - please restart manually"

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo "Data directory: $DATA_DIR"
echo "Database: $DATA_DIR/blog.db"
echo "Content: $DATA_DIR/content/"
echo ""
echo "Permissions set for www-data user"
echo "Please verify your .env file has:"
echo "  DATA_DIR=$DATA_DIR"
echo "  CONTENT_DIR=$DATA_DIR/content"

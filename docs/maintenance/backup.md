# Backup Strategy

Protect your Trellis content with a robust backup approach.

## What Needs Backing Up?

Your Trellis site contains:

**Text Content** (version control recommended):
- Markdown files (`*.md`)
- Configuration files (`config.yaml`)
- Include files (Python, YAML, text)

**Binary Content** (file-based backups):
- Images (PNG, JPG, GIF)
- PDFs and documents
- Videos and other media

**Databases** (file-based backups):
- `trellis_admin.db` - User accounts
- `trellis_content.db` - Content metadata cache

**Generated Content** (can be rebuilt):
- `search_index/` - Full-text search index

## Recommended Approach: Hybrid Strategy

Use **Git for text content** and **rsync for full backups**.

### Why This Approach?

**Git Benefits:**
- ✅ Version history for text
- ✅ Easy rollback
- ✅ Works great with markdown
- ✅ Can push to remote (GitHub, GitLab)
- ❌ Poor performance with binary files
- ❌ Bloats repository with large files

**Rsync Benefits:**
- ✅ Efficient binary file backups
- ✅ Incremental backups (only changed files)
- ✅ Fast and reliable
- ✅ Handles databases and images well
- ❌ No version history
- ❌ Requires separate backup location

**Hybrid = Best of Both Worlds**

## Setup: Git for Text Content

--8<-- "includes/backup-git-setup.md"

### Auto-Commit Setup

Trellis automatically commits changes when you save content through the web editor if `GITLAB_REPO_PATH` is set:

In your `.env`:
```bash
GITLAB_REPO_PATH=/path/to/your/site
```

Each save creates a commit like:
```
Update: content/blog/article.md
```

### Manual Commits

For bulk changes:

```bash
git add content/
git commit -m "Added new article series"
git push origin main
```

## Setup: Rsync for Full Backups

### Basic Rsync Backup

```bash
#!/bin/bash
# backup.sh

SOURCE="/path/to/your/site"
BACKUP="/backup/trellis-$(date +%Y%m%d-%H%M%S)"

rsync -av --delete "$SOURCE/" "$BACKUP/"

echo "Backup complete: $BACKUP"
```

Make it executable:
```bash
chmod +x backup.sh
```

Run it:
```bash
./backup.sh
```

### Advanced Backup Script

Create `backup-trellis.sh`:

```bash
#!/bin/bash
# Comprehensive Trellis backup script

set -e  # Exit on error

# Configuration
SITE_DIR="/var/www/trellis_data"
BACKUP_BASE="/backup/trellis"
KEEP_DAYS=30
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="$BACKUP_BASE/$TIMESTAMP"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting Trellis backup..."
echo "Source: $SITE_DIR"
echo "Destination: $BACKUP_DIR"

# Full rsync backup
rsync -av \
  --delete \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  "$SITE_DIR/" \
  "$BACKUP_DIR/"

# Verify critical files
CRITICAL_FILES=(
  "trellis_admin.db"
  "trellis_content.db"
  "content"
)

for file in "${CRITICAL_FILES[@]}"; do
  if [ ! -e "$BACKUP_DIR/$file" ]; then
    echo "ERROR: Critical file missing: $file"
    exit 1
  fi
done

# Create backup manifest
cat > "$BACKUP_DIR/backup-info.txt" <<EOF
Backup Date: $(date)
Source: $SITE_DIR
Backup Script: $0
Hostname: $(hostname)
EOF

# Compress backup (optional)
# tar -czf "$BACKUP_BASE/trellis-$TIMESTAMP.tar.gz" -C "$BACKUP_BASE" "$TIMESTAMP"
# rm -rf "$BACKUP_DIR"

# Clean old backups
echo "Removing backups older than $KEEP_DAYS days..."
find "$BACKUP_BASE" -maxdepth 1 -type d -mtime +$KEEP_DAYS -exec rm -rf {} \;

echo "Backup complete: $BACKUP_DIR"

# Optional: Git commit and push
if [ -d "$SITE_DIR/.git" ]; then
  echo "Committing text changes to git..."
  cd "$SITE_DIR"
  git add -A
  if git diff --staged --quiet; then
    echo "No changes to commit"
  else
    git commit -m "Automated backup: $(date)"
    git push origin main || echo "Warning: Could not push to remote"
  fi
fi

echo "All backup tasks complete"
```

Make it executable:
```bash
chmod +x backup-trellis.sh
```

### Schedule Automatic Backups

Use cron to run backups automatically:

```bash
crontab -e
```

Add one of these schedules:

```cron
# Daily backup at 2 AM
0 2 * * * /path/to/backup-trellis.sh >> /var/log/trellis-backup.log 2>&1

# Every 6 hours
0 */6 * * * /path/to/backup-trellis.sh >> /var/log/trellis-backup.log 2>&1

# Weekly on Sunday at 3 AM
0 3 * * 0 /path/to/backup-trellis.sh >> /var/log/trellis-backup.log 2>&1
```

### Remote Backups with Rsync

Backup to remote server:

```bash
#!/bin/bash
# remote-backup.sh

SITE_DIR="/path/to/your/site"
REMOTE_USER="backup"
REMOTE_HOST="backup.example.com"
REMOTE_DIR="/backups/trellis"

rsync -av \
  --delete \
  -e "ssh -i ~/.ssh/backup_key" \
  "$SITE_DIR/" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

echo "Remote backup complete"
```

## Cloud Backups

### Amazon S3

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Sync to S3
aws s3 sync /path/to/your/site s3://your-bucket/trellis-backup/ \
  --exclude ".git/*" \
  --exclude "__pycache__/*" \
  --exclude "search_index/*"
```

### Backblaze B2

```bash
# Install B2 CLI
pip install b2

# Authenticate
b2 authorize-account

# Sync to B2
b2 sync /path/to/your/site b2://your-bucket/trellis-backup \
  --excludeRegex "\.git|__pycache__|search_index"
```

### Rsync.net

```bash
# Rsync.net provides rsync-over-ssh
rsync -av --delete \
  -e "ssh -p 22" \
  /path/to/your/site/ \
  username@usw-s001.rsync.net:trellis-backup/
```

## Restoration

### Restore from Rsync Backup

Full restoration:

```bash
BACKUP="/backup/trellis/20260109-020000"
SITE_DIR="/var/www/trellis_data"

# Stop the application
sudo systemctl stop trellis

# Restore files
rsync -av "$BACKUP/" "$SITE_DIR/"

# Set permissions
sudo chown -R www-data:www-data "$SITE_DIR"

# Rebuild search index
cd "$SITE_DIR"
trellis-search --rebuild
trellis-index --clear

# Start the application
sudo systemctl start trellis
```

### Restore from Git

Rollback to previous version:

```bash
cd /path/to/your/site

# View commit history
git log

# Rollback to specific commit
git checkout abc123 -- content/

# Or reset to previous state
git reset --hard HEAD~1

# Rebuild indexes
trellis-search --rebuild
```

### Restore Specific Files

```bash
# From rsync backup
cp /backup/trellis/20260109/content/blog/article.md \
   /path/to/your/site/content/blog/

# From git
git checkout HEAD~5 -- content/blog/article.md
```

## Testing Your Backups

**Monthly test restoration:**

```bash
# Create test environment
mkdir /tmp/trellis-test
cd /tmp/trellis-test

# Restore from backup
rsync -av /backup/trellis/latest/ .

# Verify critical files
ls -lh trellis_admin.db trellis_content.db
find content -name "*.md" | head

# Test database integrity
sqlite3 trellis_admin.db "PRAGMA integrity_check;"
sqlite3 trellis_content.db "PRAGMA integrity_check;"

# Cleanup
rm -rf /tmp/trellis-test
```

## Backup Verification

Create `verify-backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Usage: $0 /path/to/backup"
  exit 1
fi

echo "Verifying backup: $BACKUP_DIR"

# Check critical files exist
CRITICAL=(
  "trellis_admin.db"
  "trellis_content.db"
  "content"
)

for item in "${CRITICAL[@]}"; do
  if [ -e "$BACKUP_DIR/$item" ]; then
    echo "✓ $item"
  else
    echo "✗ MISSING: $item"
    exit 1
  fi
done

# Check database integrity
echo "Checking database integrity..."
sqlite3 "$BACKUP_DIR/trellis_admin.db" "PRAGMA integrity_check;" > /dev/null
echo "✓ trellis_admin.db is valid"

sqlite3 "$BACKUP_DIR/trellis_content.db" "PRAGMA integrity_check;" > /dev/null
echo "✓ trellis_content.db is valid"

# Count markdown files
MD_COUNT=$(find "$BACKUP_DIR/content" -name "*.md" 2>/dev/null | wc -l)
echo "✓ Found $MD_COUNT markdown files"

echo "Backup verification complete"
```

## Best Practices

**Backup frequency:**
- **Text content**: Automatic via git (on every save)
- **Full backups**: Daily or multiple times per day
- **Off-site backups**: Weekly to monthly

**Retention:**
- **Local backups**: Keep 30 days
- **Remote backups**: Keep 90+ days
- **Git history**: Keep forever (text is small)

**3-2-1 Rule:**
- **3** copies of your data
- **2** different storage types
- **1** off-site backup

**Example implementation:**
1. Primary: Your live site
2. Local: Rsync to local NAS/external drive
3. Remote: Git push to GitHub + S3/B2 sync

**Test regularly:**
- Monthly restoration tests
- Verify database integrity
- Check file counts

**Monitor backups:**
- Log backup results
- Alert on failures
- Track backup sizes

**Security:**
- Encrypt off-site backups
- Protect `.env` files with secrets
- Use SSH keys for remote backups
- Restrict backup script permissions (600)

## Troubleshooting

**Rsync permission denied:**
```bash
# Use sudo for system directories
sudo rsync -av ...

# Or fix ownership
sudo chown -R $USER /path/to/your/site
```

**Git repository too large:**
```bash
# Remove binary files from history
git filter-branch --tree-filter 'rm -f *.png *.jpg' HEAD

# Or use BFG Repo-Cleaner
bfg --delete-files *.png
```

**Database locked during backup:**
```bash
# Use SQLite backup API instead
sqlite3 source.db ".backup backup.db"
```

**Out of disk space:**
```bash
# Compress old backups
find /backup/trellis -type d -mtime +7 -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} \;

# Or reduce retention period
```

## Next Steps

- **[Search Indexing](indexing.md)** - Manage search indexes
- **[Updates](updates.md)** - Keeping Trellis up to date
- **[Deployment](../reference/deployment.md)** - Production setup

# Updates

Keeping Trellis CMS up to date.

## Checking Current Version

```bash
pip show trellis-cms
```

Output:
```
Name: trellis-cms
Version: 0.3.0
...
```

## Updating Trellis

### From PyPI

```bash
pip install --upgrade trellis-cms
```

### From Source

```bash
cd /path/to/trellis
git pull origin main
pip install --upgrade -e .
```

## Version History

### v0.3.0 (2026-01-09)

- Improved documentation with MkDocs
- Enhanced backup strategies
- Better indexing performance
- Bug fixes and stability improvements

### v0.2.1 (2024-11-25)

- Added commenting system integration
- Improved user management
- Added email capabilities
- Wiki-links for internal linking

### v0.2.0 (2024-11-22)

- Published to PyPI as `trellis-cms`
- Command-line tools: `trellis-init-db`, `trellis-search`, etc.
- Production-ready deployment support

### v0.1.0 (2024-10-15)

- Initial release
- Basic digital garden functionality
- Markdown rendering with frontmatter
- User authentication
- Git integration

## Breaking Changes

### v0.3.0

No breaking changes. Fully backward compatible with v0.2.x.

### v0.2.0

- **Command names changed**: Old scripts renamed to CLI commands
  - `init_db.py` → `trellis-init-db`
  - `rebuild_search.py` → `trellis-search --rebuild`

## Update Process

### 1. Backup First

Always backup before updating:

```bash
# Backup your data
./backup-trellis.sh

# Or manual backup
cp -r /path/to/site /backup/site-$(date +%Y%m%d)
```

### 2. Check Changelog

Read the changelog for breaking changes:

```bash
# On GitHub
https://github.com/almargolis/trellis/blob/main/CHANGELOG.md
```

### 3. Update Dependencies

```bash
# Update Trellis
pip install --upgrade trellis-cms

# Check dependencies
pip check
```

### 4. Run Migrations

If database changes are needed:

```bash
# Check for migration scripts
ls -l /path/to/trellis/migrations/

# Run migrations if any
trellis-migrate  # (future feature)
```

### 5. Rebuild Indexes

After major updates:

```bash
trellis-search --rebuild
trellis-index --clear
```

### 6. Test Locally

```bash
# Run development server
python run.py

# Test in browser
# - Login works
# - Content displays
# - Search works
# - Editor works
```

### 7. Deploy to Production

```bash
# Stop service
sudo systemctl stop trellis

# Update code (if from source)
cd /var/www/trellis
git pull origin main
pip install --upgrade -e .

# Restart service
sudo systemctl start trellis

# Verify
sudo systemctl status trellis
```

## Updating Dependencies

### Update All Dependencies

```bash
pip install --upgrade trellis-cms
```

This updates Trellis and all its dependencies.

### Update Specific Dependency

```bash
pip install --upgrade Flask
pip install --upgrade Markdown
```

### Check for Outdated Packages

```bash
pip list --outdated
```

## Rolling Back

### To Previous Version

```bash
# Install specific version
pip install trellis-cms==0.2.1

# Rebuild indexes
trellis-search --rebuild
```

### From Backup

```bash
# Stop service
sudo systemctl stop trellis

# Restore from backup
rsync -av /backup/site-20260109/ /path/to/site/

# Restart service
sudo systemctl start trellis
```

## Automated Updates

### Dependabot (GitHub)

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Renovate Bot

Create `renovate.json`:

```json
{
  "extends": ["config:base"],
  "python": {
    "enabled": true
  }
}
```

## Security Updates

### Check for Vulnerabilities

```bash
pip install safety
safety check
```

### Update Security Fixes Only

```bash
# Update Flask (example security fix)
pip install --upgrade Flask>=3.0.1
```

### Monitor Security Advisories

Subscribe to:
- GitHub Security Advisories
- PyPI security feed
- Flask security mailing list

## Production Update Checklist

- [ ] Read changelog and release notes
- [ ] Backup data directory
- [ ] Test in staging environment
- [ ] Schedule maintenance window
- [ ] Notify users of downtime
- [ ] Update application
- [ ] Run migrations if needed
- [ ] Rebuild indexes
- [ ] Test all functionality
- [ ] Monitor error logs
- [ ] Verify search and links work
- [ ] Confirm user login works

## Troubleshooting

### Dependency Conflicts

```bash
# List installed versions
pip list

# Check conflicts
pip check

# Resolve conflicts
pip install --upgrade --force-reinstall trellis-cms
```

### Import Errors After Update

```bash
# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Reinstall
pip uninstall trellis-cms
pip install trellis-cms
```

### Database Errors After Update

```bash
# Check database integrity
sqlite3 trellis_admin.db "PRAGMA integrity_check;"

# Restore from backup if needed
cp /backup/trellis_admin.db .
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u trellis -n 50

# Verify Python environment
which python3
python3 -c "import trellis; print(trellis.__version__)"

# Check permissions
ls -la /path/to/site
```

## Best Practices

**Before updating:**
- Always backup
- Test in development first
- Read release notes
- Check for breaking changes

**During updates:**
- Use maintenance mode
- Monitor error logs
- Have rollback plan ready

**After updating:**
- Test thoroughly
- Rebuild indexes
- Verify backups work
- Monitor performance

**Frequency:**
- Security updates: Immediately
- Feature updates: Monthly or quarterly
- Major versions: Plan carefully

## Development Updates

For developers working on Trellis itself:

```bash
# Update from git
cd /path/to/trellis
git pull origin main

# Update dependencies
pip install --upgrade -e .

# Run tests
pytest

# Check for issues
flake8 trellis/
```

## Next Steps

- **[Backup Strategy](backup.md)** - Protect your content
- **[Search Indexing](indexing.md)** - Manage indexes
- **[Deployment](../reference/deployment.md)** - Production setup

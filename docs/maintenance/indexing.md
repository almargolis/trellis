# Search Indexing

Managing Trellis search and content indexes.

## Overview

Trellis maintains two indexes:

1. **Search Index** (Whoosh) - Full-text search across all content
2. **Content Index** (SQLite) - Metadata cache for wiki-links and queries

Both indexes must stay synchronized with your content.

## Index Update Modes

### Immediate Mode (Default)

Indexes update automatically when you save/create content via the web editor:

- Single-file updates are fast (milliseconds)
- No manual intervention needed
- Best for single-user sites or low-traffic sites

**No configuration needed** - this is the default behavior.

### Deferred Mode

Updates are queued and processed in batches:

- Better for high-traffic sites with multiple editors
- Reduces lock contention
- Requires periodic rebuilds via cron

**Setup:**

In your `.env`:
```bash
TRELLIS_DEFERRED_INDEXING=true
```

Add cron job:
```bash
# Rebuild indexes every 5 minutes
*/5 * * * * cd /var/www/trellis && trellis-index-update
```

## Command Reference

### Update All Indexes

Check if rebuild is needed and rebuild if dirty:

```bash
trellis-index-update
```

Force rebuild regardless of dirty flag:

```bash
trellis-index-update --force
```

### Search Index Only

Rebuild full-text search index:

```bash
trellis-search --rebuild
```

Show search index statistics:

```bash
trellis-search --stats
```

Output:
```
Search Index Statistics
=======================
Total documents: 42
Index size: 1.2 MB
Last updated: 2026-01-09 14:30:00
```

### Content Index Only

Rebuild content metadata cache:

```bash
trellis-index --clear
```

Show content index statistics:

```bash
trellis-index --stats
```

Output:
```
Content Index Statistics
========================
Total articles: 42
Gardens: 3
Tags: 15
Last updated: 2026-01-09 14:30:00
```

## When to Rebuild

### After Bulk Changes

```bash
# Added many articles manually
cd content/blog
# ... added 10 new .md files ...

# Rebuild indexes
trellis-search --rebuild
```

### After Restoring from Backup

```bash
# Restored files from backup
rsync -av /backup/trellis/latest/ /var/www/trellis_data/

# Rebuild all indexes
trellis-search --rebuild
trellis-index --clear
```

### After Content Migration

```bash
# Moved articles between gardens
mv content/old-garden/*.md content/new-garden/

# Rebuild indexes
trellis-index-update --force
```

### Search Not Working

```bash
# Wiki-links or search returning nothing
trellis-search --rebuild
```

## How It Works

### Immediate Mode Flow

1. User saves article via web editor
2. `MarkdownHandler.save_file()` writes markdown
3. `IndexManager.update_single_file()` updates indexes
4. Search and wiki-links work immediately

### Deferred Mode Flow

1. User saves article via web editor
2. `MarkdownHandler.save_file()` writes markdown
3. `IndexManager` sets `.index_dirty` flag file
4. Cron job checks for flag, rebuilds if present
5. Flag is cleared after successful rebuild

### Index Structure

**Search Index** (`search_index/`):
```
search_index/
  _MAIN_xxx.toc
  _MAIN_xxx.seg
  ...
```

Whoosh index files for full-text search.

**Content Index** (`trellis_content.db`):
```sql
CREATE TABLE articles (
  id INTEGER PRIMARY KEY,
  title TEXT,
  slug TEXT,
  garden_slug TEXT,
  content TEXT,
  tags TEXT,
  published_date TEXT,
  ...
);
```

SQLite database for fast metadata lookups.

## Performance Considerations

### Index Rebuild Times

Typical rebuild times (depends on content size):

| Articles | Search Index | Content Index | Total |
|----------|--------------|---------------|-------|
| 10       | < 1s         | < 1s          | < 2s  |
| 100      | 2-3s         | 1-2s          | 3-5s  |
| 1000     | 15-20s       | 5-10s         | 20-30s |
| 10000    | 2-3 min      | 30-60s        | 3-4 min |

### Single File Updates

Immediate mode single-file updates:

| Operation | Time |
|-----------|------|
| Update existing article | 50-100ms |
| Add new article | 100-200ms |
| Delete article | 50-100ms |

Much faster than full rebuild!

### Optimization Tips

**For small sites (< 100 articles):**
- Use immediate mode
- No cron needed
- Fast enough for real-time updates

**For medium sites (100-1000 articles):**
- Immediate mode still fine
- Consider deferred for multiple concurrent editors
- Cron every 5-10 minutes

**For large sites (> 1000 articles):**
- Use deferred mode
- Cron every 1-5 minutes
- Consider dedicated search service (future feature)

## Monitoring

### Check Index Health

```bash
# Verify search index
trellis-search --stats

# Verify content index
trellis-index --stats

# Check for dirty flag
ls -la /path/to/site/.index_dirty
```

### Log Index Operations

Add logging to your cron job:

```bash
#!/bin/bash
# index-update-cron.sh

LOGFILE="/var/log/trellis-index.log"

echo "=== Index update started at $(date) ===" >> "$LOGFILE"
trellis-index-update >> "$LOGFILE" 2>&1
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE" >> "$LOGFILE"
echo "" >> "$LOGFILE"

if [ $EXIT_CODE -ne 0 ]; then
  # Send alert (example)
  echo "Index update failed" | mail -s "Trellis Index Error" admin@example.com
fi
```

Crontab:
```cron
*/5 * * * * /path/to/index-update-cron.sh
```

### Monitor Index Size

```bash
#!/bin/bash
# check-index-size.sh

SITE_DIR="/var/www/trellis_data"

echo "Index Sizes:"
du -sh "$SITE_DIR/search_index"
du -sh "$SITE_DIR/trellis_content.db"

# Alert if too large
SEARCH_SIZE=$(du -sm "$SITE_DIR/search_index" | cut -f1)
if [ $SEARCH_SIZE -gt 1000 ]; then
  echo "Warning: Search index is very large ($SEARCH_SIZE MB)"
fi
```

## Troubleshooting

### Search Returns No Results

```bash
# Rebuild search index
trellis-search --rebuild

# Check index stats
trellis-search --stats

# If stats show 0 documents, check content directory
ls -R content/
```

### Wiki-Links Not Resolving

```bash
# Rebuild content index
trellis-index --clear

# Check index stats
trellis-index --stats

# Verify articles are indexed
sqlite3 trellis_content.db "SELECT COUNT(*) FROM articles;"
```

### Index Corruption

```bash
# Remove corrupted indexes
rm -rf search_index/
rm -f trellis_content.db

# Rebuild from scratch
trellis-search --rebuild
trellis-index --clear
```

### Cron Job Not Running

```bash
# Check cron logs
grep CRON /var/log/syslog

# Test manually
trellis-index-update

# Check permissions
ls -l $(which trellis-index-update)
```

### Database Locked

```bash
# Check for running processes
ps aux | grep trellis

# Kill stale processes
pkill -f trellis-index-update

# Retry
trellis-index-update --force
```

### Out of Disk Space

```bash
# Check index sizes
du -sh search_index/ trellis_content.db

# Clean and rebuild
rm -rf search_index/
trellis-search --rebuild
```

## Advanced Topics

### Custom Search Schema

For advanced users, you can customize the Whoosh schema in `trellis/utils/search_handler.py`:

```python
schema = Schema(
    path=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT(stored=True),
    tags=KEYWORD(stored=True, commas=True),
    published_date=DATETIME(stored=True),
    # Add custom fields here
)
```

### Query Optimization

Search queries support:

- **Phrase search**: `"exact phrase"`
- **Wildcards**: `python*` matches "python", "pythonic"
- **Boolean**: `python AND flask`, `python OR javascript`
- **Field search**: `title:python`, `tags:tutorial`

Example complex query:
```
title:python AND (flask OR django) -beginner
```

### Index Backup

Include indexes in backups for faster restoration:

```bash
# Backup with indexes
rsync -av \
  --include="search_index/" \
  --include="trellis_content.db" \
  /path/to/site/ \
  /backup/trellis/
```

Or exclude and rebuild after restore (saves space):

```bash
# Backup without indexes (smaller)
rsync -av \
  --exclude="search_index/" \
  --exclude="trellis_content.db" \
  /path/to/site/ \
  /backup/trellis/

# After restore
trellis-index-update --force
```

## Best Practices

**Development:**
- Use immediate mode
- Rebuild after bulk imports
- Test search after changes

**Production:**
- Use deferred mode for high-traffic sites
- Cron every 5 minutes
- Monitor cron logs
- Alert on failures

**Maintenance:**
- Rebuild indexes after restoration
- Verify with `--stats` commands
- Include in monitoring scripts
- Document rebuild procedures

**Performance:**
- Use immediate mode for < 1000 articles
- Use deferred mode for >= 1000 articles
- Monitor index sizes
- Optimize search queries

## Next Steps

- **[Backup Strategy](backup.md)** - Protect your content
- **[Updates](updates.md)** - Keeping Trellis up to date
- **[Deployment](../reference/deployment.md)** - Production setup

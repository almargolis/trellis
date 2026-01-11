# Documentation Includes Guide

MkDocs supports including shared documentation snippets using the `pymdownx.snippets` extension.

## How It Works

The `--8<--` syntax includes external files into your documentation:

```markdown
--8<-- "includes/backup-git-setup.md"
```

When the documentation builds, that line is replaced with the contents of `docs/includes/backup-git-setup.md`.

## Current Implementation

### Trellis Includes

Located in `docs/includes/`:

- **`backup-git-setup.md`** - Git repository setup for backups
- **`quickdev-dev-setup.md`** - Editable install instructions for quickdev dependencies

### Usage Examples

See how they're used:

- `docs/maintenance/backup.md` - Uses `backup-git-setup.md`
- `docs/reference/development.md` - Uses `quickdev-dev-setup.md`

## Creating Shared Quickdev Documentation

For documentation that should be shared across multiple quickdev-based applications, you have several options:

### Option 1: Dedicated quickdev-docs Repository (Recommended)

Create a separate repository for shared documentation:

```bash
# Create the repository
mkdir quickdev-docs
cd quickdev-docs
git init

# Create directory structure
mkdir -p docs/includes/{backup,development,deployment,testing}

# Add shared snippets
cat > docs/includes/backup/git-setup.md <<'EOF'
### Initialize Git Repository
...
EOF
```

**Structure:**
```
quickdev-docs/
  docs/
    includes/
      backup/
        git-setup.md
        rsync-backup.md
        cloud-backup.md
        3-2-1-rule.md
      development/
        editable-install.md
        testing-strategy.md
        debugging.md
      deployment/
        systemd-service.md
        apache-wsgi.md
        nginx-uwsgi.md
        ssl-setup.md
      monitoring/
        logging.md
        error-tracking.md
        performance.md
```

**In each application:**

```bash
cd /path/to/app

# Add as git submodule
git submodule add https://github.com/almargolis/quickdev-docs.git docs/includes/quickdev
git commit -m "Add quickdev docs submodule"

# Or for development, use symlink
ln -s ../../../quickdev-docs/docs/includes docs/includes/quickdev
```

**In application's mkdocs.yml:**

```yaml
markdown_extensions:
  - pymdownx.snippets:
      base_path:
        - docs
        - docs/includes
        - docs/includes/quickdev  # Add quickdev docs path
```

**Use in documentation:**

```markdown
## Backup Strategy

--8<-- "quickdev/backup/git-setup.md"

For more advanced backup strategies:

--8<-- "quickdev/backup/3-2-1-rule.md"
```

### Option 2: Within Quickdev Repository

Keep shared docs in the main quickdev repo:

```bash
cd /Users/almargolis/Projects/quickdev

# Create docs structure
mkdir -p docs/includes/{backup,deployment,development}

# Add shared documentation
```

**In each application:**

```bash
# Symlink (development)
ln -s ../../../quickdev/docs/includes docs/includes/quickdev

# Or sparse checkout (production)
git sparse-checkout set docs/includes
```

### Option 3: Per-App Customization with Base

Create base snippets that apps can extend:

**quickdev-docs/docs/includes/backup/git-setup-base.md:**
```markdown
### Initialize Git Repository

```bash
cd /path/to/your/site
git init
```

### Create `.gitignore`

Exclude generated files:

```gitignore
# Databases
*.db
*.db-journal

# Environment
.env
```
```

**trellis/docs/includes/backup-git-setup.md:**
```markdown
--8<-- "quickdev/backup/git-setup-base.md"

### Trellis-Specific Exclusions

Add these Trellis-specific patterns:

```gitignore
# Search index (can be rebuilt)
search_index/

# Content index
trellis_content.db
```
```

## With Variable Substitution

For even more flexibility, install `mkdocs-macros-plugin`:

```bash
pip install mkdocs-macros-plugin
```

**mkdocs.yml:**
```yaml
plugins:
  - search
  - macros

extra:
  app_name: "Trellis"
  data_dir: "/var/www/trellis_data"
  db_name: "trellis_admin.db"
```

**In documentation:**
```markdown
The application stores data in `{{ data_dir }}` with database `{{ db_name }}`.
```

**In shared snippets:**
```markdown
### Initialize Database

```bash
cd {{ data_dir }}
sqlite3 {{ db_name }} < schema.sql
```
```

## Benefits of Shared Documentation

1. **Single Source of Truth** - Update once, all apps benefit
2. **Consistency** - All quickdev apps have consistent documentation patterns
3. **Maintenance** - Fix documentation bugs in one place
4. **Versioning** - Use git tags for doc versions
5. **Customization** - Apps can extend or override shared docs

## Example Shared Topics

Good candidates for shared documentation:

- **Backup strategies** - Git setup, rsync, cloud backups, 3-2-1 rule
- **Development workflow** - Editable installs, testing, debugging
- **Deployment patterns** - systemd, Apache, Nginx, SSL
- **Database management** - SQLite best practices, backups, migrations
- **Security** - .env files, secrets management, permission hardening
- **Monitoring** - Logging, error tracking, performance monitoring
- **CI/CD** - GitHub Actions, testing pipelines

## Updating Documentation Flow

When you improve documentation in one app:

1. **Identify shared content** - Is this useful for other apps?
2. **Extract to shared snippet** - Move to quickdev-docs
3. **Replace in original app** - Use include syntax
4. **Update other apps** - Pull latest quickdev-docs
5. **Test builds** - Ensure all apps build correctly

## Best Practices

1. **Keep snippets focused** - Each file covers one topic
2. **Use descriptive names** - `backup-git-setup.md` not `git.md`
3. **Version shared docs** - Tag releases in quickdev-docs repo
4. **Document variables** - If using macros, document required variables
5. **Test across apps** - Ensure snippets work in all contexts
6. **Provide examples** - Show how to use each snippet
7. **Avoid deep nesting** - Keep include chains shallow

## See Also

- `docs/includes/README.txt` - Additional usage examples
- [pymdownx.snippets docs](https://facelessuser.github.io/pymdown-extensions/extensions/snippets/)
- [mkdocs-macros-plugin](https://mkdocs-macros-plugin.readthedocs.io/)

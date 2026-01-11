# Using Includes in MkDocs

## Basic Include Syntax

Use the `--8<--` syntax to include files:

````markdown
--8<-- "includes/backup-git-setup.md"
````

This includes the entire file content at that location.

## Partial Includes

Include specific sections using line numbers or markers:

````markdown
<!-- Include lines 1-10 -->
--8<-- "includes/backup-git-setup.md:1:10"
````

## With Variables (Requires mkdocs-macros-plugin)

For variable substitution, install mkdocs-macros-plugin:

```bash
pip install mkdocs-macros-plugin
```

Add to mkdocs.yml:
```yaml
plugins:
  - search
  - macros

extra:
  app_name: "Trellis"
  data_dir: "/var/www/trellis_data"
```

Then use Jinja2 syntax:
````markdown
The data directory is: {{ data_dir }}
````

## Shared Quickdev Documentation

Place common snippets in a shared location that all quickdev-based apps can reference:

**Option 1: Git Submodule**
```bash
# In each app repo
git submodule add https://github.com/almargolis/quickdev-docs docs/includes/quickdev
```

Then include in docs:
````markdown
--8<-- "includes/quickdev/backup-strategy.md"
````

**Option 2: Symlink (Development)**
```bash
# In each app repo
ln -s ../../quickdev/docs/includes docs/includes/quickdev
```

Then include in docs:
````markdown
--8<-- "includes/quickdev/backup-strategy.md"
````

**Option 3: Separate quickdev-docs Repo**
```bash
# Create a dedicated docs repo
mkdir quickdev-docs
cd quickdev-docs
# Add common documentation snippets

# In each app, add as submodule
git submodule add https://github.com/almargolis/quickdev-docs docs/includes/quickdev
```

## Example Structure

```
quickdev-docs/
  backup/
    git-setup.md
    rsync-backup.md
    cloud-backup.md
  development/
    editable-install.md
    testing.md
  deployment/
    systemd-service.md
    apache-config.md
    nginx-config.md

trellis/
  docs/
    includes/
      quickdev/ -> ../../../quickdev-docs  (symlink or submodule)
    getting-started/
      installation.md  (includes quickdev snippets)
```

## Benefits

1. **Single Source of Truth** - Update backup strategy once, all apps benefit
2. **Consistency** - All quickdev-based apps have consistent documentation
3. **Maintenance** - Fix documentation bugs in one place
4. **Customization** - Apps can override or extend shared docs

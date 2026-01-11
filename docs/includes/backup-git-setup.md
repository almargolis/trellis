### Initialize Git Repository

```bash
cd /path/to/your/site
git init
```

### Create `.gitignore`

Exclude binary content and generated files:

```gitignore
# Databases (backed up by rsync)
*.db
*.db-journal
*.db-wal

# Search index (can be rebuilt)
search_index/

# Large binary files (backed up by rsync)
*.png
*.jpg
*.jpeg
*.gif
*.bmp
*.ico
*.pdf
*.zip
*.tar.gz
*.mp4
*.mov
*.avi

# System files
.DS_Store
Thumbs.db
__pycache__/
*.pyc

# Environment files (may contain secrets)
.env

# Keep text content in git
!*.md
!*.yaml
!*.yml
!*.py
!*.js
!*.css
!*.html
!*.txt
```

### Initial Commit

```bash
git add .
git commit -m "Initial site setup"
```

### Optional: Push to Remote

```bash
# Create a repository on GitHub/GitLab, then:
git remote add origin git@github.com:yourusername/your-site.git
git branch -M main
git push -u origin main
```

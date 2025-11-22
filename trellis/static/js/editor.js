// Initialize CodeMirror
const editor = CodeMirror.fromTextArea(document.getElementById('markdown-editor'), {
    mode: 'markdown',
    theme: 'monokai',
    lineNumbers: true,
    lineWrapping: true,
    autoCloseBrackets: true,
    matchBrackets: true
});

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Preview update
const updatePreview = debounce(async () => {
    const content = editor.getValue();

    try {
        const response = await fetch('/editor/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content })
        });

        const data = await response.json();
        document.getElementById('preview-content').innerHTML = data.html;
    } catch (error) {
        console.error('Preview error:', error);
    }
}, 500);

// Listen for changes
editor.on('change', updatePreview);

// Save functionality
document.getElementById('save-btn').addEventListener('click', async () => {
    const filename = document.getElementById('article-filename').value;
    const garden_slug = document.getElementById('garden-slug').value;
    const content = editor.getValue();

    const metadata = {
        title: document.getElementById('title').value,
        created_date: document.getElementById('created-date').value,
        published_date: document.getElementById('published-date').value,
        updated_date: document.getElementById('updated-date').value,
        tags: document.getElementById('tags').value.split(',').map(t => t.trim()).filter(t => t)
    };

    const status = document.getElementById('save-status');
    status.textContent = 'Saving...';
    status.className = 'save-status saving';

    try {
        const response = await fetch('/editor/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filename, garden_slug, metadata, content })
        });

        const data = await response.json();

        if (data.success) {
            status.textContent = 'Saved!';
            status.className = 'save-status success';

            // Update the updated date
            document.getElementById('updated-date').value = data.metadata.updated_date;

            setTimeout(() => {
                status.textContent = '';
                status.className = 'save-status';
            }, 3000);
        } else {
            throw new Error('Save failed');
        }
    } catch (error) {
        status.textContent = 'Save failed!';
        status.className = 'save-status error';
        console.error('Save error:', error);
    }
});

// Download functionality
document.getElementById('download-btn').addEventListener('click', () => {
    // Get metadata
    const metadata = {
        title: document.getElementById('title').value,
        created_date: document.getElementById('created-date').value,
        published_date: document.getElementById('published-date').value,
        updated_date: document.getElementById('updated-date').value,
        tags: document.getElementById('tags').value.split(',').map(t => t.trim()).filter(t => t)
    };

    // Build frontmatter
    let frontmatter = '---\n';
    frontmatter += `title: ${metadata.title}\n`;
    frontmatter += `created_date: ${metadata.created_date}\n`;
    frontmatter += `published_date: ${metadata.published_date}\n`;
    frontmatter += `updated_date: ${metadata.updated_date}\n`;
    if (metadata.tags.length > 0) {
        frontmatter += 'tags:\n';
        metadata.tags.forEach(tag => {
            frontmatter += `  - ${tag}\n`;
        });
    }
    frontmatter += '---\n\n';

    // Combine frontmatter and content
    const content = frontmatter + editor.getValue();
    const filename = metadata.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') + '.md';

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
});

// Upload functionality
document.getElementById('upload-file').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
        const content = e.target.result;

        // Parse the markdown file
        // Simple frontmatter parser
        const frontmatterRegex = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/;
        const match = content.match(frontmatterRegex);

        if (match) {
            const frontmatterText = match[1];
            const bodyContent = match[2];

            // Parse YAML frontmatter (simple key: value parser)
            const lines = frontmatterText.split('\n');
            let currentTags = [];
            let inTags = false;

            lines.forEach(line => {
                if (line.trim().startsWith('title:')) {
                    document.getElementById('title').value = line.split('title:')[1].trim();
                } else if (line.trim().startsWith('created_date:')) {
                    document.getElementById('created-date').value = line.split('created_date:')[1].trim();
                } else if (line.trim().startsWith('published_date:')) {
                    document.getElementById('published-date').value = line.split('published_date:')[1].trim();
                } else if (line.trim().startsWith('updated_date:')) {
                    document.getElementById('updated-date').value = line.split('updated_date:')[1].trim();
                } else if (line.trim() === 'tags:') {
                    inTags = true;
                } else if (inTags && line.trim().startsWith('- ')) {
                    currentTags.push(line.trim().substring(2));
                } else if (inTags && !line.trim().startsWith('- ')) {
                    inTags = false;
                }
            });

            if (currentTags.length > 0) {
                document.getElementById('tags').value = currentTags.join(', ');
            }

            // Set the content in CodeMirror
            editor.setValue(bodyContent);

            // Update preview
            updatePreview();
        } else {
            // No frontmatter, just set the content
            editor.setValue(content);
            updatePreview();
        }
    };

    reader.readAsText(file);

    // Clear the file input so the same file can be uploaded again if needed
    event.target.value = '';
});

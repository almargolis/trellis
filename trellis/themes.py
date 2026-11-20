"""
Trellis Theme Presets

Defines color scheme presets that override the CSS custom properties
in colors.css. Each preset is a dictionary of CSS variable names to values.
"""

PRESETS = {
    'default': {
        # Blue scheme (matches colors.css defaults)
        '--primary-color': '#2c5aa0',
        '--secondary-color': '#4a90e2',
        '--accent-color': '#f39c12',
    },
    'forest': {
        '--primary-color': '#2d6a4f',
        '--secondary-color': '#52b788',
        '--accent-color': '#d4a373',
    },
    'ocean': {
        '--primary-color': '#1b4965',
        '--secondary-color': '#5fa8d3',
        '--accent-color': '#bee9e8',
    },
    'sunset': {
        '--primary-color': '#9b2226',
        '--secondary-color': '#ca6702',
        '--accent-color': '#ee9b00',
    },
    'slate': {
        '--primary-color': '#475569',
        '--secondary-color': '#64748b',
        '--accent-color': '#f59e0b',
    },
}


def get_theme_css(theme_name):
    """Return inline CSS to override :root variables for the given theme.

    Args:
        theme_name: Name of a preset theme, or None/'default' for no overrides.

    Returns:
        CSS string (may be empty if theme is default or unknown).
    """
    if not theme_name or theme_name == 'default':
        return ''

    overrides = PRESETS.get(theme_name)
    if not overrides:
        return ''

    lines = [':root {']
    for var, value in overrides.items():
        lines.append(f'    {var}: {value};')
    lines.append('}')
    return '\n'.join(lines)

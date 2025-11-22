# Contributing to Trellis

Thank you for your interest in contributing to Trellis!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/trellis.git`
3. Create a virtual environment: `python3 -m venv venv && source venv/bin/activate`
4. Install in development mode: `pip install -e ".[dev]"`
5. Create a branch for your changes: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your local paths

# Initialize database
trellis-init-db

# Run development server
python -c "from trellis import create_app; create_app().run(debug=True)"
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

## Making Changes

1. Make your changes in a feature branch
2. Test your changes thoroughly
3. Update documentation if needed
4. Commit with clear, descriptive messages

## Pull Requests

1. Push your branch to your fork
2. Open a Pull Request against the `main` branch
3. Describe your changes and why they're needed
4. Link any related issues

## Reporting Issues

When reporting bugs, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Any error messages

## Feature Requests

Feature requests are welcome! Please open an issue describing:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

## Questions

If you have questions, feel free to open an issue with the "question" label.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

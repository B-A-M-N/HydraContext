# Contributing to HydraContext

Thank you for your interest in contributing to HydraContext! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or suggest features
- Provide a clear description and reproduction steps
- Include your Python version and operating system

### Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/`)
6. Format code with Black (`black hydracontext/`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to your branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/B-A-M-N/HydraContext.git
cd HydraContext

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black hydracontext/
```

## Code Style

- Follow PEP 8 guidelines
- Use Black for formatting (line length: 100)
- Add type hints where appropriate
- Write docstrings for all public functions/classes
- Keep functions focused and small

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Include edge cases

## Documentation

- Update README.md for new features
- Add docstrings with examples
- Update CHANGELOG.md

## Code Review Process

1. All submissions require review
2. Maintainers will provide feedback
3. Address review comments
4. Once approved, maintainers will merge

## Questions?

Feel free to open an issue for questions or discussion!

Thank you for contributing! 🎉

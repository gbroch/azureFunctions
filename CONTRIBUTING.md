# Contributing to Azure Functions Cost Management

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/gbroch/azureFunctions.git
   cd azureFunctions
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure local settings**
   ```bash
   cp local.settings.json.template local.settings.json
   # Edit local.settings.json with your Azure subscription ID
   ```

5. **Authenticate with Azure**
   ```bash
   az login
   ```

## Code Style

- Follow PEP 8 style guide for Python code
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose
- Include error handling and logging

## Testing

Before submitting a pull request:

1. Test the function locally:
   ```bash
   func start
   ./test_function.sh local <your-subscription-id>
   ```

2. Ensure your changes don't break existing functionality

3. Add appropriate error handling and logging

## Adding New Resource Types

To add support for shutting down additional resource types:

1. Update the `shutdown_resources()` function in `CostManager/__init__.py`
2. Add the appropriate Azure SDK client if needed
3. Implement the shutdown logic with proper error handling
4. Update the README.md documentation
5. Test thoroughly with actual Azure resources

Example:
```python
elif resource_type == "sqlservers":
    # Add SQL Server pause logic
    sql_client = SqlManagementClient(credential, subscription_id)
    # Implement pause/stop logic
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -am 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Create a Pull Request

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Include testing steps
- Update documentation as needed
- Ensure CI/CD checks pass

## Reporting Issues

When reporting issues, please include:

- Azure Function runtime version
- Python version
- Error messages and stack traces
- Steps to reproduce the issue
- Expected vs actual behavior

## Security

If you discover a security vulnerability, please email the maintainer directly instead of creating a public issue.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

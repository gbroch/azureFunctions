# Contributing Guide

Thank you for considering contributing to this project! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Azure Functions Core Tools (optional, for local testing)
- Git
- A code editor (VS Code recommended)

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/gbroch/azureFunctions.git
cd azureFunctions
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the settings template:
```bash
cp local.settings.json.template local.settings.json
```

5. Update `local.settings.json` with your Azure AD credentials (for testing):
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_TENANT_ID": "your-test-tenant-id",
    "AZURE_CLIENT_ID": "your-test-client-id",
    "AZURE_CLIENT_SECRET": "your-test-client-secret"
  }
}
```

### Running Locally

Start the Azure Function locally:
```bash
func start
```

Test the function:
```bash
curl -X POST http://localhost:7071/api/RemoveGlobalAdmins
```

## Code Style

### Python Code Style

- Follow PEP 8 style guidelines
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use type hints where appropriate
- Add docstrings to functions and classes

### Example

```python
def process_user(user_id: str, user_name: str) -> dict:
    """
    Process a user and return status information.
    
    Args:
        user_id: The unique identifier for the user
        user_name: The user's principal name
        
    Returns:
        A dictionary containing the processing status
    """
    # Implementation here
    pass
```

## Testing

### Manual Testing

Before submitting a pull request:

1. Test the function locally with test credentials
2. Verify error handling with invalid credentials
3. Check logging output for clarity and completeness
4. Test with different scenarios (no users, multiple users, errors)

### Test Checklist

- [ ] Function starts without errors
- [ ] Environment variable validation works
- [ ] Authentication succeeds with valid credentials
- [ ] Function correctly identifies Global Administrator role
- [ ] Function removes users as expected
- [ ] Error handling works properly
- [ ] Logging is clear and informative
- [ ] Response format is correct

## Making Changes

### Workflow

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes
3. Test your changes locally
4. Commit with clear messages:
```bash
git add .
git commit -m "Add feature: description of your change"
```

5. Push to your fork:
```bash
git push origin feature/your-feature-name
```

6. Open a Pull Request

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests where appropriate

Examples:
- `Add retry logic for Graph API calls`
- `Fix error handling for missing environment variables`
- `Update documentation for deployment process`

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update DEPLOYMENT.md if deployment steps change
3. Ensure your code follows the style guidelines
4. Test your changes thoroughly
5. Update documentation as needed
6. Request review from maintainers

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Changes are tested locally
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No sensitive information (keys, secrets) in code

## Reporting Issues

### Bug Reports

When reporting bugs, include:

- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (Python version, Azure region, etc.)
- Error messages or logs
- Screenshots if applicable

### Feature Requests

When requesting features, include:

- Clear description of the feature
- Use case and motivation
- Proposed implementation (if you have ideas)
- Any alternatives you've considered

## Code Review Process

Maintainers will review your pull request and may:

- Request changes
- Ask questions
- Suggest improvements
- Approve and merge

Please be patient and responsive to feedback.

## Security

### Reporting Security Issues

**Do not** open public issues for security vulnerabilities.

Instead, email the maintainers directly or use GitHub Security Advisories.

### Security Guidelines

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Follow principle of least privilege
- Keep dependencies up to date
- Review security best practices for Azure Functions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Questions?

If you have questions, feel free to:
- Open an issue for discussion
- Reach out to maintainers
- Check existing issues and documentation

## Thank You!

Your contributions make this project better for everyone. Thank you for taking the time to contribute!

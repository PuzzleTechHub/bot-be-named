# Test Suite Documentation

This directory contains the test suite for the bot-be-named project, with initial focus on the Hydra module.

## Structure

```
tests/
├── conftest.py                     
├── test_configs.py                 
├── modules/
│   └── hydra/
│       ├── test_old_lion_command_helpers.py  
│       └── test_hydra_helpers.py             
└── README.md                       
```

## Test Organization

### Fixtures (conftest.py)

The `conftest.py` file contains reusable fixtures:

- `mock_bot` - Mock Discord bot instance
- `mock_channel` - Mock Discord channel
- `mock_message` - Mock Discord message
- `mock_ctx` - Mock command context (combines channel and message)
- `mock_gspread_client` - Mock Google Sheets client
- `mock_embed` - Mock Discord embed

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=modules --cov=utils --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

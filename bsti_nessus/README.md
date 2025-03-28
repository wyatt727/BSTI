# BSTI Nessus to Plextrac Converter

A clean, modern implementation of the Nessus to Plextrac conversion and upload tool.

## Features

- Convert Nessus CSV files to Plextrac format
- Upload findings to Plextrac
- Upload screenshots for findings
- Filter out duplicate findings
- Smart categorization of findings
- Detailed logging and error handling
- Progress reporting with ETA calculations
- Parallel processing for faster conversions and uploads

## Installation

### Prerequisites

- Python 3.8+
- Access to a Plextrac instance
- Nessus CSV exports

### Installation

#### Easy Installation

Use the provided installation scripts:

**On Linux/macOS:**
```bash
chmod +x install.sh
./install.sh
```

**On Windows:**
```
install.bat
```

#### Manual Installation

1. Clone the repository:
```bash
git clone [repository_url]
cd [repository_directory]
```

2. Install the package:
```bash
pip install -e .
```

## Usage

After installation, you can run the tool using:

```bash
bsti-nessus --help
```

The basic usage is:

```bash
bsti-nessus -u [username] -p [password] -d [nessus_directory] -t [plextrac_instance]
```

### Configuration Wizard

For an interactive setup experience, use the configuration wizard:

```bash
bsti-nessus --config-wizard
```

The wizard will guide you through setting up:
- Plextrac instance connections
- Nessus parser settings
- General application settings

After completing the wizard, your settings will be saved to a configuration file for future use.

### Credential Management

The tool includes secure credential management for storing Plextrac login information securely. Credentials are stored using platform-specific secure storage:
- macOS: Keychain
- Windows: Credential Manager
- Linux: Secret Service API
- Other platforms: Encrypted file-based storage

To use stored credentials:

```bash
bsti-nessus -t dev --use-stored-credentials
```

To store credentials for later use:

```bash
bsti-nessus -t dev --store-credentials
```

### Progress Reporting

The tool now includes real-time progress reporting with ETA calculations for all long-running operations:

- File scanning
- Parsing Nessus CSV files
- Converting findings
- Uploading to Plextrac

You'll see a progress bar with:
- Percentage complete
- Items processed
- Estimated time remaining
- Processing speed

### Parallel Processing

The tool uses parallel processing to speed up operations:

- Multi-threading for I/O-bound operations (API calls, file operations)
- Multi-processing for CPU-bound operations (parsing, conversion)

To control parallel processing:

```bash
bsti-nessus --workers 8 --disable-parallel
```

- `--workers`: Set the number of worker threads/processes (default: auto)
- `--disable-parallel`: Disable parallel processing

### Required Arguments

- `-u, --username`: Username for Plextrac authentication
- `-p, --password`: Password for Plextrac authentication
- `-d, --directory`: Directory containing Nessus CSV files
- `-t, --target-plextrac`: Target Plextrac instance (e.g., 'dev', 'prod')

### Optional Arguments

- `-s, --scope`: Scope of the findings (default: internal)
  - Choices: internal, external, web, surveillance, mobile
- `--screenshot-dir`: Directory containing screenshots to upload
- `--client`: Client name for the report
- `--report`: Report name for the findings
- `--screenshots`: Upload screenshots if available
- `--cleanup`: Clean up temporary files after processing
- `--non-core`: Update non-core fields in Plextrac
- `--workers`: Number of worker threads/processes for parallel operations
- `--disable-parallel`: Disable parallel processing
- `-v, --verbosity`: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)

### Examples

Convert and upload Nessus findings:
```bash
bsti-nessus -u johndoe -p password123 -d ./nessus_files -t dev -s external
```

Use stored credentials and parallel processing:
```bash
bsti-nessus -d ./nessus_files -t dev --use-stored-credentials --workers 8
```

Include screenshot uploads:
```bash
bsti-nessus -u johndoe -p password123 -d ./nessus_files -t dev --screenshots --screenshot-dir ./screenshots
```

## Configuration

The tool uses configuration files located in the `config` directory:

- `config.json`: Main configuration file
- `plugins_definitions.json`: Plugin category definitions

### Plugin Definitions

You can customize the plugin category definitions in `plugins_definitions.json`:

```json
{
    "plugins": {
        "category_name": {
            "writeup_name": "Category Display Name",
            "description": "Description of the category",
            "ids": ["plugin_id1", "plugin_id2", ...]
        },
        ...
    }
}
```

## Directory Structure

```
bsti_nessus/
├── config/
│   ├── config.json
│   ├── plugins_definitions.json
│   └── templates/
├── core/
│   ├── __init__.py
│   ├── cli.py
│   └── engine.py
├── integrations/
│   ├── __init__.py
│   ├── nessus/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── parser.py
│   └── plextrac/
│       ├── __init__.py
│       ├── api.py
│       └── models.py
└── utils/
    ├── __init__.py
    ├── config_manager.py
    ├── credentials.py
    ├── http_client.py
    ├── logger.py
    ├── parallel.py
    └── progress.py
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=bsti_nessus

# Run specific test file
pytest bsti_nessus/tests/unit/utils/test_progress.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
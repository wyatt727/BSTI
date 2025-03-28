# Drone Connection Manager

The Drone Connection Manager provides an easy way to set up, store, and reuse drone connection configurations. This feature allows you to save your drone connection details and access them using just a friendly name, eliminating the need to repeatedly enter hostnames, usernames, and passwords.

## Features

- **Configuration Storage**: Save drone connection details (hostname, username, password) securely
- **Simple Setup Wizard**: Guided interactive setup process
- **Connection Testing**: Test connections before saving or using
- **Command-line Interface**: Manage drone connections directly from the command line
- **Integration with NMB**: Use saved configurations in all NMB commands

## Setting Up a Drone Connection

### Using the Setup Script

The easiest way to set up a drone connection is using the dedicated setup script:

```bash
python setup_drone.py --wizard
```

This will guide you through the process of:

1. Naming your drone configuration
2. Entering the hostname or IP address
3. Providing username and password
4. Testing the connection
5. Deciding whether to save the password

### Using NMB Command Line

You can also manage drone configurations using the NMB command-line interface:

```bash
# Run the setup wizard
python nmb.py --drone-config wizard

# List all drone configurations
python nmb.py --drone-config list

# Add a new drone configuration
python nmb.py --drone-config add --drone-name lab_drone --drone-hostname 192.168.1.10 --username admin --password mypassword --save-drone-password

# Test a drone configuration
python nmb.py --drone-config test --drone-name lab_drone

# Remove a drone configuration
python nmb.py --drone-config remove --drone-name lab_drone
```

## Using Saved Drone Configurations

Once you've set up a drone configuration, you can use it in any NMB command by specifying just the name:

```bash
# Test connection
python nmb.py -d lab_drone -m test-connection

# Deploy a scan
python nmb.py -d lab_drone -m deploy -c client_project -s core --targets-file targets.txt

# Export results
python nmb.py -d lab_drone -m export -c client_project
```

This works with all NMB modes and commands. The system will automatically retrieve the hostname, username, and password (if saved) from the configuration.

## Managing Drone Configurations

You can manage your drone configurations using the following commands:

```bash
# List all configured drones
python setup_drone.py --list

# Test a drone connection
python setup_drone.py --test lab_drone

# Delete a drone configuration
python setup_drone.py --delete lab_drone
```

## Password Security

When setting up a drone configuration, you have the option to save the password. Please note:

- Saved passwords are stored in a configuration file in your home directory
- Passwords are stored in plain text
- If you choose not to save the password, you will be prompted for it when needed
- For maximum security, it's recommended to not save passwords

## Troubleshooting

If you encounter issues with drone connections:

1. **Connection failures**: 
   - Verify the hostname/IP is correct
   - Ensure you have network connectivity to the drone
   - Confirm the username and password are correct
   - Check if the drone is accessible (ping, traceroute)

2. **Configuration not found**:
   - Run `python setup_drone.py --list` to verify your configurations
   - Ensure you're using the exact name you specified during setup

3. **Permission issues**:
   - The configuration file is stored in `~/.bsti/drone_config.json`
   - Check that you have read/write permissions to this file

## Technical Details

The Drone Connection Manager consists of:

- `scripts/drone_config.py`: Core implementation with the DroneConfigManager class
- `scripts/drone_manager.py`: Command-line interface for the configuration manager
- `setup_drone.py`: User-friendly wrapper script for common operations

Configurations are stored in:
- `~/.bsti/drone_config.json` (Linux/macOS)
- `%USERPROFILE%\.bsti\drone_config.json` (Windows) 
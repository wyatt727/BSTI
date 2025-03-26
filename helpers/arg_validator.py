from typing import Any
import os 
from getpass import getpass
class DirectoryNotFoundException(Exception):
    def __init__(self, missing_directories):
        self.missing_directories = missing_directories
        super().__init__(f"Directories not found: {', '.join(missing_directories)}")

class MissingAttributesException(Exception):
    def __init__(self, missing_attributes):
        self.missing_attributes = missing_attributes
        super().__init__(f"Missing required arguments: {', '.join(missing_attributes)}")

class ArgumentValidator:
    REQUIRED_INTERACTIVE: list[str] = ['target_plextrac', 'username', 'password']
    REQUIRED_NON_INTERACTIVE: list[str] = [
        'target_plextrac', 'directory', 'report_id', 'client_id',
        'username', 'password', 'scope' 
    ]
    DIRECTORIES_TO_CHECK: list[str] = ['directory', 'screenshot_dir']

    def __init__(self, args: Any) -> None:
        """Initializes the validator and performs validation."""
        self.args = args
        self.validate_args()

    def print_banner(self) -> None:
        """Prints the banner containing the configuration."""
        self._print_header_footer()
        print("Nessus2Plextrac-ng - Configuration".center(60))
        self._print_header_footer()
        self._print_item("Target Plextrac Server", self.args.target_plextrac)
        self._print_item("Nessus Files Directory", self.args.directory)
        self._print_item("Report ID", self.args.report_id)
        self._print_item("Client ID", self.args.client_id)
        self._print_item("Username", self.args.username)
        self._print_item("Password", '*' * len(self.args.password))
        self._print_item("Scope", self.args.scope)
        self._print_item("Screenshot Directory", self.args.screenshot_dir)
        self._print_item("Non-Core Custom Fields", self.args.non_core)
        self._print_item("Custom Client Configuration", self.args.client_config)
        self._print_item("Report Link: ", f"https://{self.args.target_plextrac}.kevlar.bulletproofsi.net/client/{self.args.client_id}/report/{self.args.report_id}")
        self._print_header_footer()
        print("\n")

    def _print_header_footer(self) -> None:
        """Prints the header and footer lines for the banner."""
        print("=" * 60)

    def _print_item(self, key: str, value: Any) -> None:
        """Prints a single configuration item."""
        print(f"{key.ljust(30)}: {value}")

    def validate_args(self) -> None:
        """Validates the arguments."""
        self._validate_attributes()
        self._validate_directories()

    def _validate_attributes(self) -> None:
        """Validates that all required attributes are present."""
        required_attrs = self.REQUIRED_INTERACTIVE if self.args.create else self.REQUIRED_NON_INTERACTIVE
        missing_attrs = [attr for attr in required_attrs if not hasattr(self.args, attr) or getattr(self.args, attr) is None]

        for attr in missing_attrs:
            if attr == 'password':
                user_input = getpass(f"Please enter {attr}: ")
            else:
                user_input = input(f"Please enter {attr}: ")
            
            setattr(self.args, attr, user_input)

        # Re-check for any missing attributes
        missing_attrs = [attr for attr in required_attrs if not hasattr(self.args, attr) or getattr(self.args, attr) is None]
        if missing_attrs:
            raise MissingAttributesException(missing_attrs)

    def _validate_png_files(self, directory: str) -> None:
        """Validates that the directory contains .png files."""
        png_files = [f for f in os.listdir(directory) if f.endswith('.png')]
        if not png_files:
            raise Exception (f"No .png files found in directory {directory}")

    def _validate_directories(self) -> None:
        """Validates that specified directories exist and have required contents."""
        missing_dirs = []
        for directory in self.DIRECTORIES_TO_CHECK:
            dir_path = getattr(self.args, directory, None)
            if dir_path and not (os.path.exists(dir_path) and os.path.isdir(dir_path)):
                missing_dirs.append(dir_path)
            elif directory == 'screenshot_dir':
                if self.args.screenshot_dir:
                    self._validate_png_files(dir_path)
        if missing_dirs:
            raise DirectoryNotFoundException(missing_dirs)
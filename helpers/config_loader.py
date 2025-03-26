import json
from typing import Dict
class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> Dict:
        """Loads the configuration file."""
        with open(config_path, 'r') as f:
            return json.load(f)
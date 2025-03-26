# Version of NMB adapted to fit bsti requirements 
# Author: Connor Fancy
# Version: 1.0
import argparse
import sys
import signal
import os
import pretty_errors
from scripts.nessus import Nessus
from scripts.creator import GenConfig
from scripts.lackey import Lackey
from scripts.logging_config import log

# ================== Utility Functions ==================

class CredentialsCache:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

    def get_creds(self):
        return self.username, self.password

def find_policy_file(project_scope):
    policies = {
        'core': "Default Good Model Nessus Vulnerability Policy.nessus",
        'nc': "Custom_Nessus_Policy-Pn_pAll_AllSSLTLS-Web-NoLocalCheck-NoDOS.nessus"
    }
    
    # If project_scope is 'custom', prompt the user for the path
    if project_scope == 'custom':
        custom_path = input("Please enter the path to your custom policy file: ").strip()
        return os.path.normpath(custom_path)
    
    policy_dir = os.path.join(os.getcwd(), "Nessus-policy")
    return os.path.normpath(os.path.join(policy_dir, policies.get(project_scope, "")))


def read_burp_targets(targets_file_path):
    with open(targets_file_path, 'r') as targets_file:
        return [url.strip() for url in targets_file.readlines() if url.strip()]

def read_credentials(username_file_path, password_file_path):
    try:
        if not username_file_path:
            return
        with open(username_file_path, 'r') as username_file, open(password_file_path, 'r') as password_file:
            usernames = [u.strip() for u in username_file.read().split('\n') if u.strip()]
            passwords = [p.strip() for p in password_file.read().split('\n') if p.strip()]
            return usernames, passwords
    except Exception as e:
        log.warning(f"Burp scan will be executed without credentials due to: {str(e)}")
        return None, None

def determine_execution_mode(args):
    # Return True if we want to run locally, False if we want to run on the drone
    # For internal mode, explicitly use drone unless --local is passed
    is_local = args.local is True
    log.info(f"Execution mode: {'LOCAL' if is_local else 'DRONE'}")
    return is_local

def signal_handler(signal, frame):
    print()
    log.warning("Ctrl+C detected. Exiting...")
    sys.exit(0)


# ================== Mode Handlers ==================

def handle_mode(args, mode, required_args, handler_info):
    if getattr(args, 'local', False) and "drone" in required_args:
        required_args.remove("drone")
    
    missing_args = [arg for arg in required_args if not getattr(args, arg)]
    if missing_args:
        log.error(f"Missing required arguments for {mode} mode: {', '.join(missing_args)}")
        sys.exit(1)
    
    # Handle modes that use the old structure
    if 'handler_class' in handler_info:
        handler_classes_with_args_providers = [(handler_info['handler_class'], handler_info['handler_args_providers'])]
    else:
        handler_classes_with_args_providers = handler_info['handler_classes_with_args_providers']
    
    try:
        for handler_class, handler_args_providers in handler_classes_with_args_providers:
            handler_args = []
            handler_kwargs = {}
            for provider in handler_args_providers:
                result = provider(args)
                if isinstance(result, tuple):
                    handler_args.extend(result)
                elif isinstance(result, dict):
                    handler_kwargs.update(result)
                else:
                    handler_args.append(result)
            
            handler_class(*handler_args, **handler_kwargs)

    except Exception as e:
        log.error(f"An error occurred during {mode} execution: {str(e)}")



# === Main Execution ===
def main():
    signal.signal(signal.SIGINT, signal_handler)
    args = parse_arguments()
    creds_cache = CredentialsCache(username=args.username, password=args.password)

    mode_config = {
        "deploy": {
            "required_args": ["client", "drone", "project_type", "targets_file"],
            "handler_classes_with_args_providers": [
                (Nessus, [
                    lambda args: args.drone, 
                    lambda _: creds_cache.get_creds(),
                    lambda _: args.mode,
                    lambda args: args.client,
                    lambda args: find_policy_file(args.project_type), 
                    lambda args: args.targets_file,
                    lambda args: args.exclude_file, 
                    lambda args: args.discovery
                ]),
                (Lackey, [
                    lambda args: args.csv_file or f"{args.client}.csv",
                    lambda _: None,
                    lambda args: determine_execution_mode(args),
                    lambda _: creds_cache.get_creds() if not getattr(args, 'local', False) else (None, None),
                    lambda args: args.drone
                ])
            ]
        },
        "internal": {
            "required_args": ["drone", "csv_file"],
            "handler_class": Lackey,
            "handler_args_providers": [lambda args: args.csv_file,
                                       lambda _: None,
                                       lambda args: determine_execution_mode(args),
                                       lambda _: creds_cache.get_creds() if not getattr(args, 'local', False) else (None, None),
                                       lambda args: args.drone]
        },
        "external": {
            "required_args": ["drone", "csv_file"],
            "handler_class": Lackey,
            "handler_args_providers": [lambda args: args.csv_file,
                                       lambda _: True,
                                       lambda args: determine_execution_mode(args),
                                       lambda _: creds_cache.get_creds() if not getattr(args, 'local', False) else (None, None),
                                       lambda args: args.drone]
        },
        "create": {
            "required_args": ["client", "drone", "project_type", "targets_file"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: args.mode,
                                       lambda args: args.client,
                                       lambda args: find_policy_file(args.project_type), 
                                       lambda args: args.targets_file,
                                       lambda args: args.exclude_file, 
                                       lambda args: args.discovery]
        },
        "launch": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: args.mode,
                                       lambda args: args.client]
        },
        "pause": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: args.mode,
                                       lambda args: args.client]
        },
        "resume": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: args.mode,
                                       lambda args: args.client]
        },
        "monitor": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: args.mode,
                                       lambda args: args.client]
        },

        "regen": {
            "required_args": [],
            "handler_class": GenConfig,
            "handler_args_providers": [lambda _: {"regen": True}]
        },


        "export": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: args.mode,
                                       lambda args: args.client]
        }
    }

    mode_info = mode_config.get(args.mode)
    if not mode_info:
        log.error("Invalid mode selected")
        print("Options are: [deploy, create, launch, pause, resume, monitor, export, internal, external]")
        sys.exit(1)

    handle_mode(args, args.mode, mode_config[args.mode]["required_args"], mode_config[args.mode])



# === Argument Parsing ===
def parse_arguments():
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser(
        usage = "nmb.py [OPTIONS]",
        formatter_class = argparse.RawTextHelpFormatter,
        epilog = "Example:\n" \
                 "nmb.py -d storm -c myclient -m deploy -s core -u bstg -p password --csv-file path/to/csv\n" \
    )
    parser.add_argument("-m", "--mode", required=False, choices=["deploy","create","launch","pause","resume","monitor","export", "external", "internal", "regen"], help="" \
        "choose mode to run Nessus:\n" \
        "deploy: update settings, upload policy file, upload targets file, launch scan, monitor scan, export results, analyze results\n" \
        "create: update settings, upload policy file, upload targets files\n" \
        "launch: launch scan, export results, analyze results\n" \
        "pause: pause scan\n" \
        "resume: resume scan, export results, analyze results\n" \
        "monitor: monitor scan\n" \
        "export: export scan results, analyze results\n" \
        "external: perform nmap scans, manual finding verification, generate external report, take screenshots\n" \
        "internal: perform nmap scans, manual finding verification, generate internal report, take screenshots\n" \
        "regen: Regenerates 'NMB_config.json'"
    )

    # UTIL
    parser.add_argument("-u", "--username", required=False, help="Username for the drone")
    parser.add_argument("-p", "--password", required=False, help="Password for the drone")
    parser.add_argument("--targets-file", required=False, help="Path to the txt file")
    parser.add_argument("--csv-file", required=False, help="Path to the csv file")


    # INTERNAL/EXTERNAL
    parser.add_argument("-d", "--drone", required=False, help="drone name or IP")
    parser.add_argument("-c", "--client-name", dest="client", required=False, help="client name or project name (used to name the scan and output files)")
    parser.add_argument("-s", "--scope", dest="project_type", required=False, choices=["core", "nc", "custom"], help="Specify if core, custom or non-core policy file")
    parser.add_argument("-e", "--exclude-file", dest="exclude_file", required=False, help="exclude targets file", type=argparse.FileType('r'))
    parser.add_argument("-ex", "--external", dest="external", required=False, action="store_const", const=True, help="Enable external mode")
    parser.add_argument("-l", "--local", dest="local", required=False, action="store_const", const=True, help="run manual checks on your local machine instead of over ssh")
    parser.add_argument("--discovery", dest="discovery", required=False, action="store_const", const=True, help="Enable discovery scan prior to running nessus.")

    args = parser.parse_args()
    return args

    
if __name__ == '__main__':
    log.info("---------------Welcome to NMB----------------")
    main()

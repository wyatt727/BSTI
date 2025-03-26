import io
import json
import logging.config
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

from contextlib import closing
from shutil import which
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from pyaxmlparser import APK

from apkleaks.colors import color as col
from apkleaks.utils import util


class APKLeaks:
    def __init__(self, args):
        self.file = os.path.realpath(args.file)
        self.apk = self.apk_info()
        self.json = args.json
        self.disarg = args.args
        self.prefix = "apkleaks-"
        self.tempdir = tempfile.mkdtemp(prefix=self.prefix)
        self.main_dir = os.path.dirname(os.path.realpath(__file__))
        self.tools_dir = "tools"
        self.output = tempfile.mkstemp(suffix=".%s" % ("json" if self.json else "txt"), prefix=self.prefix)[1] if args.output is None else args.output
        self.fileout = open(self.output, "%s" % ("w" if self.json else "a"))
        self.pattern = os.path.join(str(Path(self.main_dir).parent), "config", "regexes.json") if args.pattern is None else args.pattern
        
        # Resolve the path to the jadx binary
        self.jadx = which("jadx")
        if self.jadx is None:
            self.jadx = os.path.join(self.tools_dir, "jadx", "bin", "jadx%s" % (".bat" if os.name == "nt" else ""))
        
        self.out_json = {}
        self.scanned = False
        logging.config.dictConfig({"version": 1, "disable_existing_loggers": True})

    def dependencies(self):
        # Path to the jadx binary
        jadx_bin = os.path.join(self.tools_dir, "jadx", "bin", "jadx%s" % (".bat" if os.name == "nt" else ""))
        
        # Debug print for path
        print(f"Checking for Jadx binary at: {jadx_bin}")
        
        # Check if jadx binary exists
        if not os.path.isfile(jadx_bin):
            exter = "https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip"
            try:
                # Download and extract jadx if it does not exist
                print("Jadx not found. Downloading...")
                with closing(urlopen(exter)) as response:
                    with ZipFile(io.BytesIO(response.read())) as zfile:
                        zfile.extractall(self.tools_dir)
                
                # Make the jadx binary executable if on a non-Windows OS
                if os.name != "nt":
                    os.chmod(jadx_bin, 0o755)
                print("Jadx downloaded and extracted successfully.")
            except Exception as error:
                print(f"Error downloading or extracting jadx: {error}")
                sys.exit()
        else:
            print("Jadx already exists. No need to download.")
    
    def decompile(self):
        # Ensure jadx exists
        if not os.path.isfile(self.jadx):
            raise FileNotFoundError(f"Jadx binary not found at {self.jadx}")
        
        args = [self.jadx, self.file, "-d", self.tempdir]
        if self.disarg:
            args.extend(re.split(r"\s|=", self.disarg))
        
        # Debug print for command
        print(f"Running decompile with command: {' '.join(args)}")
        
        # Use subprocess for better handling of command execution
        subprocess.run(args, check=True)

    def apk_info(self):
        return APK(self.file)

    def extract(self, name, matches):
        if len(matches):
            stdout = ("[%s]" % (name))
            self.fileout.write("%s" % (stdout + "\n" if self.json is False else ""))
            for secret in matches:
                if name == "LinkFinder":
                    if re.match(r"^.(L[a-z]|application|audio|fonts|image|kotlin|layout|multipart|plain|text|video).*\/.+", secret) is not None:
                        continue
                    secret = secret[len("'"):-len("'")]
                stdout = ("- %s" % (secret))
                self.fileout.write("%s" % (stdout + "\n" if self.json is False else ""))
            self.fileout.write("%s" % ("\n" if self.json is False else ""))
            self.out_json["results"].append({"name": name, "matches": matches})
            self.scanned = True

    def scanning(self):
        if self.apk is None:
            sys.exit(util.writeln("** Undefined package. Exit!", col.FAIL))
        self.out_json["package"] = self.apk.package
        self.out_json["results"] = []
        with open(self.pattern) as regexes:
            regex = json.load(regexes)
            for name, pattern in regex.items():
                if isinstance(pattern, list):
                    for p in pattern:
                        try:
                            thread = threading.Thread(target=self.extract, args=(name, util.finder(p, self.tempdir)))
                            thread.start()
                        except KeyboardInterrupt:
                            sys.exit(util.writeln("\n** Interrupted. Aborting...", col.FAIL))
                else:
                    try:
                        thread = threading.Thread(target=self.extract, args=(name, util.finder(pattern, self.tempdir)))
                        thread.start()
                    except KeyboardInterrupt:
                        sys.exit(util.writeln("\n** Interrupted. Aborting...", col.FAIL))

    def cleanup(self):
        shutil.rmtree(self.tempdir)
        if self.scanned:
            self.fileout.write("%s" % (json.dumps(self.out_json, indent=4) if self.json else ""))
            self.fileout.close()
            print("%s\n** Results saved into '%s%s%s%s'%s." % (col.HEADER, col.ENDC, col.OKGREEN, self.output, col.HEADER, col.ENDC))
        else:
            self.fileout.close()
            os.remove(self.output)


import xml.etree.ElementTree as XML
import os
import sys

class Analyzer:
    def __init__(self, scan_file, output_folder, drone):
        self.scan_file = scan_file
        self.output_folder = output_folder
        self.drone = drone

    def analyze_results(self):
        try:
            remote_file = self.drone.upload(self.scan_file)
            tmp_dir = "/tmp/eyewitness_output"
            self.drone.execute(f"mkdir -p {tmp_dir}")

            # Execute Eyewitness and direct the output to the temporary directory
            self.drone.execute(f"eyewitness --timeout 15 -x {remote_file} --no-prompt -d {tmp_dir}")

            # Zip the Eyewitness output directory
            zip_file = "/tmp/eyewitness_output.zip"
            self.drone.execute(f"zip -r {zip_file} {tmp_dir}")

            # Download the zipped results
            local_zip_path = os.path.join(self.output_folder, os.path.basename(zip_file))
            self.drone.download(zip_file, local_zip_path)

            # Clean up the remote temporary files
            self.drone.execute(f"rm -rf {tmp_dir}")
            self.drone.execute(f"rm {zip_file}")

            return local_zip_path

        except Exception as e:
            print(e)
            sys.exit()

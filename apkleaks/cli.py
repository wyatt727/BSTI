from apkleaks.apkleaks import APKLeaks
import os 

def run_apkleaks(apk_file, output=None, pattern=None, args=None, json_output=False):
    class Args:
        def __init__(self, file, output, pattern, args, json):
            self.file = file
            self.output = output
            self.pattern = pattern
            self.args = args
            self.json = json

    
    args_obj = Args(apk_file, output, pattern, args, json_output)
    
    apkleaks = APKLeaks(args_obj)
    
    try:
        apkleaks.dependencies()
        apkleaks.decompile()
        apkleaks.scanning()
    finally:
        apkleaks.cleanup()
    
    if apkleaks.output and os.path.exists(apkleaks.output):
        return apkleaks.output
    return None

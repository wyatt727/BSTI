#!/usr/bin/env python3
import traceback
import sys

try:
    from bsti_refactored import main
    main()
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1) 
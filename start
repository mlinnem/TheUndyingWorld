#!/usr/bin/env python3

import subprocess
import os

def main():
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    try:
        # Run server.py
        subprocess.run(['python', 'server.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running server.py: {e}")
        exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        exit(0)

if __name__ == "__main__":
    main()

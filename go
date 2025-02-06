#!/usr/bin/env python3

import subprocess
import os

def main():
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    try:
        # Install required packages
        subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True)
        
        # Run server.py
        subprocess.run(['python', 'app.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running server.py: {e}")
        exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        exit(0)

if __name__ == "__main__":
    # Clear the terminal before running main
    os.system('clear' if os.name == 'posix' else 'cls')
    main()

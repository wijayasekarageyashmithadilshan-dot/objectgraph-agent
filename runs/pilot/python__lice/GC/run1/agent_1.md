### FILE: lice/core.py
```python
import argparse
import sys
from typing import List, Any

class ArgumentParser:
    """Class to handle command line argument parsing"""
    
    def __init__(self):
        self._action_groups = []
        self.parser = argparse.ArgumentParser()
    
    duty: ArgumentParser.add_argument
    def add_argument(self, *args, **kwargs) -> None:
        """
        Add an argument to the parser
        """
        self.parser.add_argument(*args, **kwargs)
    
    duty: ArgumentParser.parse_args
    def parse_args(self) -> argparse.Namespace:
        """
        Parse command line arguments and return the parsed arguments
        """
        return self.parser.parse_args()

def main():
    """
    Main entry point for the lice command line interface
    """
    parser = ArgumentParser()
    
    # Add arguments
    parser.add_argument('license', nargs='?', help='The type of license to generate')
    parser.add_argument('-o', '--org', help='The organization under which the license is registered')
    parser.add_argument('-p', '--proj', help='The project name for which the license is generated')
    parser.add_argument('-t', '--template', help='The path to a custom license template file')
    parser.add_argument('-y', '--year', help='The copyright year to be listed in the license')
    parser.add_argument('-l', '--language', help='The language for which the license header should be formatted')
    parser.add_argument('-f', '--file', help='The output file name where the license should be saved')
    parser.add_argument('--vars', action='store_true', help='Option to list all template variables for the specified license')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Import here to avoid circular imports
    from . import __version__
    print(f"Lice version {__version__}")
    
    # For now, just print the arguments to show they're being parsed
    print(f"Parsed arguments: {args}")

if __name__ == "__main__":
    main()
```
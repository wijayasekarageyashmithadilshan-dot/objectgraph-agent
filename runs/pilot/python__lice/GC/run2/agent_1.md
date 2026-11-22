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
        """Add an argument to the parser"""
        self.parser.add_argument(*args, **kwargs)
    
    duty: ArgumentParser.parse_args
    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments and return the result"""
        return self.parser.parse_args()
```
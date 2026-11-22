### FILE: lice/core.py
```python
import sys
import os
from io import StringIO

class StringIO:
    def __init__(self):
        self._buffer = []
        self._closed = False
    
    def write(self, str):
        """duty: StringIO.write"""
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        self._buffer.append(str)
    
    def getvalue(self):
        """duty: StringIO.getvalue"""
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return ''.join(self._buffer)
    
    def close(self):
        """duty: StringIO.close"""
        self._closed = True
        self._buffer = None
    
    def seek(self, index):
        """duty: StringIO.seek"""
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        if index < 0 or index > len(self._buffer):
            raise ValueError("Invalid seek position")
        # For simplicity, we'll just truncate the buffer
        # In a real implementation, this would require more complex handling
        self._buffer = self._buffer[:index]
    
    def readlines(self):
        """duty: StringIO.readlines"""
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return self.getvalue().splitlines(True)
```
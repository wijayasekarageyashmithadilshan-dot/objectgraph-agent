### FILE: lice/core.py
```python
import sys
import os
from io import StringIO

# duty: StringIO.write
def write(self, str):
    self.buf.write(str)

# duty: StringIO.getvalue
def getvalue(self):
    return self.buf.getvalue()

# duty: StringIO.close
def close(self):
    self.buf.close()

# duty: StringIO.seek
def seek(self, index):
    self.buf.seek(index)

# duty: StringIO.readlines
def readlines(self):
    return self.buf.readlines()

# Monkey patch the StringIO class with our methods
StringIO.write = write
StringIO.getvalue = getvalue
StringIO.close = close
StringIO.seek = seek
StringIO.readlines = readlines
```
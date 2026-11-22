### FILE: lice/core.py
```python
import os
import sys
from argparse import ArgumentParser

# Assuming these are defined elsewhere in the codebase
# from . import LICENSES
# from ._init_ import __version__

class Context:
    """Context holds the configuration data for license generation."""
    
    def __init__(self, year=None, organization=None, project=None):
        self._year = year
        self._organization = organization
        self._project = project

    @property
    def year(self):
        """Get the copyright year."""
        return self._year

    @year.setter
    def year(self, value):
        """Set the copyright year."""
        self._year = value

    @property
    def organization(self):
        """Get the organization name."""
        return self._organization

    @organization.setter
    def organization(self, value):
        """Set the organization name."""
        self._organization = value

    @property
    def project(self):
        """Get the project name."""
        return self._project

    @project.setter
    def project(self, value):
        """Set the project name."""
        self._project = value

duty: Context.<state>
```
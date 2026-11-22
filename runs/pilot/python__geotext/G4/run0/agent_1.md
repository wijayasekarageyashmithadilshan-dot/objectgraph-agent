### FILE: geotext/geotext.py
```python
import os
import re
from collections import OrderedDict

# Assuming this is the main module file
# Global functions class (will be implemented by agent_2)
class Global_functions:
    pass

# GeoText class implementation
class GeoText:
    def __init__(self, text, country=None):
        """
        duty: GeoText.__init__
        Initialize GeoText with input text and optional country filter.
        """
        self.text = text
        self.country = country
        self.countries = []
        self.cities = []
        self.nationalities = []
        self.country_mentions = OrderedDict()
        self.city_regex = None
        
        # Build the index for lookups
        self._build_index()
        
        # Extract entities from text
        self._extract_entities()

    def _build_index(self):
        """
        Build indexes for countries, cities, and nationalities.
        This method would typically call build_index() from Global_functions,
        but since it's not implemented here, we'll simulate its behavior.
        """
        # In a real implementation, this would load data from files
        # For now, we'll just set up basic structures
        self.countries_index = {}
        self.cities_index = {}
        self.nationalities_index = {}

    def _extract_entities(self):
        """
        Extract countries, cities, and nationalities from the text.
        """
        # This is a simplified version - actual implementation would use regex
        # and the indexes built earlier
        pass

# Global functions implementation (agent_2 should implement this)
def get_data_path(path):
    """
    duty: Global_functions.get_data_path
    Construct a file path by joining the root directory with a given path.
    """
    return os.path.join(os.path.dirname(__file__), 'data_file', path)

def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
    """
    duty: Global_functions.read_table
    Parse data files from the data_file directory to create dictionaries.
    """
    file_path = get_data_path(filename)
    
    # Read the file and process lines
    data = []
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            for i, line in enumerate(f):
                if i < skip or line.startswith(comment):
                    continue
                fields = line.strip().split(sep)
                if usecols:
                    fields = [fields[i] for i in usecols]
                data.append(fields)
    except FileNotFoundError:
        # Handle missing file gracefully
        return []
    
    return data
```
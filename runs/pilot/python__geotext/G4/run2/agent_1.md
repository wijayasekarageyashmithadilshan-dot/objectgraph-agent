### FILE: geotext/geotext.py
```python
import os
import re
from collections import OrderedDict

# Assuming the data files are in the same directory as this module
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data_file')

class GeoText:
    """Extracts city and country mentions from text."""
    
    def __init__(self, text, country=None):
        """
        Initialize GeoText with input text and optional country filter.
        
        Args:
            text (str): The text to analyze for geographical mentions
            country (str, optional): Country code to filter results by
        """
        self.text = text
        self.country = country
        self.countries = []
        self.cities = []
        self.nationalities = []
        self.country_mentions = OrderedDict()
        # This would be initialized by build_index() in the actual implementation
        self.city_regex = None
        
        # For now, we'll just set up the basic structure
        # In a real implementation, this would call build_index() and process the text
        pass

class Global_functions:
    """Contains global utility functions for the geotext library."""
    
    @staticmethod
    def get_data_path(path):
        """
        Construct a file path by joining the root directory with a given path.
        
        Args:
            path (str): The relative path to a data file
            
        Returns:
            str: Absolute path to the data file
        """
        return os.path.join(DATA_DIR, path)
    
    @staticmethod
    def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
        """
        Parse data files from the data_file directory to create dictionaries.
        
        Args:
            filename (str): Name of the file to read
            usecols (list, optional): Columns to use from the file
            sep (str): Separator character
            comment (str): Comment character to ignore lines
            encoding (str): File encoding
            skip (int): Number of lines to skip at the beginning
            
        Returns:
            list: List of rows from the parsed file
        """
        file_path = Global_functions.get_data_path(filename)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
                
            # Skip initial lines if needed
            lines = lines[skip:]
            
            # Filter out comment lines
            lines = [line for line in lines if not line.strip().startswith(comment)]
            
            # Parse each line
            result = []
            for line in lines:
                line = line.strip()
                if line:  # Only process non-empty lines
                    row = line.split(sep)
                    if usecols is not None:
                        row = [row[i] for i in usecols if i < len(row)]
                    result.append(row)
                    
            return result
            
        except FileNotFoundError:
            # Return empty list if file doesn't exist
            return []
        except Exception:
            # Return empty list if there's any other error
            return []
```
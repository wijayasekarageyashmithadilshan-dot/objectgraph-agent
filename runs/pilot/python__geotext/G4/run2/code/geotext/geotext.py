import os
import re
from collections import OrderedDict
from collections import OrderedDict, namedtuple


# Assuming the data files are in the same directory as this module
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data_file')


# Define the namedtuple for the index
Index = namedtuple('Index', ['cities', 'countries', 'nationalities'])


def get_data_path(path):
    """Construct a file path by joining the root directory with a given path."""
    return os.path.join(os.path.dirname(__file__), 'data_file', path)


def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
    """Parse data files from the data_file directory to create dictionaries."""
    data = []
    try:
        with open(get_data_path(filename), 'r', encoding=encoding) as f:
            for _ in range(skip):
                next(f)
            for line in f:
                if line.strip() and not line.startswith(comment):
                    row = line.strip().split(sep)
                    if usecols:
                        row = [row[i] for i in usecols]
                    data.append(row)
    except FileNotFoundError:
        # Handle missing files gracefully
        pass
    return data


def build_index():
    """Load data from text files in the data_file directory and create an index."""
    # Load cities data
    cities_data = read_table('cities15000.txt', usecols=[1, 2, 4], skip=0)
    cities_dict = {}
    for row in cities_data:
        if len(row) >= 3:
            city_name = row[0].lower()
            city_alternatives = row[1].lower().split(',')
            country_code = row[2]
            
            # Add main city name
            if city_name not in cities_dict:
                cities_dict[city_name] = set()
            cities_dict[city_name].add(country_code)
            
            # Add alternative names
            for alt_name in city_alternatives:
                alt_name = alt_name.strip()
                if alt_name and alt_name != city_name:
                    if alt_name not in cities_dict:
                        cities_dict[alt_name] = set()
                    cities_dict[alt_name].add(country_code)
    
    # Load country info
    countries_data = read_table('countryInfo.txt', usecols=[4, 1], skip=0)
    countries_dict = {}
    for row in countries_data:
        if len(row) >= 2:
            country_name = row[0].lower()
            country_code = row[1]
            countries_dict[country_name] = country_code
    
    # Load nationalities
    nationalities_data = read_table('nationalities.txt', usecols=[0], skip=0)
    nationalities_dict = {}
    for row in nationalities_data:
        if row:
            for item in row:
                if ':' in item:
                    nationality, code = item.split(':')
                    nationalities_dict[nationality.lower()] = code
    
    # Load city patches
    city_patches_data = read_table('citypatches.txt', usecols=[0, 1], skip=0)
    for row in city_patches_data:
        if len(row) >= 2:
            city_name = row[0].lower()
            country_code = row[1]
            if city_name not in cities_dict:
                cities_dict[city_name] = set()
            cities_dict[city_name].add(country_code)
    
    return Index(cities=cities_dict, countries=countries_dict, nationalities=nationalities_dict)


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

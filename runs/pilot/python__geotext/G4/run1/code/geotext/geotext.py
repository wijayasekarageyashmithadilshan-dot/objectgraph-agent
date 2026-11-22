import os
import re
from collections import OrderedDict
from collections import OrderedDict, namedtuple


# Assuming the data files are in the same directory as this module
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data_file')


# duty: Global_functions.get_data_path
def get_data_path(path):
    """
    Construct a file path by joining the root directory with a given path.
    
    Args:
        path (str): Relative path to a data file
        
    Returns:
        str: Absolute path to the data file
    """
    return os.path.join(DATA_DIR, path)


# duty: Global_functions.read_table
def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
    """
    Parse data files from the data_file directory to create dictionaries.
    
    Args:
        filename (str): Name of the file to read
        usecols (list, optional): Columns to read from the file
        sep (str): Separator character
        comment (str): Comment character to skip lines
        encoding (str): File encoding
        skip (int): Number of lines to skip at the beginning
        
    Returns:
        dict: Dictionary mapping keys to values based on the specified columns
    """
    data_dict = {}
    filepath = get_data_path(filename)
    
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            for _ in range(skip):
                next(f, None)
            
            for line in f:
                if line.strip() and not line.startswith(comment):
                    parts = line.strip().split(sep)
                    if usecols:
                        # Only process specified columns
                        selected_parts = [parts[i] for i in usecols if i < len(parts)]
                        key = selected_parts[0]
                        value = selected_parts[1] if len(selected_parts) > 1 else None
                    else:
                        key = parts[0]
                        value = parts[1] if len(parts) > 1 else None
                    
                    if key:
                        data_dict[key] = value
                        
    except FileNotFoundError:
        # Return empty dict if file doesn't exist
        pass
    
    return data_dict


# duty: Global_functions.build_index
def build_index():
    """
    Load data from text files in the data_file directory and create an index
    of nationalities, cities, and countries in the form of a namedtuple.
    """
    # Load nationalities
    nationalities = {}
    nat_data = read_table('nationalities.txt', usecols=[0, 1], sep=':')
    for key, value in nat_data.items():
        if value:
            nationalities[key] = value[0]
    
    # Load cities
    cities = {}
    city_data = read_table('cities15000.txt', usecols=[1, 2, 3, 4, 5])
    for key, value in city_data.items():
        if value:
            # Store city name and country code
            city_name = value[0]
            country_code = value[1] if len(value) > 1 else ''
            cities[city_name] = country_code
    
    # Load countries
    countries = {}
    country_data = read_table('countryInfo.txt', usecols=[4, 1])
    for key, value in country_data.items():
        if value:
            country_name = value[0]
            iso_code = value[1] if len(value) > 1 else ''
            countries[country_name] = iso_code
    
    # Create namedtuple for index
    Index = namedtuple('Index', ['nationalities', 'cities', 'countries'])
    return Index(nationalities=nationalities, cities=cities, countries=countries)


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

### FILE: geotext/geotext.py
```python
import os
import re
from collections import OrderedDict, namedtuple

# duty: Global_functions.get_data_path
def get_data_path(path):
    """Construct a file path by joining the root directory with a given path."""
    return os.path.join(os.path.dirname(__file__), 'data_file', path)

# duty: Global_functions.read_table
def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
    """
    Parse data files from the data_file directory to create dictionaries
    mapping terms to their corresponding values based on the specified columns.
    """
    data = {}
    filepath = get_data_path(filename)
    
    with open(filepath, 'r', encoding=encoding) as f:
        for _ in range(skip):
            next(f)
            
        for line in f:
            if line.strip() and not line.startswith(comment):
                parts = line.strip().split(sep)
                if usecols:
                    row = [parts[i] for i in usecols]
                else:
                    row = parts
                    
                # Use first column as key, rest as value
                key = row[0]
                value = row[1:] if len(row) > 1 else None
                data[key] = value
                
    return data

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
```
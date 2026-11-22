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
    """Parse data files from the data_file directory to create dictionaries."""
    data_path = get_data_path(filename)
    result = {}
    
    try:
        with open(data_path, 'r', encoding=encoding) as f:
            for _ in range(skip):
                next(f)
            
            for line in f:
                if line.strip() and not line.startswith(comment):
                    parts = line.strip().split(sep)
                    if usecols:
                        selected_parts = [parts[i] for i in usecols if i < len(parts)]
                        key = selected_parts[0]
                        value = selected_parts[1:] if len(selected_parts) > 1 else selected_parts[0]
                    else:
                        key = parts[0]
                        value = parts[1:]
                    
                    result[key] = value
    except FileNotFoundError:
        # Handle case where file doesn't exist
        pass
    
    return result

# duty: Global_functions.build_index
def build_index():
    """Load data from text files and create an index of nationalities, cities, and countries."""
    # Load nationalities
    nationalities_dict = read_table('nationalities.txt', usecols=[0, 1], sep=':', skip=0)
    
    # Load cities
    cities_dict = read_table('cities15000.txt', usecols=[1, 2], sep='\t', skip=0)
    
    # Load country info
    countries_dict = read_table('countryInfo.txt', usecols=[4, 1], sep='\t', skip=0)
    
    # Load city patches
    city_patches = read_table('citypatches.txt', usecols=[0, 1], sep='\t', skip=0)
    
    # Create namedtuple for the index
    Index = namedtuple('Index', ['nationalities', 'cities', 'countries', 'city_patches'])
    
    return Index(nationalities=nationalities_dict,
                 cities=cities_dict,
                 countries=countries_dict,
                 city_patches=city_patches)
```
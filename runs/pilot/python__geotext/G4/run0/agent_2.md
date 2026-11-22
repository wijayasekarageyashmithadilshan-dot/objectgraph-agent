### FILE: geotext/geotext.py
```python
import os
import re
from collections import namedtuple, OrderedDict

# Define the namedtuple for the index
Index = namedtuple('Index', ['cities', 'countries', 'nationalities'])

def get_data_path(path):
    """Construct a file path by joining the root directory with a given path."""
    return os.path.join(os.path.dirname(__file__), 'data_file', path)

def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
    """Parse data files from the data_file directory to create dictionaries."""
    data = {}
    try:
        with open(get_data_path(filename), 'r', encoding=encoding) as f:
            for _ in range(skip):
                next(f)
            for line in f:
                if line.strip() and not line.startswith(comment):
                    parts = line.strip().split(sep)
                    if usecols:
                        # Use only specified columns
                        selected_parts = [parts[i] for i in usecols if i < len(parts)]
                        key = selected_parts[0]
                        value = selected_parts[1] if len(selected_parts) > 1 else None
                    else:
                        # Use all columns
                        key = parts[0]
                        value = parts[1] if len(parts) > 1 else None
                    
                    if key:
                        data[key] = value
    except FileNotFoundError:
        print(f"Warning: {filename} not found.")
    return data

def build_index():
    """Load data from text files and create an index of nationalities, cities, and countries."""
    # Load cities data
    cities_data = read_table('cities15000.txt', usecols=[1, 2], sep='\t')
    # Extract city names and country codes
    cities = {}
    for city_name, country_code in cities_data.items():
        if country_code:
            if country_code not in cities:
                cities[country_code] = []
            cities[country_code].append(city_name)
    
    # Load country info
    countries_data = read_table('countryInfo.txt', usecols=[4, 1], sep='\t')
    countries = {}
    for country_name, iso_code in countries_data.items():
        if iso_code:
            countries[iso_code] = country_name
    
    # Load nationalities
    nationalities_data = read_table('nationalities.txt', usecols=[0, 1], sep=':')
    nationalities = {}
    for nationality_term, iso_code in nationalities_data.items():
        if iso_code:
            nationalities[nationality_term] = iso_code
    
    return Index(cities=cities, countries=countries, nationalities=nationalities)
```
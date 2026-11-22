### FILE: geotext/geotext.py
```python
import os
import pandas as pd
from collections import namedtuple, OrderedDict

# Define the namedtuple for the index
Index = namedtuple('Index', ['nationalities', 'cities', 'countries'])

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
    try:
        df = pd.read_csv(file_path, sep=sep, comment=comment, encoding=encoding, 
                         usecols=usecols, skiprows=skip, header=None)
        # Convert to dictionary, using first column as key and rest as values
        if len(df.columns) == 1:
            return dict(zip(df.iloc[:, 0], [None] * len(df)))
        else:
            return dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return {}

def build_index():
    """
    duty: Global_functions.build_index
    Load data from text files and create an index of nationalities, cities, and countries.
    """
    # Read nationalities
    nationalities = read_table('nationalities.txt', usecols=[0, 1], sep=':', encoding='utf-8')
    
    # Read cities
    cities = read_table('cities15000.txt', usecols=[1, 2], sep='\t', encoding='utf-8')
    
    # Read countries
    countries = read_table('countryInfo.txt', usecols=[4, 1], sep='\t', encoding='utf-8')
    
    return Index(nationalities=nationalities, cities=cities, countries=countries)
```
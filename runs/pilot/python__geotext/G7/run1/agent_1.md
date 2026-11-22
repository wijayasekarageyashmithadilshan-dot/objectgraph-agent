### FILE: geotext/geotext.py
```python
import os
import re
from collections import OrderedDict, namedtuple

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
                        # Use only specified columns
                        selected_parts = [parts[i] for i in usecols if i < len(parts)]
                        key = selected_parts[0]
                        value = selected_parts[1] if len(selected_parts) > 1 else None
                    else:
                        # Use all columns
                        key = parts[0]
                        value = parts[1] if len(parts) > 1 else None
                    
                    if key:
                        result[key] = value
    except FileNotFoundError:
        # Return empty dict if file not found
        pass
    
    return result

def build_index():
    """
    duty: Global_functions.build_index
    Load data from text files and create an index of nationalities, cities, and countries.
    """
    # Read nationalities
    nationalities = read_table('nationalities.txt', usecols=[0, 1], sep=':')
    
    # Read cities
    cities = read_table('cities15000.txt', usecols=[1, 2], sep='\t')
    
    # Read countries
    countries = read_table('countryInfo.txt', usecols=[4, 1], sep='\t')
    
    return Index(nationalities=nationalities, cities=cities, countries=countries)

class GeoText:
    """
    duty: GeoText.__init__
    Extract cities and countries from a given text.
    """
    def __init__(self, text, country=None):
        self.text = text
        self.country = country
        self.countries = []
        self.cities = []
        self.nationalities = []
        self.country_mentions = OrderedDict()
        
        # Build the index once during initialization
        self.index = build_index()
        
        # Build regex patterns
        self._build_city_regex()
        
        # Process the text
        self._extract_places()
    
    def _build_city_regex(self):
        """
        Build a regex pattern for city names.
        """
        # Get all city names from the index
        city_names = list(self.index.cities.keys())
        
        # Sort by length descending to match longer names first
        city_names.sort(key=len, reverse=True)
        
        # Escape special regex characters and join with OR operator
        escaped_cities = [re.escape(city) for city in city_names]
        city_pattern = '|'.join(escaped_cities)
        
        # Create regex with word boundaries
        self.city_regex = re.compile(r'\b(?:{})\b'.format(city_pattern), re.IGNORECASE)
    
    def _extract_places(self):
        """
        Extract countries, cities, and nationalities from the text.
        """
        # Find all potential matches
        potential_matches = set()
        
        # Find cities
        city_matches = self.city_regex.findall(self.text)
        for match in city_matches:
            # Check if this city exists in our index
            if match in self.index.cities:
                self.cities.append(match)
                potential_matches.add(match)
        
        # Find countries
        country_matches = set()
        for country_name, country_code in self.index.countries.items():
            if country_name.lower() in self.text.lower():
                country_matches.add(country_name)
                self.country_mentions[country_name] = self.country_mentions.get(country_name, 0) + 1
        
        # Add to countries list
        self.countries = list(country_matches)
        
        # Find nationalities
        nationality_matches = set()
        for nationality_term, country_code in self.index.nationalities.items():
            if nationality_term.lower() in self.text.lower():
                nationality_matches.add(nationality_term)
        
        self.nationalities = list(nationality_matches)
```

### FILE: geotext/__init__.py
```python
from .geotext import GeoText, get_data_path, read_table, build_index

__all__ = ['GeoText', 'get_data_path', 'read_table', 'build_index']
```
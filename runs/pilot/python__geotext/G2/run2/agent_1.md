### FILE: geotext/geotext.py
```python
import os
import re
from collections import OrderedDict, namedtuple

# Define the namedtuple for the index
Index = namedtuple('Index', ['nationalities', 'cities', 'countries'])

def get_data_path(path):
    """duty: Global_functions.get_data_path"""
    return os.path.join(os.path.dirname(__file__), 'data_file', path)

def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
    """duty: Global_functions.read_table"""
    data = {}
    filepath = get_data_path(filename)
    
    try:
        with open(filepath, 'r', encoding=encoding) as f:
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
        # Handle case where file doesn't exist
        pass
    
    return data

def build_index():
    """duty: Global_functions.build_index"""
    # Read nationalities
    nationalities = read_table('nationalities.txt', usecols=[0, 1], sep=':')
    
    # Read cities
    cities = read_table('cities15000.txt', usecols=[1, 2], sep='\t')
    
    # Read countries
    countries = read_table('countryInfo.txt', usecols=[4, 1], sep='\t')
    
    return Index(nationalities=nationalities, cities=cities, countries=countries)

class GeoText:
    """duty: GeoText.__init__"""
    def __init__(self, text, country=None):
        self.text = text
        self.country = country
        self.countries = []
        self.cities = []
        self.nationalities = []
        self.country_mentions = OrderedDict()
        
        # Build the index
        self.index = build_index()
        
        # Build regex patterns
        self._build_regex()
        
        # Extract entities
        self._extract_entities()
    
    def _build_regex(self):
        """Build regex patterns for city and country matching."""
        # Create city regex pattern
        city_names = list(self.index.cities.keys())
        escaped_cities = [re.escape(city) for city in city_names]
        self.city_regex = re.compile(r'\b(?:' + '|'.join(escaped_cities) + r')\b', re.IGNORECASE)
        
        # Create country regex pattern
        country_names = list(self.index.countries.keys())
        escaped_countries = [re.escape(country) for country in country_names]
        self.country_regex = re.compile(r'\b(?:' + '|'.join(escaped_countries) + r')\b', re.IGNORECASE)
        
        # Create nationality regex pattern
        nationality_terms = list(self.index.nationalities.keys())
        escaped_nationalities = [re.escape(term) for term in nationality_terms]
        self.nationality_regex = re.compile(r'\b(?:' + '|'.join(escaped_nationalities) + r')\b', re.IGNORECASE)
    
    def _extract_entities(self):
        """Extract countries, cities, and nationalities from text."""
        # Find all matches for countries
        country_matches = self.country_regex.findall(self.text)
        for match in country_matches:
            country_name = match
            # Get the country code from the index
            country_code = self.index.countries.get(country_name)
            if country_code:
                self.countries.append(country_name)
                # Update country mentions count
                if country_name in self.country_mentions:
                    self.country_mentions[country_name] += 1
                else:
                    self.country_mentions[country_name] = 1
        
        # Find all matches for cities
        city_matches = self.city_regex.findall(self.text)
        for match in city_matches:
            city_name = match
            # Check if we're filtering by country
            if self.country:
                # If we have a specific country filter, check if city belongs to it
                # This would require additional logic to map cities to countries
                # For now, just add the city
                self.cities.append(city_name)
            else:
                self.cities.append(city_name)
        
        # Find all matches for nationalities
        nationality_matches = self.nationality_regex.findall(self.text)
        for match in nationality_matches:
            nationality_term = match
            # Get the country code associated with this nationality
            country_code = self.index.nationalities.get(nationality_term)
            if country_code:
                self.nationalities.append(nationality_term)
```
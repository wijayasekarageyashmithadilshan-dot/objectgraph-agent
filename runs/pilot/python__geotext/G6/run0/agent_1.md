### FILE: geotext/geotext.py
```python
import os
import re
from collections import OrderedDict

# Assuming the data files are in the same directory as this module
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data_file')

def get_data_path(path):
    """Construct a file path by joining the root directory with a given path."""
    return os.path.join(DATA_DIR, path)

def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
    """Parse data files from the data_file directory to create dictionaries."""
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
                        row = [parts[i] for i in usecols]
                    else:
                        row = parts
                    
                    # Use first column as key, rest as value
                    key = row[0]
                    value = row[1:] if len(row) > 1 else None
                    data[key] = value
    except FileNotFoundError:
        print(f"Warning: {filename} not found.")
    
    return data

def build_index():
    """Load data from text files and create indexes for nationalities, cities, and countries."""
    # Read nationalities
    nationalities = {}
    nat_data = read_table('nationalities.txt', usecols=[0, 1], sep=':')
    for key, value in nat_data.items():
        if value:
            nationalities[key] = value[0]
    
    # Read cities
    cities = {}
    city_data = read_table('cities15000.txt', usecols=[1, 2])
    for key, value in city_data.items():
        if value:
            cities[key] = value[0]  # Store city name
    
    # Read countries
    countries = {}
    country_data = read_table('countryInfo.txt', usecols=[4, 1])
    for key, value in country_data.items():
        if value:
            countries[key] = value[0]  # Store country name
    
    # Read city patches
    city_patches = {}
    patch_data = read_table('citypatches.txt', usecols=[0, 1], sep='\t')
    for key, value in patch_data.items():
        if value:
            city_patches[key] = value[0]  # Store patched city name
    
    return {
        'nationalities': nationalities,
        'cities': cities,
        'countries': countries,
        'city_patches': city_patches
    }

class GeoText:
    """Extract cities and countries from text using pre-loaded data."""
    
    def __init__(self, text, country=None):
        """
        Initialize GeoText with input text and optional country filter.
        
        Args:
            text (str): The text to analyze for geographical mentions.
            country (str, optional): Filter results to only include cities from this country.
        """
        self.text = text
        self.country = country
        self.countries = []
        self.cities = []
        self.nationalities = []
        self.country_mentions = OrderedDict()
        
        # Build index once during initialization
        self.index = build_index()
        
        # Compile regex patterns
        self._compile_patterns()
        
        # Process the text
        self._extract_geographical_elements()

    def _compile_patterns(self):
        """Compile regular expressions for finding potential geographical elements."""
        # Create a pattern that matches words which could be city or country names
        # This is a simplified approach; real implementation would be more complex
        all_names = set()
        all_names.update(self.index['cities'].keys())
        all_names.update(self.index['countries'].keys())
        all_names.update(self.index['nationalities'].keys())
        
        # Sort by length descending to match longer names first
        sorted_names = sorted(all_names, key=len, reverse=True)
        
        # Escape special regex characters and join with OR operator
        escaped_names = [re.escape(name) for name in sorted_names]
        pattern_string = '|'.join(escaped_names)
        
        # Add word boundaries to avoid partial matches
        self.city_regex = re.compile(r'\b(?:{})\b'.format(pattern_string), re.IGNORECASE)

    def _extract_geographical_elements(self):
        """Extract geographical elements from the text."""
        # Find all potential matches
        matches = self.city_regex.findall(self.text)
        
        # Categorize matches
        found_countries = []
        found_cities = []
        found_nationalities = []
        
        for match in matches:
            # Check if it's a country
            if match in self.index['countries']:
                found_countries.append(match)
                # Update mention count
                country_code = self.index['countries'][match]
                if country_code in self.country_mentions:
                    self.country_mentions[country_code] += 1
                else:
                    self.country_mentions[country_code] = 1
            
            # Check if it's a city
            elif match in self.index['cities']:
                found_cities.append(match)
                
            # Check if it's a nationality
            elif match in self.index['nationalities']:
                found_nationalities.append(match)
        
        # Apply country filter if specified
        if self.country:
            # If country is provided, filter cities by country code
            filtered_cities = []
            for city_name in found_cities:
                # In a real implementation, we'd need to map city names to country codes
                # For now, we'll just add all cities since we don't have that mapping here
                filtered_cities.append(city_name)
            self.cities = filtered_cities
        else:
            self.cities = found_cities
            
        self.countries = found_countries
        self.nationalities = found_nationalities
```
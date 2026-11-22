import os
import re
from collections import OrderedDict
from collections import OrderedDict, namedtuple


# Assuming the data files are in the same directory as this module
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data_file')


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
                        value = parts[1:] if len(parts) > 1 else None
                    
                    result[key] = value
    except FileNotFoundError:
        # Handle case where file doesn't exist
        pass
    
    return result


def build_index():
    """Load data from text files in the data_file directory and create indexes."""
    # Read nationalities
    nationalities = {}
    nat_data = read_table('nationalities.txt', sep=':', usecols=[0, 1])
    for nat, code in nat_data.items():
        nationalities[nat] = code
    
    # Read countries
    countries = {}
    country_data = read_table('countryInfo.txt', usecols=[4, 1])
    for country_name, iso_code in country_data.items():
        countries[country_name] = iso_code
    
    # Read cities
    cities = {}
    city_data = read_table('cities15000.txt', usecols=[1, 2])
    for city_name, country_code in city_data.items():
        if country_code not in cities:
            cities[country_code] = []
        cities[country_code].append(city_name)
    
    # Read city patches
    city_patches = {}
    patch_data = read_table('citypatches.txt', sep='\t', usecols=[0, 1])
    for patch_name, country_code in patch_data.items():
        city_patches[patch_name] = country_code
    
    return nationalities, cities, countries, city_patches


class GeoText:
    """Extract cities and countries from text."""
    
    def __init__(self, text, country=None):
        """
        Initialize GeoText with text and optional country filter.
        
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
        
        # Build the index once during initialization
        self.nationalities_dict, self.cities_dict, self.countries_dict, self.city_patches = build_index()
        
        # Create regex patterns for city and country matching
        self._build_city_regex()
        self._extract_geographical_elements()
    
    def _build_city_regex(self):
        """Build regex pattern for city name matching."""
        # Get all city names from the dictionary
        all_cities = []
        for city_list in self.cities_dict.values():
            all_cities.extend(city_list)
        
        # Add patched city names
        all_cities.extend(list(self.city_patches.keys()))
        
        # Escape special regex characters and sort by length (longest first)
        escaped_cities = [re.escape(city) for city in all_cities]
        escaped_cities.sort(key=len, reverse=True)
        
        # Join into a single regex pattern
        city_pattern = '|'.join(escaped_cities)
        self.city_regex = re.compile(r'\b(?:{})\b'.format(city_pattern), re.IGNORECASE)
    
    def _extract_geographical_elements(self):
        """Extract countries, cities, and nationalities from the text."""
        # Find all potential matches using regex
        potential_matches = set()
        for match in self.city_regex.finditer(self.text):
            potential_matches.add(match.group())
        
        # Check each potential match against our databases
        found_cities = []
        found_countries = []
        found_nationalities = []
        
        # Check for cities
        for city in potential_matches:
            # Check if it's a known city
            is_city = False
            for country_code, city_list in self.cities_dict.items():
                if city in city_list:
                    found_cities.append(city)
                    is_city = True
                    break
            
            # Check if it's a patched city
            if not is_city and city in self.city_patches:
                found_cities.append(city)
                is_city = True
        
        # Check for countries
        for country_name, iso_code in self.countries_dict.items():
            if country_name.lower() in self.text.lower():
                found_countries.append(country_name)
                # Update mention count
                if country_name not in self.country_mentions:
                    self.country_mentions[country_name] = 0
                self.country_mentions[country_name] += 1
        
        # Check for nationalities
        for nat, code in self.nationalities_dict.items():
            if nat.lower() in self.text.lower():
                found_nationalities.append(nat)
        
        # Filter by country if specified
        if self.country:
            filtered_cities = []
            for city in found_cities:
                # Check if city belongs to the specified country
                for country_code, city_list in self.cities_dict.items():
                    if city in city_list and country_code == self.country:
                        filtered_cities.append(city)
                        break
                # Also check patched cities
                if city in self.city_patches and self.city_patches[city] == self.country:
                    filtered_cities.append(city)
            found_cities = filtered_cities
        
        self.cities = found_cities
        self.countries = found_countries
        self.nationalities = found_nationalities

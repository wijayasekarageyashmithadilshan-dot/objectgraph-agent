import os
import re
from collections import OrderedDict
from typing import List, Optional, Tuple
import pandas as pd
from collections import namedtuple, OrderedDict


# Assuming the data files are in the same directory as this module
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data_file')


# Build indexes once when module loads
NATIONALITIES, CITIES, COUNTRIES = build_index()


# Define the namedtuple for the index
Index = namedtuple('Index', ['nationalities', 'cities', 'countries'])


def get_data_path(path):
    """
    # duty: Global_functions.get_data_path
    Construct a file path by joining the root directory with a given path.
    """
    return os.path.join(os.path.dirname(__file__), 'data_file', path)


def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
    """
    # duty: Global_functions.read_table
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


def build_index() -> Tuple[dict, dict, dict]:
    """Load data from text files and create indexes for nationalities, cities, and countries."""
    # Load nationalities
    nationalities = {}
    nat_data = read_table('nationalities.txt', sep=':', usecols=[0, 1])
    for row in nat_data:
        if len(row) >= 2:
            nationalities[row[0]] = row[1]
    
    # Load cities
    cities = {}
    city_data = read_table('cities15000.txt', usecols=[1, 2, 4])
    for row in city_data:
        if len(row) >= 3:
            city_name = row[0].split(',')[0]  # Get first name
            country_code = row[2]
            if country_code not in cities:
                cities[country_code] = set()
            cities[country_code].add(city_name.lower())
    
    # Load countries
    countries = {}
    country_data = read_table('countryInfo.txt', usecols=[4, 1])
    for row in country_data:
        if len(row) >= 2:
            country_name = row[0]
            country_code = row[1]
            countries[country_name.lower()] = country_code
    
    return nationalities, cities, countries


class GeoText:
    """Extract cities and countries from text using pre-loaded data."""
    
    def __init__(self, text: str, country: Optional[str] = None):
        """
        Initialize GeoText with input text and optional country filter.
        
        Args:
            text: Input text to analyze
            country: Optional country code to filter results
        """
        self.text = text
        self.country = country
        
        # Initialize attributes
        self.countries = []
        self.cities = []
        self.nationalities = []
        self.country_mentions = OrderedDict()
        
        # Build regex patterns
        self._build_city_regex()
        
        # Process the text
        self._extract_places()
    
    def _build_city_regex(self) -> None:
        """Build regex pattern for city matching."""
        # This is a simplified approach; in practice, you'd want more sophisticated matching
        # For now, we'll just create a basic pattern that matches words
        # In a real implementation, this would be more complex
        self.city_regex = re.compile(r'\b\w+\b')
    
    def _extract_places(self) -> None:
        """Extract countries and cities from the text."""
        # Convert text to lowercase for case-insensitive matching
        lower_text = self.text.lower()
        
        # Extract countries
        for country_name, country_code in COUNTRIES.items():
            if country_name in lower_text:
                self.countries.append(country_name)
                if country_code not in self.country_mentions:
                    self.country_mentions[country_code] = 0
                self.country_mentions[country_code] += 1
        
        # Extract cities
        # This is a simplified version - in reality, you'd match against actual city lists
        # and potentially apply filters based on country if provided
        words = self.city_regex.findall(lower_text)
        for word in words:
            # Check if word matches any known city names
            # This is a placeholder - in a full implementation, you'd check against
            # the cities dictionary with appropriate filtering
            pass
        
        # Extract nationalities
        for nationality, code in NATIONALITIES.items():
            if nationality in lower_text:
                self.nationalities.append(nationality)

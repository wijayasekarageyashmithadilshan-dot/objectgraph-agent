import os
import re
from collections import OrderedDict, namedtuple

# Define the namedtuple for the index
Index = namedtuple('Index', ['nationalities', 'cities', 'countries'])

class GeoText:
    def __init__(self, text, country=None):
        """
        # duty: GeoText.__init__
        Initialize GeoText with input text and optional country filter.
        """
        self.text = text
        self.country = country
        self.countries = []
        self.cities = []
        self.nationalities = []
        self.country_mentions = OrderedDict()
        
        # Build the index once during initialization
        self.index = build_index()
        
        # Extract entities from text
        self._extract_entities()

    def _extract_entities(self):
        """
        Extract countries, cities, and nationalities from the text.
        """
        # Convert text to lowercase for case-insensitive matching
        lower_text = self.text.lower()
        
        # Find country mentions
        for country_name, iso_code in self.index.countries.items():
            if country_name.lower() in lower_text:
                self.countries.append(country_name)
                if country_name not in self.country_mentions:
                    self.country_mentions[country_name] = 0
                self.country_mentions[country_name] += 1
        
        # Find city mentions
        for city_name, country_code in self.index.cities.items():
            if city_name.lower() in lower_text:
                # If country filter is set, only include cities from that country
                if self.country is None or country_code == self.country:
                    self.cities.append(city_name)
        
        # Find nationality mentions
        for nationality_term, iso_code in self.index.nationalities.items():
            if nationality_term.lower() in lower_text:
                self.nationalities.append(nationality_term)

class Global_functions:
    @staticmethod
    def get_data_path(path):
        """
        # duty: Global_functions.get_data_path
        Construct a file path by joining the root directory with a given path.
        """
        return os.path.join(os.path.dirname(__file__), 'data_file', path)

    @staticmethod
    def read_table(filename, usecols=None, sep='\t', comment='#', encoding='utf-8', skip=0):
        """
        # duty: Global_functions.read_table
        Parse data files from the data_file directory to create dictionaries.
        """
        data_dict = {}
        file_path = Global_functions.get_data_path(filename)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                for i, line in enumerate(f):
                    if i < skip or line.startswith(comment):
                        continue
                    
                    parts = line.strip().split(sep)
                    if usecols:
                        # Use only specified columns
                        selected_parts = [parts[col] for col in usecols if col < len(parts)]
                        if len(selected_parts) >= 2:
                            key = selected_parts[0]
                            value = selected_parts[1]
                            data_dict[key] = value
                    else:
                        # Use all columns
                        if len(parts) >= 2:
                            key = parts[0]
                            value = parts[1]
                            data_dict[key] = value
        except FileNotFoundError:
            print(f"Warning: File {filename} not found.")
            
        return data_dict

    @staticmethod
    def build_index():
        """
        # duty: Global_functions.build_index
        Load data from text files and create an index of nationalities, cities, and countries.
        """
        # Read nationalities
        nationalities = Global_functions.read_table(
            'nationalities.txt',
            usecols=[0, 1],
            sep=':',
            encoding='utf-8'
        )
        
        # Read cities
        cities = Global_functions.read_table(
            'cities15000.txt',
            usecols=[1, 8],  # City name and country code
            sep='\t',
            encoding='utf-8'
        )
        
        # Read countries
        countries = Global_functions.read_table(
            'countryInfo.txt',
            usecols=[4, 1],  # Country name and ISO code
            sep='\t',
            encoding='utf-8'
        )
        
        # Return the index as a namedtuple
        return Index(nationalities=nationalities, cities=cities, countries=countries)

### FILE: lice/core.py
```python
import argparse
import sys
from typing import List, Any

class ArgumentParser:
    """Class to handle command line argument parsing"""
    
    def __init__(self):
        self._action_groups = []
        self.parser = argparse.ArgumentParser()
    
    duty: ArgumentParser.add_argument
    def add_argument(self, *args, **kwargs) -> None:
        """Add an argument to the parser"""
        self.parser.add_argument(*args, **kwargs)
    
    duty: ArgumentParser.parse_args
    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments and return the result"""
        return self.parser.parse_args()

def main():
    """Main entry point for the CLI"""
    parser = ArgumentParser()
    
    # Add arguments
    parser.add_argument('license', nargs='?', default=None,
                       help='The type of license to generate')
    parser.add_argument('-o', '--org', dest='organization',
                       help='The organization under which the license is registered')
    parser.add_argument('-p', '--proj', dest='project',
                       help='The project name for which the license is generated')
    parser.add_argument('-t', '--template', dest='template_path',
                       help='The path to a custom license template file')
    parser.add_argument('-y', '--year', dest='year',
                       help='The copyright year to be listed in the license')
    parser.add_argument('-l', '--language', dest='language',
                       help='The language for which the license header should be formatted')
    parser.add_argument('-f', '--file', dest='output_file',
                       help='The output file name where the license should be saved')
    parser.add_argument('--vars', action='store_true',
                       help='Option to list all template variables for the specified license')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Import here to avoid circular imports
    from . import __version__
    print(f"Lice version {__version__}")
    
    # Handle the case where no arguments are provided
    if len(sys.argv) == 1:
        parser.parser.print_help()
        return
    
    # Process the arguments
    try:
        # Import the global functions
        from ._global_functions import get_context, load_template, generate_license, \
            format_license, extract_vars, clean_path
        
        # Get context
        context = get_context(args)
        
        # If --vars flag is used, show variables and exit
        if args.vars:
            template = load_template(args.license, False)
            vars_list = extract_vars(template)
            print("Template variables:")
            for var in vars_list:
                print(f"  {var}")
            return
        
        # Load template
        template = load_template(args.license, bool(args.language))
        
        # Generate license
        license_text = generate_license(template, context)
        
        # Format if language is specified
        if args.language:
            license_text = format_license(license_text, args.language)
        
        # Output handling
        if args.output_file:
            # Write to file
            with open(args.output_file, 'w') as f:
                f.write(license_text)
        else:
            # Print to stdout
            print(license_text)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

# This is just to make the module runnable
if __name__ == "__main__":
    main()
```
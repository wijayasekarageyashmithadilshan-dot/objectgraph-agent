import argparse
import sys
from typing import List, Any
import os
from argparse import ArgumentParser
from io import StringIO
# Import datetime for year handling
import datetime


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


def clean_path(p):
    """duty: Global_functions.clean_path"""
    return os.path.abspath(os.path.expanduser(p))


def get_context(args):
    """duty: Global_functions.get_context"""
    context = Context()
    context.year = args.year or str(datetime.datetime.now().year)
    context.organization = args.organization or guess_organization()
    context.project = args.project or os.path.basename(os.getcwd())
    return context


def guess_organization():
    """Guess the organization from git config or USER env var"""
    # Try git config first
    try:
        import subprocess
        result = subprocess.run(['git', 'config', '--global', 'user.name'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    
    # Fall back to USER environment variable
    return os.environ.get('USER', 'Unknown')


def load_file_template(path):
    """duty: Global_functions.load_file_template"""
    with open(path, 'r') as f:
        content = f.read()
    string_io = StringIO()
    string_io.write(content)
    return string_io


def load_template(license_name, header=False):
    """duty: Global_functions.load_template"""
    # This is a simplified version - in reality this would load from templates directory
    template_path = f"templates/template-{license_name}{'-header' if header else ''}.txt"
    try:
        with open(template_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        # Return empty template if not found
        content = ""
    
    string_io = StringIO()
    string_io.write(content)
    return string_io


def extract_vars(template):
    """duty: Global_functions.extract_vars"""
    content = template.getvalue()
    # Simple regex to find variables like {{variable_name}}
    import re
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, content)
    return list(set(matches))  # Remove duplicates


def generate_license(template, context):
    """duty: Global_functions.generate_license"""
    content = template.getvalue()
    
    # Replace template variables
    replacements = {
        'year': context.year,
        'organization': context.organization,
        'project': context.project
    }
    
    for key, value in replacements.items():
        content = content.replace('{{' + key + '}}', value)
    
    # Create new StringIO with generated content
    result = StringIO()
    result.write(content)
    return result


def format_license(template, lang):
    """duty: Global_functions.format_license"""
    content = template.getvalue()
    
    # Language-specific comment formats
    comment_formats = {
        'py': '# ',
        'js': '// ',
        'java': '// ',
        'c': '// ',
        'cpp': '// ',
        'html': '<!-- ',
        'css': '/* ',
        'sh': '# ',
        'rb': '# ',
        'php': '// '
    }
    
    prefix = comment_formats.get(lang, '# ')
    
    if prefix == '/* ':
        # Special handling for CSS-style comments
        lines = content.split('\n')
        formatted_lines = [prefix + line if line.strip() else line for line in lines]
        formatted_lines[-1] += ' */'
        formatted_content = '\n'.join(formatted_lines)
    elif prefix == '<!-- ':
        # Special handling for HTML comments
        lines = content.split('\n')
        formatted_lines = [prefix + line if line.strip() else line for line in lines]
        formatted_lines[-1] += ' -->'
        formatted_content = '\n'.join(formatted_lines)
    else:
        # Regular prefix comment
        lines = content.split('\n')
        formatted_lines = [prefix + line if line.strip() else line for line in lines]
        formatted_content = '\n'.join(formatted_lines)
    
    result = StringIO()
    result.write(formatted_content)
    return result


def get_suffix(name):
    """duty: Global_functions.get_suffix"""
    parts = name.split('.')
    if len(parts) > 1:
        return parts[-1]
    return False


class ArgumentParser:
    """Class to handle command line argument parsing"""
    
    def __init__(self):
        self._action_groups = []
        self.parser = argparse.ArgumentParser()
    
    # duty: ArgumentParser.add_argument
    def add_argument(self, *args, **kwargs) -> None:
        """Add an argument to the parser"""
        self.parser.add_argument(*args, **kwargs)
    
    # duty: ArgumentParser.parse_args
    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments and return the result"""
        return self.parser.parse_args()


# Define the Context class
class Context:
    def __init__(self, year=None, organization=None, project=None):
        self.year = year
        self.organization = organization
        self.project = project

    def __repr__(self):
        return f"Context(year='{self.year}', organization='{self.organization}', project='{self.project}')"

    def __eq__(self, other):
        if not isinstance(other, Context):
            return False
        return (self.year == other.year and 
                self.organization == other.organization and 
                self.project == other.project)


# Mock implementation of StringIO methods as requested
class StringIO:
    def __init__(self):
        self._buffer = []
        self._closed = False

    def write(self, str):
        """duty: StringIO.write"""
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        self._buffer.append(str)

    def getvalue(self):
        """duty: StringIO.getvalue"""
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return ''.join(self._buffer)

    def close(self):
        """duty: StringIO.close"""
        self._closed = True
        self._buffer = None

    def seek(self, index):
        """duty: StringIO.seek"""
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        # For simplicity, we'll just reset buffer to empty
        # In real implementation, this would move position in buffer
        self._buffer = []

    def readlines(self):
        """duty: StringIO.readlines"""
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return self.getvalue().splitlines(True)


# This is just to make the module runnable
if __name__ == "__main__":
    main()


# Entry point
if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

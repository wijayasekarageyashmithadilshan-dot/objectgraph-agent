### FILE: lice/core.py
```python
import os
import sys
from argparse import ArgumentParser
from io import StringIO

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

# Global functions
def main():
    """Main function to parse arguments and generate license"""
    parser = ArgumentParser(description='Generate license files')
    parser.add_argument('license', nargs='?', help='Type of license to generate')
    parser.add_argument('-o', '--org', help='Organization name')
    parser.add_argument('-p', '--proj', help='Project name')
    parser.add_argument('-t', '--template', help='Path to custom template file')
    parser.add_argument('-y', '--year', help='Copyright year')
    parser.add_argument('-l', '--language', help='Language for header formatting')
    parser.add_argument('-f', '--file', help='Output file name')
    parser.add_argument('--vars', action='store_true', help='List template variables')

    args = parser.parse_args()

    # Get context
    context = get_context(args)
    
    # Rest of the logic would go here...
    # For now, just return the context for testing purposes
    return context

def clean_path(p):
    """Clean up a file path"""
    return os.path.normpath(p)

def get_context(args):
    """Create context object from arguments"""
    # Try to guess organization if not provided
    org = args.org or guess_organization()
    
    # Create and return context
    return Context(
        year=args.year,
        organization=org,
        project=args.proj
    )

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
    """Load a template from a file"""
    with open(path, 'r') as f:
        return StringIO(f.read())

def load_template(license_name, header=False):
    """Load a template by license name"""
    # This would normally load from the templates directory
    # For now, returning empty StringIO for demonstration
    return StringIO("")

def extract_vars(template):
    """Extract variables from template"""
    # Implementation would parse template for variables
    return []

def generate_license(template, context):
    """Generate license text with context"""
    # Implementation would substitute variables in template
    return template

def format_license(template, lang):
    """Format license for specific language"""
    # Implementation would format according to language comment style
    return template

def get_suffix(name):
    """Get file suffix from name"""
    if '.' in name:
        return name.split('.')[-1]
    return False

# Entry point
if __name__ == "__main__":
    main()
```
### FILE: lice/core.py
```python
import argparse
import os
import sys
from enum import Enum
from io import StringIO


class LICENSES(Enum):
    """Enumeration of supported licenses"""
    AFL3 = "afl3"
    AGPL3 = "agpl3"
    APACHE = "apache"
    BSD2 = "bsd2"
    BSD3 = "bsd3"
    CC_BY = "cc_by"
    ECLIPSE = "eclipse"
    GPL2 = "gpl2"
    GPL3 = "gpl3"
    LGPL3 = "lgpl3"
    MIT = "mit"
    MPL2 = "mpl2"
    UNLICENSE = "unlicense"
    WTFPL = "wtfpl"


class Context:
    """Context for license generation"""
    def __init__(self, year=None, organization=None, project=None):
        self.year = year
        self.organization = organization
        self.project = project


class ArgumentParser:
    """Wrapper around argparse.ArgumentParser"""
    def __init__(self):
        self._action_groups = []
        self.parser = argparse.ArgumentParser()
        
    def add_argument(self, *args, **kwargs):
        """Add an argument to the parser"""
        return self.parser.add_argument(*args, **kwargs)
    
    def parse_args(self):
        """Parse command line arguments"""
        return self.parser.parse_args()


def clean_path(p):
    """Clean a file path by normalizing it"""
    return os.path.normpath(p)


def get_context(args):
    """Create a context object from parsed arguments"""
    return Context(
        year=args.year,
        organization=args.org,
        project=args.proj
    )


def guess_organization():
    """Guess the organization from git config or USER environment variable"""
    # Try to get organization from git config
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
    """Load a template from a file path"""
    with open(clean_path(path), 'r') as f:
        content = f.read()
    return StringIO(content)


def load_template(license_name, header=False):
    """Load a template for a given license"""
    # Determine template filename
    if header:
        template_name = f"template-{license_name}-header.txt"
    else:
        template_name = f"template-{license_name}.txt"
    
    # Try to find template in current directory first
    template_path = clean_path(template_name)
    if os.path.exists(template_path):
        return load_file_template(template_path)
    
    # If not found, look in a templates directory
    templates_dir = clean_path(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    template_path = clean_path(os.path.join(templates_dir, template_name))
    if os.path.exists(template_path):
        return load_file_template(template_path)
    
    # If still not found, raise an error
    raise FileNotFoundError(f"Template {template_name} not found")


def extract_vars(template):
    """Extract variables from a template"""
    vars_list = []
    for line in template.readlines():
        if '${' in line and '}' in line:
            # Extract variables between ${ and }
            start = 0
            while True:
                start = line.find('${', start)
                if start == -1:
                    break
                end = line.find('}', start)
                if end == -1:
                    break
                var = line[start+2:end]
                if var not in vars_list:
                    vars_list.append(var)
                start = end + 1
    return vars_list


def generate_license(template, context):
    """Generate license text using a template and context"""
    # Reset template position
    template.seek(0)
    
    # Get template content
    content = template.read()
    
    # Replace variables with context values
    result = content.replace('${year}', context.year or '')
    result = result.replace('${organization}', context.organization or '')
    result = result.replace('${project}', context.project or '')
    
    # Create new StringIO with the result
    output = StringIO()
    output.write(result)
    output.seek(0)
    return output


def format_license(template, lang):
    """Format license for a specific programming language"""
    # Reset template position
    template.seek(0)
    
    # Get the content
    content = template.read()
    
    # Define comment styles for different languages
    comment_styles = {
        'py': '# ',
        'js': '// ',
        'java': '// ',
        'c': '// ',
        'cpp': '// ',
        'cs': '// ',
        'go': '// ',
        'rs': '// ',
        'php': '// ',
        'rb': '# ',
        'sh': '# ',
        'pl': '# ',
        'sql': '-- ',
        'html': '<!-- ',
        'css': '/* ',
        'xml': '<!-- ',
        'yaml': '# ',
        'yml': '# ',
        'md': '<!-- ',
        'txt': '',
    }
    
    # Get comment prefix
    prefix = comment_styles.get(lang, '# ')
    
    # Format lines
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        if line.strip() == '':
            formatted_lines.append('')
        elif line.startswith('<!--') or line.startswith('/*'):
            # Preserve special comments
            formatted_lines.append(line)
        else:
            formatted_lines.append(prefix + line)
    
    # Join formatted lines
    formatted_content = '\n'.join(formatted_lines)
    
    # Create new StringIO with formatted content
    output = StringIO()
    output.write(formatted_content)
    output.seek(0)
    return output


def get_suffix(name):
    """Get file suffix from name"""
    if '.' in name:
        return name.split('.')[-1]
    return False


def main():
    """Main function to handle command line interface"""
    # Create argument parser
    parser = ArgumentParser()
    
    # Add arguments
    parser.add_argument('license', nargs='?', default=None, 
                       help='Type of license to generate')
    parser.add_argument('-o', '--org', dest='org',
                       help='Organization name')
    parser.add_argument('-p', '--proj', dest='proj',
                       help='Project name')
    parser.add_argument('-t', '--template', dest='template',
                       help='Path to custom template file')
    parser.add_argument('-y', '--year', dest='year',
                       help='Copyright year')
    parser.add_argument('-l', '--language', dest='language',
                       help='Programming language for header formatting')
    parser.add_argument('-f', '--file', dest='ofile',
                       help='Output file name')
    parser.add_argument('--vars', action='store_true',
                       help='List all template variables')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set default year if not provided
    if not args.year:
        import datetime
        args.year = str(datetime.datetime.now().year)
    
    # Set default organization if not provided
    if not args.org:
        args.org = guess_organization()
    
    # Handle --vars flag
    if args.vars:
        if not args.license:
            print("Error: --vars requires a license type", file=sys.stderr)
            sys.exit(1)
        try:
            template = load_template(args.license)
            vars_list = extract_vars(template)
            for var in vars_list:
                print(var)
            return
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Handle no license specified
    if not args.license:
        print("Available licenses:")
        for license in LICENSES:
            print(f"  {license.value}")
        return
    
    # Validate license
    try:
        license_enum = LICENSES(args.license)
    except ValueError:
        print(f"Error: Unknown license '{args.license}'", file=sys.stderr)
        sys.exit(1)
    
    # Load template
    try:
        if args.template:
            template = load_file_template(args.template)
        else:
            template = load_template(args.license, header=bool(args.language))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create context
    context = get_context(args)
    
    # Generate license
    license_text = generate_license(template, context)
    
    # Format if language specified
    if args.language:
        license_text = format_license(license_text, args.language)
    
    # Output to file or stdout
    if args.ofile:
        with open(args.ofile, 'w') as f:
            f.write(license_text.getvalue())
    else:
        print(license_text.getvalue())


# StringIO methods
def StringIO_write(self, s):
    """Write string to StringIO buffer"""
    self.buf.write(s)

def StringIO_getvalue(self):
    """Get value from StringIO buffer"""
    return self.buf.getvalue()

def StringIO_close(self):
    """Close StringIO buffer"""
    self.buf.close()

def StringIO_seek(self, index):
    """Seek to position in StringIO buffer"""
    self.buf.seek(index)

def StringIO_readlines(self):
    """Read lines from StringIO buffer"""
    self.buf.seek(0)
    return self.buf.readlines()
```
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
    GNU_GPL3 = "gpl3"
    GNU_GPL2 = "gpl2"
    GNU_LGPL3 = "lgpl3"
    GNU_LGPL21 = "lgpl21"
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
    """Guess the organization from git config or USER env var"""
    # Try to get organization from git config
    try:
        import subprocess
        result = subprocess.run(['git', 'config', '--get', 'user.name'], 
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
    """Load a template based on license name and header flag"""
    # Determine template filename
    if header:
        template_name = f"template-{license_name}-header.txt"
    else:
        template_name = f"template-{license_name}.txt"
    
    # In a real implementation, this would look in the templates directory
    # For now, we'll simulate loading by creating a StringIO with placeholder content
    return StringIO(f"Template content for {template_name}")


def extract_vars(template):
    """Extract variables from a template"""
    # This is a simplified implementation
    # In reality, this would parse the template for placeholders like {{var}}
    vars_found = []
    content = template.getvalue()
    # Simple regex-like extraction for demonstration
    lines = content.split('\n')
    for line in lines:
        if '{{' in line and '}}' in line:
            # Extract variable names between {{ and }}
            start = line.find('{{') + 2
            end = line.find('}}')
            if start > 1 and end > start:
                var_name = line[start:end].strip()
                vars_found.append(var_name)
    return vars_found


def generate_license(template, context):
    """Generate license text with context variables"""
    # This is a simplified implementation
    # In reality, this would replace template variables with context values
    content = template.getvalue()
    
    # Replace placeholders with context values
    if context.year:
        content = content.replace('{{year}}', str(context.year))
    if context.organization:
        content = content.replace('{{organization}}', context.organization)
    if context.project:
        content = content.replace('{{project}}', context.project)
    
    # Return updated content
    template.seek(0)
    template.truncate(0)
    template.write(content)
    template.seek(0)
    return template


def format_license(template, lang):
    """Format license for a specific programming language"""
    # This is a simplified implementation
    # In reality, this would apply language-specific comment formatting
    content = template.getvalue()
    
    # Apply language-specific formatting
    if lang == 'py':
        # Python comments
        lines = content.split('\n')
        formatted_lines = ['# ' + line if line.strip() else '#' for line in lines]
        content = '\n'.join(formatted_lines)
    elif lang == 'js':
        # JavaScript comments
        lines = content.split('\n')
        formatted_lines = ['// ' + line if line.strip() else '//' for line in lines]
        content = '\n'.join(formatted_lines)
    elif lang == 'c':
        # C comments
        lines = content.split('\n')
        formatted_lines = ['/* ' + line + ' */' if line.strip() else '/* */' for line in lines]
        content = '\n'.join(formatted_lines)
    # Add more language support as needed
    
    # Update template with formatted content
    template.seek(0)
    template.truncate(0)
    template.write(content)
    template.seek(0)
    return template


def get_suffix(name):
    """Get file suffix for a given name"""
    # This is a simplified implementation
    # In reality, this would map names to extensions
    suffix_map = {
        'py': '.py',
        'js': '.js',
        'c': '.c',
        'cpp': '.cpp',
        'java': '.java',
        'html': '.html',
        'css': '.css',
        'sh': '.sh'
    }
    return suffix_map.get(name, '')


def main():
    """Main function to parse arguments and generate license"""
    # Create argument parser
    parser = ArgumentParser()
    
    # Add arguments
    parser.add_argument('license', nargs='?', default='mit', 
                       help='License type to generate')
    parser.add_argument('-o', '--org', dest='org', 
                       help='Organization name')
    parser.add_argument('-p', '--proj', dest='proj', 
                       help='Project name')
    parser.add_argument('-t', '--template', dest='template', 
                       help='Custom template file path')
    parser.add_argument('-y', '--year', dest='year', 
                       help='Copyright year')
    parser.add_argument('-l', '--language', dest='language', 
                       help='Programming language for header formatting')
    parser.add_argument('-f', '--file', dest='file', 
                       help='Output file name')
    parser.add_argument('--vars', action='store_true', 
                       help='List template variables')
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no organization provided, try to guess it
    if not args.org:
        args.org = guess_organization()
    
    # If year not provided, use current year
    if not args.year:
        import datetime
        args.year = str(datetime.datetime.now().year)
    
    # Get context
    context = get_context(args)
    
    # Handle --vars flag
    if args.vars:
        template = load_template(args.license, header=args.language is not None)
        vars_list = extract_vars(template)
        print("Template variables:", ', '.join(vars_list))
        return
    
    # Load template
    if args.template:
        template = load_file_template(args.template)
    else:
        template = load_template(args.license, header=args.language is not None)
    
    # Generate license
    license_text = generate_license(template, context)
    
    # Format if language specified
    if args.language:
        license_text = format_license(license_text, args.language)
    
    # Output result
    if args.file:
        with open(args.file, 'w') as f:
            f.write(license_text.getvalue())
    else:
        print(license_text.getvalue())


# StringIO methods implementations
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
    return self.buf.readlines()
```
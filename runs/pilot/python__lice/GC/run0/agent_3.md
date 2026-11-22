### FILE: lice/core.py
```python
import sys
import os
import datetime
from argparse import ArgumentParser
from io import StringIO

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

def main():
    """duty: Global_functions.main"""
    parser = ArgumentParser()
    parser.add_argument('license', nargs='?', default='mit')
    parser.add_argument('-o', '--org', dest='organization')
    parser.add_argument('-p', '--proj', dest='project')
    parser.add_argument('-t', '--template', dest='template_path')
    parser.add_argument('-y', '--year', dest='year')
    parser.add_argument('-l', '--language', dest='language')
    parser.add_argument('-f', '--file', dest='output_file')
    parser.add_argument('--vars', action='store_true')
    
    args = parser.parse_args()
    
    # Get context
    context = get_context(args)
    
    # Handle --vars flag
    if args.vars:
        template = load_template(args.license, False)
        vars_list = extract_vars(template)
        print("Template variables:", ', '.join(vars_list))
        return
    
    # Load template
    if args.template_path:
        template = load_file_template(args.template_path)
    else:
        template = load_template(args.license, False)
    
    # Generate license
    license_text = generate_license(template, context)
    
    # Format if language specified
    if args.language:
        license_text = format_license(license_text, args.language)
    
    # Output handling
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(license_text)
    else:
        print(license_text)

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
    """duty: Global_functions.guess_organization"""
    import subprocess
    try:
        result = subprocess.run(['git', 'config', 'user.name'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
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

# Mock Context class since it's owned by another agent
class Context:
    def __init__(self):
        self.year = ""
        self.organization = ""
        self.project = ""
```
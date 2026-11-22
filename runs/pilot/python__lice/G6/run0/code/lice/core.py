import argparse
import os
import re
import sys
from io import StringIO
from enum import Enum

class LICENSES(Enum):
    AFL3 = "afl3"
    AGPL3 = "agpl3"
    APACHE = "apache"
    BSD2 = "bsd2"
    BSD3 = "bsd3"
    CC_BY = "cc_by"
    GPL3 = "gpl3"
    MIT = "mit"
    MPL2 = "mpl2"
    UNLICENSE = "unlicense"

class Context:
    def __init__(self, year=None, organization=None, project=None):
        self.year = year
        self.organization = organization
        self.project = project

class ArgumentParser:
    def __init__(self):
        self._action_groups = []
        self.parser = argparse.ArgumentParser()
        
    def add_argument(self, *args, **kwargs):
        """duty: ArgumentParser.add_argument"""
        return self.parser.add_argument(*args, **kwargs)
    
    def parse_args(self):
        """duty: ArgumentParser.parse_args"""
        return self.parser.parse_args()

def clean_path(p):
    """duty: Global_functions.clean_path"""
    return os.path.normpath(p)

def get_context(args):
    """duty: Global_functions.get_context"""
    year = getattr(args, 'year', None)
    organization = getattr(args, 'org', None)
    project = getattr(args, 'proj', None)
    
    if not organization:
        organization = guess_organization()
    
    return Context(year=year, organization=organization, project=project)

def guess_organization():
    """duty: Global_functions.guess_organization"""
    try:
        import subprocess
        result = subprocess.run(['git', 'config', '--global', 'user.name'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    
    return os.environ.get('USER', 'Unknown')

def load_file_template(path):
    """duty: Global_functions.load_file_template"""
    with open(path, 'r') as f:
        content = f.read()
    return StringIO(content)

def load_template(license_name, header=False):
    """duty: Global_functions.load_template"""
    template_name = f"template-{license_name}{'-header' if header else ''}.txt"
    template_path = os.path.join("templates", template_name)
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template {template_path} not found")
    
    return load_file_template(template_path)

def extract_vars(template):
    """duty: Global_functions.extract_vars"""
    vars_found = re.findall(r'\{\{([^}]+)\}\}', template.getvalue())
    return list(set(vars_found))  # Remove duplicates

def generate_license(template, context):
    """duty: Global_functions.generate_license"""
    content = template.getvalue()
    
    # Replace template variables with context values
    if context.year:
        content = content.replace('{{ year }}', str(context.year))
    if context.organization:
        content = content.replace('{{ organization }}', context.organization)
    if context.project:
        content = content.replace('{{ project }}', context.project)
    
    # Create new StringIO with generated content
    result = StringIO()
    result.write(content)
    result.seek(0)
    return result

def format_license(template, lang):
    """duty: Global_functions.format_license"""
    content = template.getvalue()
    
    # Define comment styles for different languages
    comment_styles = {
        'py': '# ',
        'js': '// ',
        'java': '// ',
        'c': '// ',
        'cpp': '// ',
        'html': '<!-- ',
        'css': '/* ',
        'sh': '# ',
        'rb': '# ',
        'php': '// ',
        'go': '// ',
        'rs': '// ',
        'swift': '// ',
        'kt': '// ',
        'scala': '// ',
        'pl': '# ',
        'perl': '# ',
        'lua': '-- ',
        'sql': '-- ',
        'r': '# ',
        'matlab': '% ',
        'groovy': '// ',
        'docker': '# ',
        'yaml': '# ',
        'yml': '# ',
        'toml': '# ',
        'ini': '; ',
        'cfg': '; ',
        'conf': '; ',
        'log': '',
        'md': '',
        'txt': ''
    }
    
    comment_prefix = comment_styles.get(lang, '')
    
    if comment_prefix == '':
        return template
    
    # Format content with comments
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        if line.strip() == '':
            formatted_lines.append('')
        else:
            formatted_lines.append(comment_prefix + line)
    
    formatted_content = '\n'.join(formatted_lines)
    
    # Create new StringIO with formatted content
    result = StringIO()
    result.write(formatted_content)
    result.seek(0)
    return result

def get_suffix(name):
    """duty: Global_functions.get_suffix"""
    parts = name.split('.')
    if len(parts) < 2:
        return False
    return parts[-1]

def main():
    """duty: Global_functions.main"""
    parser = ArgumentParser()
    
    # Add arguments
    parser.add_argument('license', nargs='?', default='mit', 
                       help='The type of license to generate')
    parser.add_argument('-o', '--org', help='The organization under which the license is registered')
    parser.add_argument('-p', '--proj', help='The project name for which the license is generated')
    parser.add_argument('-t', '--template', help='The path to a custom license template file')
    parser.add_argument('-y', '--year', help='The copyright year to be listed in the license')
    parser.add_argument('-l', '--language', help='The language for which the license header should be formatted')
    parser.add_argument('-f', '--file', help='The output file name where the license should be saved')
    parser.add_argument('--vars', action='store_true', help='List all template variables for the specified license')
    
    args = parser.parse_args()
    
    # Handle --vars flag
    if args.vars:
        try:
            template = load_template(args.license, header=bool(args.language))
            vars_list = extract_vars(template)
            print("Template variables:", ", ".join(vars_list))
            return
        except Exception as e:
            print(f"Error: {e}")
            return
    
    # Get context
    context = get_context(args)
    
    # Load template
    if args.template:
        template = load_file_template(args.template)
    else:
        template = load_template(args.license, header=bool(args.language))
    
    # Generate license
    generated = generate_license(template, context)
    
    # Format if language specified
    if args.language:
        formatted = format_license(generated, args.language)
        output_content = formatted.getvalue()
    else:
        output_content = generated.getvalue()
    
    # Output handling
    if args.file:
        with open(args.file, 'w') as f:
            f.write(output_content)
    else:
        print(output_content)

# StringIO methods
def StringIO_write(self, s):
    """duty: StringIO.write"""
    self.buf += s.encode('utf-8') if isinstance(s, str) else s

def StringIO_getvalue(self):
    """duty: StringIO.getvalue"""
    return self.buf.decode('utf-8') if hasattr(self, 'buf') else ''

def StringIO_close(self):
    """duty: StringIO.close"""
    if hasattr(self, 'buf'):
        self.buf = b''

def StringIO_seek(self, index):
    """duty: StringIO.seek"""
    if hasattr(self, 'buf'):
        self.buf = self.buf[index:]

def StringIO_readlines(self):
    """duty: StringIO.readlines"""
    if hasattr(self, 'buf'):
        content = self.buf.decode('utf-8')
        return content.split('\n')
    return []

# Monkey patch StringIO methods
StringIO.write = StringIO_write
StringIO.getvalue = StringIO_getvalue
StringIO.close = StringIO_close
StringIO.seek = StringIO_seek
StringIO.readlines = StringIO_readlines

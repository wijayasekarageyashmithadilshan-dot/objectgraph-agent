### FILE: lice/core.py
```python
import argparse
import sys
import os
from io import StringIO
from typing import List, Any, Union
from argparse import ArgumentParser

# Importing classes from other agents
# from . import LICENSES
# from ._init_ import __version__
# from .Context import Context

# Assuming these are defined elsewhere in the codebase
# from . import LICENSES
# from ._init_ import __version__

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


class Context:
    """Context holds the configuration data for license generation."""
    
    def __init__(self, year=None, organization=None, project=None):
        self._year = year
        self._organization = organization
        self._project = project

    @property
    def year(self):
        """Get the copyright year."""
        return self._year

    @year.setter
    def year(self, value):
        """Set the copyright year."""
        self._year = value

    @property
    def organization(self):
        """Get the organization name."""
        return self._organization

    @organization.setter
    def organization(self, value):
        """Set the organization name."""
        self._organization = value

    @property
    def project(self):
        """Get the project name."""
        return self._project

    @project.setter
    def project(self, value):
        """Set the project name."""
        self._project = value


# duty: Global_functions.main
def main():
    """Main function to parse arguments and generate license"""
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
    
    # If --vars flag is set, print variables and exit
    if args.vars:
        template = load_template(args.license, False)
        vars_list = extract_vars(template)
        for var in vars_list:
            print(var)
        return
    
    # Load template
    if args.template_path:
        template = load_file_template(args.template_path)
    else:
        template = load_template(args.license, False)
    
    # Generate license
    license_text = generate_license(template, context)
    
    # Format license if language is specified
    if args.language:
        license_text = format_license(license_text, args.language)
    
    # Output license
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(license_text.getvalue())
    else:
        print(license_text.getvalue())


# duty: Global_functions.clean_path
def clean_path(p: str) -> str:
    """Clean up a file path by normalizing it"""
    return os.path.normpath(p)


# duty: Global_functions.get_context
def get_context(args: argparse.Namespace) -> Context:
    """Create a context object from command line arguments"""
    context = Context()
    
    # Set year
    if args.year:
        context.year = args.year
    else:
        import datetime
        context.year = str(datetime.datetime.now().year)
    
    # Set organization
    if args.organization:
        context.organization = args.organization
    else:
        context.organization = guess_organization()
    
    # Set project
    if args.project:
        context.project = args.project
    else:
        context.project = os.getcwd().split(os.sep)[-1]
    
    return context


# duty: Global_functions.guess_organization
def guess_organization() -> str:
    """Guess the organization from git config or USER environment variable"""
    import subprocess
    
    try:
        # Try to get from git config
        result = subprocess.run(['git', 'config', '--get', 'user.name'], 
                               capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    
    # Fall back to USER environment variable
    return os.environ.get('USER', 'Unknown')


# duty: Global_functions.load_file_template
def load_file_template(path: str) -> StringIO:
    """Load a template from a file path"""
    path = clean_path(path)
    with open(path, 'r') as f:
        content = f.read()
    return StringIO(content)


# duty: Global_functions.load_template
def load_template(license_name: str, header: bool) -> StringIO:
    """Load a built-in template by license name and header flag"""
    # This would normally load from the templates directory
    # For now, we'll simulate this behavior
    template_name = f"template-{license_name}{'-header' if header else ''}.txt"
    # In a real implementation, this would read from the templates folder
    # For now, returning a mock template
    return StringIO(f"Mock template for {license_name}")


# duty: Global_functions.extract_vars
def extract_vars(template: StringIO) -> List[str]:
    """Extract all template variables from a template"""
    template.seek(0)
    lines = template.readlines()
    vars_list = []
    
    for line in lines:
        # Look for variables in the format {{variable_name}}
        start = 0
        while True:
            start = line.find('{{', start)
            if start == -1:
                break
            end = line.find('}}', start)
            if end == -1:
                break
            var_name = line[start+2:end].strip()
            if var_name not in vars_list:
                vars_list.append(var_name)
            start = end + 2
    
    return vars_list


# duty: Global_functions.generate_license
def generate_license(template: StringIO, context: Context) -> StringIO:
    """Generate license text by replacing variables in template with context values"""
    template.seek(0)
    content = template.getvalue()
    
    # Replace variables with context values
    replacements = {
        'year': context.year,
        'organization': context.organization,
        'project': context.project
    }
    
    for key, value in replacements.items():
        content = content.replace('{{' + key + '}}', str(value))
    
    return StringIO(content)


# duty: Global_functions.format_license
def format_license(license_text: StringIO, lang: str) -> StringIO:
    """Format license text for a specific programming language"""
    license_text.seek(0)
    content = license_text.getvalue()
    
    # Define comment styles for different languages
    comment_styles = {
        'py': '# ',
        'js': '// ',
        'java': '// ',
        'c': '/* ',
        'cpp': '/* ',
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
        'dart': '// ',
        'h': '/* ',
        'hs': '-- ',
        'erl': '% ',
        'ex': '# ',
        'clj': '; ',
        'coffee': '# ',
        'elm': '-- ',
        'f90': '! ',
        'fs': '// ',
        'ml': '(* ',
        'pas': '{ ',
        'asm': '; ',
        'awk': '# ',
        'sed': '# ',
        'tcl': '# ',
        'vhdl': '-- ',
        'verilog': '// ',
        'yaml': '# ',
        'json': '// ',  # JSON doesn't support comments, but we'll use // anyway
        'xml': '<!-- ',
        'ini': '; ',
        'cfg': '; ',
        'toml': '# ',
        'md': '<!-- ',
        'rst': '.. ',
        'tex': '% ',
        'bib': '% ',
        'csv': '# ',  # CSV doesn't support comments, but we'll use # anyway
        'log': '# ',
        'out': '# ',
        'err': '# ',
        'dat': '# ',
        'txt': '# ',
        'conf': '# ',
        'properties': '# ',
        'gradle': '// ',
        'makefile': '# ',
        'dockerfile': '# ',
        'gitignore': '# ',
        'editorconfig': '# ',
        'babelrc': '# ',
        'eslintrc': '# ',
        'prettierrc': '# ',
        'stylelintrc': '# ',
        'jest': '# ',
        'webpack': '# ',
        'gulpfile': '# ',
        'gruntfile': '# ',
        'packagejson': '// ',
        'readme': '# ',
        'license': '# ',
        'changelog': '# ',
        'contributing': '# ',
        'codeofconduct': '# ',
        'security': '# ',
        'support': '# ',
        'faq': '# ',
        'todo': '# ',
        'notes': '# ',
        'ideas': '# ',
        'brainstorm': '# ',
        'design': '# ',
        'spec': '# ',
        'api': '# ',
        'docs': '# ',
        'examples': '# ',
        'tests': '# ',
        'test': '# ',
        'src': '# ',
        'lib': '# ',
        'bin': '# ',
        'etc': '# ',
        'var': '# ',
        'tmp': '# ',
        'logdir': '# ',
        'cache': '# ',
        'build': '# ',
        'dist': '# ',
        'release': '# ',
        'deploy': '# ',
        'prod': '# ',
        'staging': '# ',
        'dev': '# ',
        'local': '# ',
        'temp': '# ',
        'backup': '# ',
        'old': '# ',
        'new': '# ',
        'draft': '# ',
        'final': '# ',
        'complete': '# ',
        'done': '# ',
        'inprogress': '# ',
        'pending': '# ',
        'queued': '# ',
        'running': '# ',
        'failed': '# ',
        'success': '# ',
        'error': '# ',
        'warning': '# ',
        'info': '# ',
        'debug': '# ',
        'trace': '# ',
        'verbose': '# ',
        'quiet': '# ',
        'silent': '# ',
        'default': '# '
    }
    
    # Get comment style for language
    comment_style = comment_styles.get(lang, '# ')
    
    # If it's a header-style comment, we need to handle differently
    if comment_style in ['/* ', '/*', '*/']:
        # Handle C-style comments
        lines = content.split('\n')
        formatted_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                formatted_lines.append(comment_style.rstrip() + ' ' + line)
            elif i == len(lines) - 1 and line == '':
                formatted_lines.append(' */')
            else:
                formatted_lines.append(' * ' + line)
        formatted_content = '\n'.join(formatted_lines)
    elif comment_style.startswith('<!--'):
        # Handle HTML/XML comments
        lines = content.split('\n')
        formatted_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                formatted_lines.append(comment_style.rstrip() + ' ' + line)
            elif i == len(lines) - 1 and line == '':
                formatted_lines.append(' -->')
            else:
                formatted_lines.append(' ' + line)
        formatted_content = '\n'.join(formatted_lines)
    else:
        # Handle line-by-line comments
        lines = content.split('\n')
        formatted_lines = [comment_style + line for line in lines]
        formatted_content = '\n'.join(formatted_lines)
    
    return StringIO(formatted_content)


# duty: Global_functions.get_suffix
def get_suffix(name: str) -> Union[str, bool]:
    """Get file suffix from filename"""
    if '.' not in name:
        return False
    return name.split('.')[-1]
```
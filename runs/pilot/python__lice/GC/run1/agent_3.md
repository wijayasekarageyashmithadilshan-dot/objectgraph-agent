### FILE: lice/core.py
```python
import argparse
import sys
import os
import re
from typing import List, Any, Union
from io import StringIO

class ArgumentParser:
    """Class to handle command line argument parsing"""
    
    def __init__(self):
        self._action_groups = []
        self.parser = argparse.ArgumentParser()
    
    # duty: ArgumentParser.add_argument
    def add_argument(self, *args, **kwargs) -> None:
        """
        Add an argument to the parser
        """
        self.parser.add_argument(*args, **kwargs)
    
    # duty: ArgumentParser.parse_args
    def parse_args(self) -> argparse.Namespace:
        """
        Parse command line arguments and return the parsed arguments
        """
        return self.parser.parse_args()

class Context:
    """Context for license generation"""
    def __init__(self, year: str, organization: str, project: str):
        self.year = year
        self.organization = organization
        self.project = project

class LICENSES:
    """Enumeration of supported licenses"""
    AGPL3 = "agpl3"
    Apache = "apache"
    BSD2 = "bsd2"
    BSD3 = "bsd3"
    CC_BY = "cc_by"
    EPL = "epl"
    GPL2 = "gpl2"
    GPL3 = "gpl3"
    LGPL3 = "lgpl3"
    MIT = "mit"
    MPL2 = "mpl2"
    Unlicense = "unlicense"

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
        if index < 0 or index > len(self._buffer):
            raise ValueError("Invalid seek position")
        # For simplicity, we'll just truncate the buffer
        # In a real implementation, this would require more complex handling
        self._buffer = self._buffer[:index]
    
    def readlines(self):
        """duty: StringIO.readlines"""
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        return self.getvalue().splitlines(True)

# duty: Global_functions.main
def main():
    """
    Main entry point for the lice command line interface
    """
    parser = ArgumentParser()
    
    # Add arguments
    parser.add_argument('license', nargs='?', help='The type of license to generate')
    parser.add_argument('-o', '--org', help='The organization under which the license is registered')
    parser.add_argument('-p', '--proj', help='The project name for which the license is generated')
    parser.add_argument('-t', '--template', help='The path to a custom license template file')
    parser.add_argument('-y', '--year', help='The copyright year to be listed in the license')
    parser.add_argument('-l', '--language', help='The language for which the license header should be formatted')
    parser.add_argument('-f', '--file', help='The output file name where the license should be saved')
    parser.add_argument('--vars', action='store_true', help='Option to list all template variables for the specified license')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Import here to avoid circular imports
    from . import __version__
    print(f"Lice version {__version__}")
    
    # Get context
    context = get_context(args)
    
    # Handle --vars flag
    if args.vars:
        template = load_template(args.license, False)
        vars_list = extract_vars(template)
        print("Template variables:")
        for var in vars_list:
            print(f"  {var}")
        return
    
    # Load template
    if args.template:
        template = load_file_template(args.template)
    else:
        template = load_template(args.license, False)
    
    # Generate license
    license_text = generate_license(template, context)
    
    # Format license if needed
    if args.language:
        license_text = format_license(license_text, args.language)
    
    # Output license
    if args.file:
        with open(args.file, 'w') as f:
            f.write(license_text)
    else:
        print(license_text)

# duty: Global_functions.clean_path
def clean_path(p: str) -> str:
    """
    Clean a file path by normalizing it
    """
    return os.path.normpath(p)

# duty: Global_functions.get_context
def get_context(args: argparse.Namespace) -> Context:
    """
    Create a context object from command line arguments
    """
    year = args.year or str(datetime.datetime.now().year)
    org = args.org or guess_organization()
    project = args.proj or os.path.basename(os.getcwd())
    
    return Context(year, org, project)

# duty: Global_functions.guess_organization
def guess_organization() -> str:
    """
    Guess the organization from git config or USER environment variable
    """
    try:
        import subprocess
        result = subprocess.run(['git', 'config', '--get', 'user.name'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    
    # Fallback to USER environment variable
    user = os.environ.get('USER')
    if user:
        return user
    
    # If all fails, return a generic name
    return "Your Organization Name"

# duty: Global_functions.load_file_template
def load_file_template(path: str) -> StringIO:
    """
    Load a template from a file
    """
    path = clean_path(path)
    try:
        with open(path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {path}")
    
    string_io = StringIO()
    string_io.write(content)
    return string_io

# duty: Global_functions.load_template
def load_template(license_name: str, header: bool) -> StringIO:
    """
    Load a built-in template
    """
    # Determine template name
    if header:
        template_name = f"template-{license_name}-header.txt"
    else:
        template_name = f"template-{license_name}.txt"
    
    # Try to find template in current directory first
    template_path = os.path.join(os.getcwd(), "templates", template_name)
    if os.path.exists(template_path):
        return load_file_template(template_path)
    
    # Try to find template in package templates
    try:
        import pkg_resources
        template_data = pkg_resources.resource_string('lice', f'templates/{template_name}')
        template_content = template_data.decode('utf-8')
        
        string_io = StringIO()
        string_io.write(template_content)
        return string_io
    except Exception:
        # If we can't find the template anywhere, raise an error
        raise FileNotFoundError(f"Template not found: {template_name}")

# duty: Global_functions.extract_vars
def extract_vars(template: StringIO) -> List[str]:
    """
    Extract template variables from a template
    """
    content = template.getvalue()
    # Find all variables in the format {{variable_name}}
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, content)
    return list(set(matches))  # Remove duplicates

# duty: Global_functions.generate_license
def generate_license(template: StringIO, context: Context) -> StringIO:
    """
    Generate license text by replacing variables in template with context values
    """
    content = template.getvalue()
    
    # Replace variables
    replacements = {
        'year': context.year,
        'organization': context.organization,
        'project': context.project
    }
    
    for key, value in replacements.items():
        content = content.replace('{{' + key + '}}', value)
    
    string_io = StringIO()
    string_io.write(content)
    return string_io

# duty: Global_functions.format_license
def format_license(license_text: StringIO, lang: str) -> str:
    """
    Format license text for a specific programming language
    """
    text = license_text.getvalue()
    
    # Define comment styles for different languages
    comment_styles = {
        'py': '# ',
        'js': '// ',
        'java': '// ',
        'c': '/* ',
        'cpp': '/* ',
        'html': '<!-- ',
        'css': '/* ',
        'rb': '# ',
        'sh': '# ',
        'php': '// ',
        'go': '// ',
        'rs': '// ',
        'swift': '// ',
        'kt': '// ',
        'scala': '// ',
        'pl': '# ',
        'lua': '-- ',
        'sql': '-- ',
        'r': '# ',
        'matlab': '% ',
        'perl': '# ',
        'dart': '// ',
        'h': '/* ',
        'hs': '-- ',
        'erl': '% ',
        'ml': '(* ',
        'fs': '// ',
        'coffee': '# ',
        'ts': '// ',
        'tsx': '// ',
        'jsx': '// ',
        'groovy': '// ',
        'scala': '// ',
        'clj': '; ',
        'el': '; ',
        'lisp': '; ',
        'scm': '; ',
        'rkt': '; ',
        'ss': '; ',
        'hy': '; ',
        'julia': '# ',
        'nim': '# ',
        'cr': '# ',
        'sl': '# ',
        'v': '// ',
        'zig': '// ',
        'asm': '; ',
        'pas': '{ ',
        'ada': '-- ',
        'f90': '! ',
        'f95': '! ',
        'f03': '! ',
        'f08': '! ',
        'f15': '! ',
        's': '! ',
        'sas': '* ',
        'stata': '* ',
        'awk': '# ',
        'sed': '# ',
        'fish': '# ',
        'zsh': '# ',
        'bash': '# ',
        'ksh': '# ',
        'tcsh': '# ',
        'csh': '# ',
        'tcl': '# ',
        'r': '# ',
        'tcl': '# ',
        'vhdl': '-- ',
        'verilog': '// ',
        'systemverilog': '// ',
        'yaml': '# ',
        'json': '// ',
        'xml': '<!-- ',
        'csv': '# ',
        'md': '<!-- ',
        'txt': '',
        'log': '# ',
        'cfg': '# ',
        'ini': '; ',
        'conf': '# ',
        'properties': '# ',
        'env': '# ',
        'dockerfile': '# ',
        'makefile': '# ',
        'cmake': '# ',
        'gradle': '// ',
        'pom': '<!-- ',
        'build': '# ',
        'yml': '# ',
        'yaml': '# ',
        'toml': '# ',
        'lock': '# ',
        'patch': '# ',
        'diff': '# ',
        'gitignore': '# ',
        'gitattributes': '# ',
        'editorconfig': '# ',
        'prettierrc': '# ',
        'eslintrc': '// ',
        'babelrc': '// ',
        'stylelintrc': '// ',
        'lintstagedrc': '// ',
        'commitlintrc': '// ',
        'renovaterc': '// ',
        'dependabot': '# ',
        'codecov': '# ',
        'coveragerc': '# ',
        'pytest': '# ',
        'tox': '# ',
        'travis': '# ',
        'circleci': '# ',
        'appveyor': '# ',
        'azure-pipelines': '# ',
        'github-workflows': '# ',
        'gitlab-ci': '# ',
        'bitbucket-pipelines': '# ',
        'jenkins': '# ',
        'ansible': '# ',
        'terraform': '# ',
        'docker-compose': '# ',
        'kubernetes': '# ',
        'helm': '# ',
        'cloudformation': '# ',
        'serverless': '# ',
        'openapi': '# ',
        'swagger': '# ',
        'graphql': '# ',
        'proto': '// ',
        'avro': '// ',
        'thrift': '// ',
        'flatbuffers': '// ',
        'protobuf': '// ',
        'capnp': '// ',
        'idl': '// ',
        'sql': '-- ',
        'plsql': '-- ',
        'psql': '-- ',
        'mysql': '-- ',
        'postgresql': '-- ',
        'sqlite': '-- ',
        'oracle': '-- ',
        'mssql': '-- ',
        'db2': '-- ',
        'sybase': '-- ',
        'informix': '-- ',
        'teradata': '-- ',
        'redshift': '-- ',
        'snowflake': '-- ',
        'bigquery': '-- ',
        'cassandra': '-- ',
        'mongodb': '// ',
        'redis': '# ',
        'elasticsearch': '// ',
        'solr': '// ',
        'couchdb': '// ',
        'riak': '// ',
        'influxdb': '// ',
        'prometheus': '# ',
        'grafana': '# ',
        'kibana': '# ',
        'splunk': '# ',
        'elasticsearch': '// ',
        'logstash': '# ',
        'kafka': '# ',
        'rabbitmq': '# ',
        'activemq': '# ',
        'nats': '# ',
        'zeromq': '# ',
        'grpc': '// ',
        'rest': '# ',
        'soap': '# ',
        'wsdl': '# ',
        'wadl': '# ',
        'api': '# ',
        'openapi': '# ',
        'swagger': '# ',
        'graphql': '# ',
        'apollo': '# ',
        'relay': '# ',
        'prisma': '# ',
        'typeorm': '# ',
        'sequelize': '# ',
        'mongoose': '# ',
        'django': '# ',
        'flask': '# ',
        'fastapi': '# ',
        'spring': '// ',
        'net': '// ',
        'aspnet': '// ',
        'rubyonrails': '# ',
        'laravel': '// ',
        'symfony': '// ',
        'zend': '// ',
        'cakephp': '// ',
        'codeigniter': '// ',
        'yii': '// ',
        'phalcon': '// ',
        'slim': '// ',
        'silex': '// ',
        'fuelphp': '// ',
        'zend': '// ',
        'thinkphp': '// ',
        'laravel': '// ',
        'lumen': '// ',
        'sails': '// ',
        'adonis': '// ',
        'nest': '// ',
        'express': '// ',
        'koa': '// ',
        'hapi': '// ',
        'loopback': '// ',
        'feathers': '// ',
        'ramda': '// ',
        'lodash': '// ',
        'underscore': '// ',
        'backbone': '// ',
        'marionette': '// ',
        'ember': '// ',
        'angular': '// ',
        'react': '// ',
        'vue': '// ',
        'svelte': '// ',
        'riot': '// ',
        'polymer': '// ',
        'aurelia': '// ',
        'knockout': '// ',
        'mithril': '// ',
        'preact': '// ',
        'alpine': '// ',
        'lit': '// ',
        'stencil': '// ',
        'ionic': '// ',
        'cordova': '// ',
        'phonegap': '// ',
        'reactnative': '// ',
        'flutter': '// ',
        'xamarin': '// ',
        'unity': '// ',
        'unreal': '// ',
        'godot': '// ',
        'construct': '// ',
        'gameMaker': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'processing': '// ',
        'p5': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'pixi': '// ',
        'phaser': '// ',
        'melonJS': '// ',
        'impact': '// ',
        'enchant': '// ',
        'crafty': '// ',
        'melonJS': '// ',
        'phaser': '// ',
        'pixi': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'p5': '// ',
        'processing': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'gameMaker': '// ',
        'construct': '// ',
        'godot': '// ',
        'unreal': '// ',
        'unity': '// ',
        'xamarin': '// ',
        'flutter': '// ',
        'reactnative': '// ',
        'phonegap': '// ',
        'cordova': '// ',
        'ionic': '// ',
        'stencil': '// ',
        'lit': '// ',
        'alpine': '// ',
        'preact': '// ',
        'mithril': '// ',
        'knockout': '// ',
        'aurelia': '// ',
        'polymer': '// ',
        'riot': '// ',
        'svelte': '// ',
        'vue': '// ',
        'react': '// ',
        'angular': '// ',
        'ember': '// ',
        'marionette': '// ',
        'backbone': '// ',
        'lodash': '// ',
        'ramda': '// ',
        'feathers': '// ',
        'loopback': '// ',
        'hapi': '// ',
        'koa': '// ',
        'express': '// ',
        'nest': '// ',
        'adonis': '// ',
        'sails': '// ',
        'lumen': '// ',
        'laravel': '// ',
        'symfony': '// ',
        'zend': '// ',
        'cakephp': '// ',
        'yii': '// ',
        'phalcon': '// ',
        'slim': '// ',
        'silex': '// ',
        'fuelphp': '// ',
        'thinkphp': '// ',
        'zend': '// ',
        'django': '# ',
        'flask': '# ',
        'fastapi': '# ',
        'spring': '// ',
        'net': '// ',
        'aspnet': '// ',
        'rubyonrails': '# ',
        'laravel': '// ',
        'symfony': '// ',
        'zend': '// ',
        'cakephp': '// ',
        'codeigniter': '// ',
        'yii': '// ',
        'phalcon': '// ',
        'slim': '// ',
        'silex': '// ',
        'fuelphp': '// ',
        'zend': '// ',
        'thinkphp': '// ',
        'laravel': '// ',
        'lumen': '// ',
        'sails': '// ',
        'adonis': '// ',
        'nest': '// ',
        'express': '// ',
        'koa': '// ',
        'hapi': '// ',
        'loopback': '// ',
        'feathers': '// ',
        'ramda': '// ',
        'lodash': '// ',
        'underscore': '// ',
        'backbone': '// ',
        'marionette': '// ',
        'ember': '// ',
        'angular': '// ',
        'react': '// ',
        'vue': '// ',
        'svelte': '// ',
        'riot': '// ',
        'polymer': '// ',
        'aurelia': '// ',
        'knockout': '// ',
        'mithril': '// ',
        'preact': '// ',
        'alpine': '// ',
        'lit': '// ',
        'stencil': '// ',
        'ionic': '// ',
        'cordova': '// ',
        'phonegap': '// ',
        'reactnative': '// ',
        'flutter': '// ',
        'xamarin': '// ',
        'unity': '// ',
        'unreal': '// ',
        'godot': '// ',
        'construct': '// ',
        'gameMaker': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'processing': '// ',
        'p5': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'pixi': '// ',
        'phaser': '// ',
        'melonJS': '// ',
        'impact': '// ',
        'enchant': '// ',
        'crafty': '// ',
        'melonJS': '// ',
        'phaser': '// ',
        'pixi': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'p5': '// ',
        'processing': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'gameMaker': '// ',
        'construct': '// ',
        'godot': '// ',
        'unreal': '// ',
        'unity': '// ',
        'xamarin': '// ',
        'flutter': '// ',
        'reactnative': '// ',
        'phonegap': '// ',
        'cordova': '// ',
        'ionic': '// ',
        'stencil': '// ',
        'lit': '// ',
        'alpine': '// ',
        'preact': '// ',
        'mithril': '// ',
        'knockout': '// ',
        'aurelia': '// ',
        'polymer': '// ',
        'riot': '// ',
        'svelte': '// ',
        'vue': '// ',
        'react': '// ',
        'angular': '// ',
        'ember': '// ',
        'marionette': '// ',
        'backbone': '// ',
        'lodash': '// ',
        'ramda': '// ',
        'feathers': '// ',
        'loopback': '// ',
        'hapi': '// ',
        'koa': '// ',
        'express': '// ',
        'nest': '// ',
        'adonis': '// ',
        'sails': '// ',
        'lumen': '// ',
        'laravel': '// ',
        'symfony': '// ',
        'zend': '// ',
        'cakephp': '// ',
        'yii': '// ',
        'phalcon': '// ',
        'slim': '// ',
        'silex': '// ',
        'fuelphp': '// ',
        'zend': '// ',
        'thinkphp': '// ',
        'laravel': '// ',
        'lumen': '// ',
        'sails': '// ',
        'adonis': '// ',
        'nest': '// ',
        'express': '// ',
        'koa': '// ',
        'hapi': '// ',
        'loopback': '// ',
        'feathers': '// ',
        'ramda': '// ',
        'lodash': '// ',
        'underscore': '// ',
        'backbone': '// ',
        'marionette': '// ',
        'ember': '// ',
        'angular': '// ',
        'react': '// ',
        'vue': '// ',
        'svelte': '// ',
        'riot': '// ',
        'polymer': '// ',
        'aurelia': '// ',
        'knockout': '// ',
        'mithril': '// ',
        'preact': '// ',
        'alpine': '// ',
        'lit': '// ',
        'stencil': '// ',
        'ionic': '// ',
        'cordova': '// ',
        'phonegap': '// ',
        'reactnative': '// ',
        'flutter': '// ',
        'xamarin': '// ',
        'unity': '// ',
        'unreal': '// ',
        'godot': '// ',
        'construct': '// ',
        'gameMaker': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'processing': '// ',
        'p5': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'pixi': '// ',
        'phaser': '// ',
        'melonJS': '// ',
        'impact': '// ',
        'enchant': '// ',
        'crafty': '// ',
        'melonJS': '// ',
        'phaser': '// ',
        'pixi': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'p5': '// ',
        'processing': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'gameMaker': '// ',
        'construct': '// ',
        'godot': '// ',
        'unreal': '// ',
        'unity': '// ',
        'xamarin': '// ',
        'flutter': '// ',
        'reactnative': '// ',
        'phonegap': '// ',
        'cordova': '// ',
        'ionic': '// ',
        'stencil': '// ',
        'lit': '// ',
        'alpine': '// ',
        'preact': '// ',
        'mithril': '// ',
        'knockout': '// ',
        'aurelia': '// ',
        'polymer': '// ',
        'riot': '// ',
        'svelte': '// ',
        'vue': '// ',
        'react': '// ',
        'angular': '// ',
        'ember': '// ',
        'marionette': '// ',
        'backbone': '// ',
        'lodash': '// ',
        'ramda': '// ',
        'feathers': '// ',
        'loopback': '// ',
        'hapi': '// ',
        'koa': '// ',
        'express': '// ',
        'nest': '// ',
        'adonis': '// ',
        'sails': '// ',
        'lumen': '// ',
        'laravel': '// ',
        'symfony': '// ',
        'zend': '// ',
        'cakephp': '// ',
        'yii': '// ',
        'phalcon': '// ',
        'slim': '// ',
        'silex': '// ',
        'fuelphp': '// ',
        'zend': '// ',
        'thinkphp': '// ',
        'laravel': '// ',
        'lumen': '// ',
        'sails': '// ',
        'adonis': '// ',
        'nest': '// ',
        'express': '// ',
        'koa': '// ',
        'hapi': '// ',
        'loopback': '// ',
        'feathers': '// ',
        'ramda': '// ',
        'lodash': '// ',
        'underscore': '// ',
        'backbone': '// ',
        'marionette': '// ',
        'ember': '// ',
        'angular': '// ',
        'react': '// ',
        'vue': '// ',
        'svelte': '// ',
        'riot': '// ',
        'polymer': '// ',
        'aurelia': '// ',
        'knockout': '// ',
        'mithril': '// ',
        'preact': '// ',
        'alpine': '// ',
        'lit': '// ',
        'stencil': '// ',
        'ionic': '// ',
        'cordova': '// ',
        'phonegap': '// ',
        'reactnative': '// ',
        'flutter': '// ',
        'xamarin': '// ',
        'unity': '// ',
        'unreal': '// ',
        'godot': '// ',
        'construct': '// ',
        'gameMaker': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'processing': '// ',
        'p5': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'pixi': '// ',
        'phaser': '// ',
        'melonJS': '// ',
        'impact': '// ',
        'enchant': '// ',
        'crafty': '// ',
        'melonJS': '// ',
        'phaser': '// ',
        'pixi': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'p5': '// ',
        'processing': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'gameMaker': '// ',
        'construct': '// ',
        'godot': '// ',
        'unreal': '// ',
        'unity': '// ',
        'xamarin': '// ',
        'flutter': '// ',
        'reactnative': '// ',
        'phonegap': '// ',
        'cordova': '// ',
        'ionic': '// ',
        'stencil': '// ',
        'lit': '// ',
        'alpine': '// ',
        'preact': '// ',
        'mithril': '// ',
        'knockout': '// ',
        'aurelia': '// ',
        'polymer': '// ',
        'riot': '// ',
        'svelte': '// ',
        'vue': '// ',
        'react': '// ',
        'angular': '// ',
        'ember': '// ',
        'marionette': '// ',
        'backbone': '// ',
        'lodash': '// ',
        'ramda': '// ',
        'feathers': '// ',
        'loopback': '// ',
        'hapi': '// ',
        'koa': '// ',
        'express': '// ',
        'nest': '// ',
        'adonis': '// ',
        'sails': '// ',
        'lumen': '// ',
        'laravel': '// ',
        'symfony': '// ',
        'zend': '// ',
        'cakephp': '// ',
        'yii': '// ',
        'phalcon': '// ',
        'slim': '// ',
        'silex': '// ',
        'fuelphp': '// ',
        'zend': '// ',
        'thinkphp': '// ',
        'laravel': '// ',
        'lumen': '// ',
        'sails': '// ',
        'adonis': '// ',
        'nest': '// ',
        'express': '// ',
        'koa': '// ',
        'hapi': '// ',
        'loopback': '// ',
        'feathers': '// ',
        'ramda': '// ',
        'lodash': '// ',
        'underscore': '// ',
        'backbone': '// ',
        'marionette': '// ',
        'ember': '// ',
        'angular': '// ',
        'react': '// ',
        'vue': '// ',
        'svelte': '// ',
        'riot': '// ',
        'polymer': '// ',
        'aurelia': '// ',
        'knockout': '// ',
        'mithril': '// ',
        'preact': '// ',
        'alpine': '// ',
        'lit': '// ',
        'stencil': '// ',
        'ionic': '// ',
        'cordova': '// ',
        'phonegap': '// ',
        'reactnative': '// ',
        'flutter': '// ',
        'xamarin': '// ',
        'unity': '// ',
        'unreal': '// ',
        'godot': '// ',
        'construct': '// ',
        'gameMaker': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'processing': '// ',
        'p5': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'pixi': '// ',
        'phaser': '// ',
        'melonJS': '// ',
        'impact': '// ',
        'enchant': '// ',
        'crafty': '// ',
        'melonJS': '// ',
        'phaser': '// ',
        'pixi': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'p5': '// ',
        'processing': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'gameMaker': '// ',
        'construct': '// ',
        'godot': '// ',
        'unreal': '// ',
        'unity': '// ',
        'xamarin': '// ',
        'flutter': '// ',
        'reactnative': '// ',
        'phonegap': '// ',
        'cordova': '// ',
        'ionic': '// ',
        'stencil': '// ',
        'lit': '// ',
        'alpine': '// ',
        'preact': '// ',
        'mithril': '// ',
        'knockout': '// ',
        'aurelia': '// ',
        'polymer': '// ',
        'riot': '// ',
        'svelte': '// ',
        'vue': '// ',
        'react': '// ',
        'angular': '// ',
        'ember': '// ',
        'marionette': '// ',
        'backbone': '// ',
        'lodash': '// ',
        'ramda': '// ',
        'feathers': '// ',
        'loopback': '// ',
        'hapi': '// ',
        'koa': '// ',
        'express': '// ',
        'nest': '// ',
        'adonis': '// ',
        'sails': '// ',
        'lumen': '// ',
        'laravel': '// ',
        'symfony': '// ',
        'zend': '// ',
        'cakephp': '// ',
        'yii': '// ',
        'phalcon': '// ',
        'slim': '// ',
        'silex': '// ',
        'fuelphp': '// ',
        'zend': '// ',
        'thinkphp': '// ',
        'laravel': '// ',
        'lumen': '// ',
        'sails': '// ',
        'adonis': '// ',
        'nest': '// ',
        'express': '// ',
        'koa': '// ',
        'hapi': '// ',
        'loopback': '// ',
        'feathers': '// ',
        'ramda': '// ',
        'lodash': '// ',
        'underscore': '// ',
        'backbone': '// ',
        'marionette': '// ',
        'ember': '// ',
        'angular': '// ',
        'react': '// ',
        'vue': '// ',
        'svelte': '// ',
        'riot': '// ',
        'polymer': '// ',
        'aurelia': '// ',
        'knockout': '// ',
        'mithril': '// ',
        'preact': '// ',
        'alpine': '// ',
        'lit': '// ',
        'stencil': '// ',
        'ionic': '// ',
        'cordova': '// ',
        'phonegap': '// ',
        'reactnative': '// ',
        'flutter': '// ',
        'xamarin': '// ',
        'unity': '// ',
        'unreal': '// ',
        'godot': '// ',
        'construct': '// ',
        'gameMaker': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'processing': '// ',
        'p5': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'pixi': '// ',
        'phaser': '// ',
        'melonJS': '// ',
        'impact': '// ',
        'enchant': '// ',
        'crafty': '// ',
        'melonJS': '// ',
        'phaser': '// ',
        'pixi': '// ',
        'threejs': '// ',
        'babylon': '// ',
        'playcanvas': '// ',
        'p5': '// ',
        'processing': '// ',
        'cocos': '// ',
        'libGDX': '// ',
        'gameMaker': '// ',
        'construct': '// ',
        'godot': '// ',
        'unreal': '// ',
        'unity': '// ',
        'xamarin': '// ',
        'flutter': '// ',
        'reactnative': '// ',
        'phonegap': '// ',
        'cordova': '// ',
        'ionic': '// ',
        'stencil': '// ',
        'lit': '// ',
        'alpine': '// ',
        'preact': '// ',
        'mithril': '// ',
        'knockout': '// ',
        'aurelia': '// ',
        'polymer': '// ',
        'riot': '// ',
        'svelte': '// ',
        'vue': '// ',
        'react': '// ',
        'angular': '// ',
        'ember': '// ',
        'marionette': '// ',
        'backbone': '// ',
        'lodash': '// ',
        'ramda': '// ',
        'feathers': '// ',
        'loopback': '// ',
        'hapi': '// ',
        'koa': '// ',
        'express': '// ',
        'nest': '// ',
        'adonis': '// ',
        'sails': '// ',
        'lumen': '// ',
        'laravel': '// ',
        'symfony': '// ',
        'zend': '// ',
        'cakephp': '// ',
        'yii': '// ',
        'phalcon': '// ',
        'slim': '// ',
        'silex': '// ',
        'fuelphp': '// ',
        'zend': '// ',
        'thinkphp': '// ',
        'laravel': '// ',
        'lumen': '// ',
        'sails': '// ',
        'adonis': '// ',
        'nest': '// ',
        'express': '// ',
        'koa': '// ',
        'hapi': '// ',
        'loopback': '// ',
        'feathers': '// ',
        'ramda': '// ',
        'lodash': '// ',
        'underscore': '// ',
        'backbone': '// ',
        'marionette': '// ',
        'ember': '// ',
        'angular': '// ',
        'react': '// ',
        '
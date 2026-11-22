### FILE: lice/core.py
```python
"""Core functionality for the Lice License Generator."""

import argparse
import os
import sys
from enum import Enum
from io import StringIO


class LICENSES(Enum):
    """Enumeration of supported license types."""
    AFL3 = "afl3"
    AGPL3 = "agpl3"
    APACHE = "apache"
    BSD2 = "bsd2"
    BSD3 = "bsd3"
    CC_BY = "cc_by"
    ECLIPSE = "eclipse"
    GNU = "gnu"
    GPL2 = "gpl2"
    GPL3 = "gpl3"
    ISC = "isc"
    MIT = "mit"
    MPL2 = "mpl2"
    UNLICENSE = "unlicense"
    W3C = "w3c"
    ZLIB = "zlib"


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Generate license files")
    parser.add_argument("license", nargs="?", default=None,
                       help="The type of license to generate")
    parser.add_argument("-o", "--org", dest="organization",
                       help="The organization under which the license is registered")
    parser.add_argument("-p", "--proj", dest="project",
                       help="The project name for which the license is generated")
    parser.add_argument("-t", "--template", dest="template_path",
                       help="The path to a custom license template file")
    parser.add_argument("-y", "--year", dest="year",
                       help="The copyright year to be listed in the license")
    parser.add_argument("-l", "--language", dest="language",
                       help="The language for which the license header should be formatted")
    parser.add_argument("-f", "--file", dest="output_file",
                       help="The output file name where the license should be saved")
    parser.add_argument("--vars", action="store_true",
                       help="List all template variables for the specified license")

    args = parser.parse_args()

    # If no license specified, show help
    if not args.license:
        parser.print_help()
        return

    # Validate license
    try:
        license_enum = LICENSES(args.license.lower())
    except ValueError:
        print(f"Error: Unknown license '{args.license}'")
        return

    # Get context
    context = get_context(args)

    # Load template
    if args.template_path:
        template = load_file_template(args.template_path)
    else:
        template = load_template(license_enum.value, bool(args.language))

    # Extract variables if requested
    if args.vars:
        vars_list = extract_vars(template)
        print("Template variables:")
        for var in vars_list:
            print(f"  {var}")
        return

    # Generate license
    license_text = generate_license(template, context)

    # Format if needed
    if args.language:
        license_text = format_license(license_text, args.language)

    # Output
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(license_text)
    else:
        print(license_text)


def clean_path(p):
    """Clean up a path string."""
    return os.path.normpath(p)


def get_context(args):
    """Create a context object from command line arguments."""
    context = {
        "year": args.year or str(os.environ.get("YEAR", "")),
        "organization": args.organization or guess_organization(),
        "project": args.project or ""
    }
    return context


def guess_organization():
    """Guess the organization from git config or USER environment variable."""
    import subprocess
    try:
        result = subprocess.run(["git", "config", "--get", "user.name"],
                               capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.environ.get("USER", "Unknown")


def load_file_template(path):
    """Load a template from a file."""
    with open(path, 'r') as f:
        content = f.read()
    return StringIO(content)


def load_template(license_name, header=False):
    """Load a built-in template."""
    template_name = f"template-{license_name}{'-header' if header else ''}.txt"
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", template_name)
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_name}")
        
    with open(template_path, 'r') as f:
        content = f.read()
    return StringIO(content)


def extract_vars(template):
    """Extract variables from a template."""
    template.seek(0)
    lines = template.readlines()
    vars_list = []
    for line in lines:
        if "${" in line and "}" in line:
            start = line.find("${") + 2
            end = line.find("}")
            var = line[start:end]
            if var not in vars_list:
                vars_list.append(var)
    return vars_list


def generate_license(template, context):
    """Generate license text using the template and context."""
    template.seek(0)
    content = template.read()
    
    # Replace variables
    for key, value in context.items():
        content = content.replace("${" + key + "}", str(value))
    
    return content


def format_license(license_text, lang):
    """Format the license for a specific programming language."""
    # Simple mapping of languages to comment styles
    comment_styles = {
        "py": "# ",
        "js": "// ",
        "java": "// ",
        "c": "/* ",
        "cpp": "// ",
        "html": "<!-- ",
        "css": "/* ",
        "sh": "# ",
        "rb": "# ",
        "php": "// ",
        "go": "// ",
        "rs": "// ",
        "swift": "// ",
        "kt": "// ",
        "scala": "// ",
        "pl": "# ",
        "sql": "-- ",
        "yaml": "# ",
        "yml": "# ",
        "toml": "# ",
        "ini": "; ",
        "cfg": "; ",
        "conf": "; ",
        "log": "# ",
        "md": "<!-- ",
        "rst": ".. ",
        "tex": "% ",
        "lua": "-- ",
        "erl": "% ",
        "hs": "-- ",
        "ml": "(* ",
        "fs": "// ",
        "coffee": "# ",
        "ts": "// ",
        "tsx": "// ",
        "jsx": "// ",
        "elm": "-- ",
        "haskell": "-- ",
        "nim": "# ",
        "cr": "# ",
        "zig": "// ",
        "v": "// ",
        "glsl": "// ",
        "hlsl": "// ",
        "wgsl": "// ",
        "dockerfile": "# ",
        "makefile": "# ",
        "cmake": "# ",
        "ansible": "# ",
        "terraform": "# ",
        "puppet": "# ",
        "salt": "# ",
        "nix": "# ",
        "jinja": "{# ",
        "django": "{# ",
        "handlebars": "{{!",
        "mustache": "{{!",
        "liquid": "{%",
        "twig": "{# ",
        "jade": "// ",
        "pug": "// ",
        "sass": "// ",
        "scss": "// ",
        "less": "// ",
        "stylus": "// ",
        "graphql": "# ",
        "protobuf": "// ",
        "proto": "// ",
        "json": "// ",
        "xml": "<!-- ",
        "svg": "<!-- ",
        "rss": "<!-- ",
        "atom": "<!-- ",
        "csv": "# ",
        "tsv": "# ",
        "dat": "# ",
        "db": "-- ",
        "sqlite": "-- ",
        "mysql": "-- ",
        "postgresql": "-- ",
        "mongodb": "// ",
        "redis": "# ",
        "elasticsearch": "# ",
        "kafka": "# ",
        "rabbitmq": "# ",
        "docker-compose": "# ",
        "helm": "# ",
        "kubernetes": "# ",
        "openshift": "# ",
        "cloudformation": "# ",
        "terraform": "# ",
        "ansible": "# ",
        "puppet": "# ",
        "salt": "# ",
        "nix": "# ",
        "jinja": "{# ",
        "django": "{# ",
        "handlebars": "{{!",
        "mustache": "{{!",
        "liquid": "{%",
        "twig": "{# ",
        "jade": "// ",
        "pug": "// ",
        "sass": "// ",
        "scss": "// ",
        "less": "// ",
        "stylus": "// ",
        "graphql": "# ",
        "protobuf": "// ",
        "proto": "// ",
        "json": "// ",
        "xml": "<!-- ",
        "svg": "<!-- ",
        "rss": "<!-- ",
        "atom": "<!-- ",
        "csv": "# ",
        "tsv": "# ",
        "dat": "# ",
        "db": "-- ",
        "sqlite": "-- ",
        "mysql": "-- ",
        "postgresql": "-- ",
        "mongodb": "// ",
        "redis": "# ",
        "elasticsearch": "# ",
        "kafka": "# ",
        "rabbitmq": "# ",
        "docker-compose": "# ",
        "helm": "# ",
        "kubernetes": "# ",
        "openshift": "# ",
        "cloudformation": "# "
    }

    comment_style = comment_styles.get(lang.lower(), "# ")
    
    # Split the license into lines
    lines = license_text.split('\n')
    
    # Add comment style to each line
    formatted_lines = []
    for line in lines:
        if line.strip():  # Only comment non-empty lines
            formatted_lines.append(comment_style + line)
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)


def get_suffix(name):
    """Get file suffix from name."""
    if '.' in name:
        return name.split('.')[-1]
    return False
```
### FILE: lice/__init__.py
```python
"""Lice License Generator package."""

__version__ = "0.1.0"

from .core import main

__all__ = ["main"]
```

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
    parser.add_argument("license", nargs="?", help="Type of license to generate")
    parser.add_argument("-o", "--org", help="Organization name")
    parser.add_argument("-p", "--proj", help="Project name")
    parser.add_argument("-t", "--template", help="Path to custom template file")
    parser.add_argument("-y", "--year", help="Copyright year")
    parser.add_argument("-l", "--language", help="Language for header formatting")
    parser.add_argument("-f", "--file", help="Output file name")
    parser.add_argument("--vars", action="store_true", help="List template variables")

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
    if args.template:
        template = load_file_template(args.template)
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
    if args.file:
        with open(args.file, "w") as f:
            f.write(license_text)
    else:
        print(license_text)


def clean_path(p):
    """Clean up a file path."""
    return os.path.abspath(os.path.expanduser(p))


def get_context(args):
    """Create context object from command line arguments."""
    context = {
        "year": args.year or str(datetime.datetime.now().year),
        "organization": args.org or guess_organization(),
        "project": args.proj or ""
    }
    return context


def guess_organization():
    """Guess the organization from git config or USER env var."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "config", "--get", "user.name"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.environ.get("USER", "Unknown")


def load_file_template(path):
    """Load a template from a file."""
    with open(clean_path(path), "r") as f:
        return StringIO(f.read())


def load_template(license_name, header=False):
    """Load a built-in template."""
    template_name = f"template-{license_name}{'-header' if header else ''}.txt"
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", template_name)
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_name}")
        
    with open(template_path, "r") as f:
        return StringIO(f.read())


def extract_vars(template):
    """Extract variables from a template."""
    template_content = template.getvalue()
    vars_list = []
    for line in template_content.split('\n'):
        if '{{' in line and '}}' in line:
            # Extract variables between {{ and }}
            start = line.find('{{') + 2
            end = line.find('}}')
            if start > 1 and end > start:
                var = line[start:end].strip()
                if var not in vars_list:
                    vars_list.append(var)
    return vars_list


def generate_license(template, context):
    """Generate license text with context variables."""
    template_content = template.getvalue()
    
    # Replace variables
    for key, value in context.items():
        template_content = template_content.replace(f"{{{{{key}}}}}", str(value))
    
    return StringIO(template_content)


def format_license(license_text, lang):
    """Format license for a specific language."""
    # This is a simplified implementation
    # In a real implementation, this would map languages to comment styles
    lang_comments = {
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
        "log": "",
        "md": "",
        "txt": "",
        "rst": "",
        "adoc": "",
        "tex": "% ",
        "lua": "-- ",
        "erl": "% ",
        "hs": "-- ",
        "ml": "(* ",
        "fs": "// ",
        "coffee": "# ",
        "sass": "// ",
        "scss": "// ",
        "less": "// ",
        "styl": "// ",
        "elm": "-- ",
        "nim": "# ",
        "cr": "# ",
        "slim": "/",
        "haml": "-# ",
        "jade": "// ",
        "pug": "// ",
        "twig": "{# ",
        "handlebars": "{{!",
        "mustache": "{{!",
        "liquid": "{% ",
        "django": "{% ",
        "jinja": "{% ",
        "erb": "<% ",
        "rhtml": "<% ",
        "aspx": "<% ",
        "jsp": "<% ",
        "jspx": "<% ",
        "xhtml": "<!-- ",
        "svg": "<!-- ",
        "xml": "<!-- ",
        "json": "",
        "csv": "",
        "tsv": "",
        "dat": "",
        "db": "",
        "sqlite": "",
        "sqlitedb": "",
        "mdb": "",
        "accdb": "",
        "xls": "",
        "xlsx": "",
        "ods": "",
        "ppt": "",
        "pptx": "",
        "pdf": "",
        "epub": "",
        "mobi": "",
        "azw": "",
        "djvu": "",
        "fb2": "",
        "rtf": "",
        "doc": "",
        "docx": "",
        "odt": "",
        "wpd": "",
        "wpdf": "",
        "wps": "",
        "wpt": "",
        "wri": "",
        "wri2": "",
        "wri3": "",
        "wri4": "",
        "wri5": "",
        "wri6": "",
        "wri7": "",
        "wri8": "",
        "wri9": "",
        "wri10": "",
        "wri11": "",
        "wri12": "",
        "wri13": "",
        "wri14": "",
        "wri15": "",
        "wri16": "",
        "wri17": "",
        "wri18": "",
        "wri19": "",
        "wri20": "",
        "wri21": "",
        "wri22": "",
        "wri23": "",
        "wri24": "",
        "wri25": "",
        "wri26": "",
        "wri27": "",
        "wri28": "",
        "wri29": "",
        "wri30": "",
        "wri31": "",
        "wri32": "",
        "wri33": "",
        "wri34": "",
        "wri35": "",
        "wri36": "",
        "wri37": "",
        "wri38": "",
        "wri39": "",
        "wri40": "",
        "wri41": "",
        "wri42": "",
        "wri43": "",
        "wri44": "",
        "wri45": "",
        "wri46": "",
        "wri47": "",
        "wri48": "",
        "wri49": "",
        "wri50": "",
        "wri51": "",
        "wri52": "",
        "wri53": "",
        "wri54": "",
        "wri55": "",
        "wri56": "",
        "wri57": "",
        "wri58": "",
        "wri59": "",
        "wri60": "",
        "wri61": "",
        "wri62": "",
        "wri63": "",
        "wri64": "",
        "wri65": "",
        "wri66": "",
        "wri67": "",
        "wri68": "",
        "wri69": "",
        "wri70": "",
        "wri71": "",
        "wri72": "",
        "wri73": "",
        "wri74": "",
        "wri75": "",
        "wri76": "",
        "wri77": "",
        "wri78": "",
        "wri79": "",
        "wri80": "",
        "wri81": "",
        "wri82": "",
        "wri83": "",
        "wri84": "",
        "wri85": "",
        "wri86": "",
        "wri87": "",
        "wri88": "",
        "wri89": "",
        "wri90": "",
        "wri91": "",
        "wri92": "",
        "wri93": "",
        "wri94": "",
        "wri95": "",
        "wri96": "",
        "wri97": "",
        "wri98": "",
        "wri99": "",
        "wri100": ""
    }
    
    comment_prefix = lang_comments.get(lang.lower(), "# ")
    
    if comment_prefix == "":
        return license_text
    
    lines = license_text.split('\n')
    formatted_lines = []
    
    for line in lines:
        if line.strip() == "":
            formatted_lines.append("")
        else:
            formatted_lines.append(comment_prefix + line)
    
    return '\n'.join(formatted_lines)


def get_suffix(name):
    """Get file suffix from name."""
    if '.' in name:
        return name.split('.')[-1]
    return False
```
### FILE: lice/core.py
```python
"""Core functionality for the Lice License Generator."""

import argparse
import os
import sys
import datetime
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


class Context:
    """Context for license generation."""
    
    def __init__(self, year, organization, project):
        self.year = year
        self.organization = organization
        self.project = project


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Generate license files")
    parser.add_argument("license", nargs="?", help="Type of license to generate")
    parser.add_argument("-o", "--org", help="Organization name")
    parser.add_argument("-p", "--proj", help="Project name")
    parser.add_argument("-t", "--template", help="Path to custom template file")
    parser.add_argument("-y", "--year", help="Copyright year")
    parser.add_argument("-l", "--language", help="Programming language for header")
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
        print(f"Unknown license: {args.license}")
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
        for var in vars_list:
            print(var)
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
    """Create context object from arguments."""
    context = Context(
        year=args.year or str(datetime.datetime.now().year),
        organization=args.org or guess_organization(),
        project=args.proj or os.path.basename(os.getcwd()),
    )
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
        content = f.read()
    return StringIO(content)


def load_template(license_name, header=False):
    """Load a built-in template."""
    template_name = f"template-{license_name}{'-header' if header else ''}.txt"
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", template_name)
    with open(clean_path(template_path), "r") as f:
        content = f.read()
    return StringIO(content)


def extract_vars(template):
    """Extract variables from a template."""
    template.seek(0)
    lines = template.readlines()
    vars_list = []
    for line in lines:
        if "{{" in line and "}}" in line:
            # Extract variables between {{ and }}
            start = line.find("{{") + 2
            end = line.find("}}")
            if start > 1 and end > start:
                var = line[start:end].strip()
                if var not in vars_list:
                    vars_list.append(var)
    return vars_list


def generate_license(template, context):
    """Generate license text with context."""
    template.seek(0)
    content = template.read()
    
    # Replace variables
    for key, value in context.__dict__.items():
        content = content.replace("{{" + key + "}}", str(value))
    
    return StringIO(content)


def format_license(license_text, lang):
    """Format license for a specific language."""
    # This is a simplified implementation
    # In a real implementation, this would map languages to comment styles
    comment_styles = {
        "py": "# ",
        "js": "// ",
        "java": "// ",
        "c": "/* ",
        "cpp": "// ",
        "html": "<!-- ",
        "css": "/* ",
    }
    
    style = comment_styles.get(lang, "# ")
    
    if style == "/* ":
        # For block comments, we need to wrap the whole text
        lines = license_text.split('\n')
        formatted_lines = [style + line if line.strip() else line for line in lines]
        formatted_lines[0] = style + formatted_lines[0][len(style):]
        formatted_lines[-1] = formatted_lines[-1] + " */"
        return '\n'.join(formatted_lines)
    else:
        # For line comments, just prefix each line
        lines = license_text.split('\n')
        formatted_lines = [style + line if line.strip() else line for line in lines]
        return '\n'.join(formatted_lines)


# duty: Global_functions.get_suffix
def get_suffix(name):
    """Get file suffix from name."""
    if "." in name:
        return name.split(".")[-1]
    return False


class ArgumentParser:
    """Mock ArgumentParser class for duty implementation."""
    
    def __init__(self):
        self._action_groups = []
    
    def add_argument(self, *args, **kwargs):
        """Add an argument to the parser."""
        # This is a simplified implementation for the duty
        pass
    
    def parse_args(self):
        """Parse command line arguments."""
        # This is a simplified implementation for the duty
        return argparse.Namespace()


class StringIO:
    """Mock StringIO class for duty implementation."""
    
    def __init__(self, buf=None):
        self._buf = buf or ""
        self._pos = 0
    
    def write(self, str):
        """Write string to buffer."""
        self._buf += str
    
    def getvalue(self):
        """Get the current buffer contents."""
        return self._buf
    
    def close(self):
        """Close the buffer."""
        self._buf = None
    
    def seek(self, index):
        """Set the buffer position."""
        self._pos = index
    
    def readlines(self):
        """Read all lines from the buffer."""
        return self._buf.splitlines(True)
```
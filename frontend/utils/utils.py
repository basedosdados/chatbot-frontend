import re


def escape_currency(text: str):
    """Escape currency dollar signs ($) while preserving markdown math expressions.

    Args:
        text (str): Input text.

    Returns:
        str: Text with currency dollar signs escaped as \$.
    """
    # Regex to match math blocks ($$...$$), inline math ($...$), or single dollars ($)
    # Inline math must not contain white spaces at the beginning/end of the expression
    pattern = r'(\$\$[\s\S]*?\$\$)|(\$(?!\$)(?!\s)[^\$\n]*?[^\$\s]\$)|(\$)'

    def repl(match: re.Match):
        if match.group(1):
            return match.group(1)
        elif match.group(2):
            return match.group(2)
        else:
            return r'\$'

    return re.sub(pattern, repl, text)

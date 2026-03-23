import re

def get_file_suggestions(filepath: str, content: str, lang: str):
    """
    Analyzes file content and returns a list of improvement suggestions.
    Returns: [{"line": int, "message": str}, ...]
    """
    suggestions = []
    lines = content.splitlines()

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()
        
        # 1. Line Length Check
        if len(line) > 100:
            suggestions.append({
                "line": line_num,
                "message": "Line exceeds 100 characters. Consider breaking it down for readability."
            })

        # 2. TODO / FIXME Check
        if "TODO" in line.upper() or "FIXME" in line.upper():
            suggestions.append({
                "line": line_num,
                "message": "Unresolved TODO or FIXME comment."
            })

        # 3. Console.log / Print statements (assuming production code shouldn't have them loosely)
        if lang in ["JavaScript", "TypeScript", "React", "React TypeScript", "Vue", "Svelte"]:
            if re.search(r'\bconsole\.(log|debug|info)\(', line):
                suggestions.append({
                    "line": line_num,
                    "message": "Avoid leaving debugging console logs in production code."
                })
        elif lang == "Python":
            if re.search(r'\bprint\(', line) and not "import" in line:
                suggestions.append({
                    "line": line_num,
                    "message": "Avoid leaving print statements in production code. Use logging instead."
                })

        # 4. Deep Nesting Check (Basic Indentation check)
        # Using indentation spaces to detect deep nesting 
        if line.startswith(' '):
            indent_count = len(line) - len(line.lstrip(' '))
            # Assuming 4 spaces per indent, > 16 means 4+ levels of nesting
            # Assuming 2 spaces per indent, > 12 means 6+ levels
            if indent_count > 16:
                 # Check if the line actually has code
                 if stripped not in ["}", "]", ");", "};"]:
                     suggestions.append({
                         "line": line_num,
                         "message": "Deeply nested code block detected. Consider refactoring into smaller functions."
                     })
                     
    return suggestions

import re

def extract_ts_structure(filepath: str):
    """Fallback structural parser for TS/React returning mapped hierarchical data."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return None
        
    classes = []
    interfaces = []
    functions = {} 
    
    current_func = None

    for line in lines:
        c_match = re.search(r'class\s+([A-Za-z0-9_]+)', line)
        if c_match:
            base_m = re.search(r'extends\s+([A-Za-z0-9_]+)', line)
            classes.append({"name": c_match.group(1), "bases": [base_m.group(1)] if base_m else [], "methods": []})
            current_func = None
            continue
            
        i_match = re.search(r'interface\s+([A-Za-z0-9_]+)', line)
        if i_match:
            interfaces.append({"name": i_match.group(1), "methods": []})
            current_func = None
            continue
            
        f_match = re.search(r'(?:function\s+([A-Za-z0-9_]+)|const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z0-9_]+)\s*=>)', line)
        if f_match:
            name = f_match.group(1) or f_match.group(2)
            if name:
                if name not in functions:
                    functions[name] = {"name": name, "loc": 0, "renders": [], "calls": []}
                current_func = name
                
        if current_func:
            call_m = re.findall(r'([A-Za-z0-9_]+)\(', line)
            for c in call_m:
                if c not in ["function", "const", "let", "var", "if", "for", "while", "switch", "catch", "return", "require"]:
                    functions[current_func]["calls"].append(c)
                    
            render_m = re.findall(r'<([A-Z][A-Za-z0-9_]+)', line)
            for r in render_m:
                functions[current_func]["renders"].append(r)
                
    for f_data in functions.values():
        f_data["calls"] = list(set(f_data["calls"]))
        f_data["renders"] = list(set(f_data["renders"]))
        
    return {
        "classes": classes,
        "interfaces": interfaces,
        "functions": list(functions.values())
    }

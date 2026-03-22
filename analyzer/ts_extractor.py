import re

def extract_ts_structure(filepath: str):
    """Fallback structural parser for TS/React returning mapped hierarchical data."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception:
        return None
        
    classes = []
    interfaces = []
    functions = []
    
    class_matches = re.finditer(r'class\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_]+))?', source)
    for m in class_matches:
        classes.append({"name": m.group(1), "bases": [m.group(2)] if m.group(2) else [], "methods": []})
        
    interface_matches = re.finditer(r'interface\s+([A-Za-z0-9_]+)', source)
    for m in interface_matches:
        interfaces.append({"name": m.group(1), "methods": []})
        
    func_matches = re.finditer(r'(?:function\s+([A-Za-z0-9_]+)|const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z0-9_]+)\s*=>)', source)
    for m in func_matches:
        name = m.group(1) or m.group(2)
        if name:
            functions.append({"name": name, "loc": 0})
            
    return {
        "classes": classes,
        "interfaces": interfaces,
        "functions": functions
    }

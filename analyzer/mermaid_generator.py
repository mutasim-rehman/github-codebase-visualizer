import os

def generate_mermaid_diagrams(stats, output_path="architecture.md"):
    all_files = stats["all_files"]
    
    lines = []
    lines.append("# Codebase Architecture Diagrams\n")
    
    # 1. Module / Package Graph
    lines.append("## Module Dependency Graph\n")
    lines.append("```mermaid\ngraph TD")
    
    node_map = {}
    for idx, f in enumerate(all_files):
        node_map[f["path"]] = f"F{idx}"
        
    for f in all_files:
        f_id = node_map[f["path"]]
        name = os.path.basename(f["path"])
        lines.append(f'    {f_id}["{name}"]')
        
    for f in all_files:
        f_id = node_map[f["path"]]
        for imp in f.get("imports", [])[:10]:
            match_id = None
            for path, nid in node_map.items():
                if isinstance(imp, str) and imp in path:
                    match_id = nid
                    break
            if match_id and match_id != f_id:
                lines.append(f'    {f_id} --> {match_id}')
                
    lines.append("```\n")
    
    # 2. Class / Interface Diagram
    lines.append("## Static Class & Interface Structure\n")
    lines.append("```mermaid\nclassDiagram")
    
    for f in all_files:
        if "ast_metrics" in f and f["ast_metrics"] and "structure" in f["ast_metrics"]:
            struct = f["ast_metrics"]["structure"]
            for cls in struct.get("classes", []):
                lines.append(f'    class {cls["name"]} {{')
                for m in cls.get("methods", []):
                    lines.append(f'        +{m["name"]}()')
                lines.append('    }')
                for b in cls.get("bases", []):
                    lines.append(f'    {b} <|-- {cls["name"]}')
                    
        if "ts_metrics" in f and f["ts_metrics"]:
            struct = f["ts_metrics"]
            for cls in struct.get("classes", []):
                lines.append(f'    class {cls["name"]} {{')
                lines.append('    }')
                for b in cls.get("bases", []):
                    lines.append(f'    {b} <|-- {cls["name"]}')
            for intf in struct.get("interfaces", []):
                lines.append(f'    class {intf["name"]} {{')
                lines.append('        <<interface>>')
                lines.append('    }')
                
    lines.append("```\n")
    
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("\n".join(lines))
        
    return output_path

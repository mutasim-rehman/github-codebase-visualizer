import os

def extract_basename(path_str):
    base = os.path.basename(path_str)
    name, _ = os.path.splitext(base)
    return name

def build_impact_graph(all_files):
    name_to_file = {}
    for f in all_files:
        name = extract_basename(f["path"])
        name_to_file[name] = f["path"]

    impact_map = {f["path"]: {"upstream": [], "downstream": []} for f in all_files}

    for f in all_files:
        f_path = f["path"]
        for imp in f.get("imports", []):
            imp_name = str(imp).split('/')[-1].split('\\')[-1]
            imp_name = imp_name.replace('.ts', '').replace('.js', '').replace('.py', '').replace('.jsx', '').replace('.tsx', '')
            
            if imp_name in name_to_file:
                target_path = name_to_file[imp_name]
                if target_path != f_path:
                    if target_path not in impact_map[f_path]["downstream"]:
                        impact_map[f_path]["downstream"].append(target_path)
                    if f_path not in impact_map[target_path]["upstream"]:
                        impact_map[target_path]["upstream"].append(f_path)
                        
    # Calculate blast radius using BFS (transitive upstream dependents)
    for f in all_files:
        f_path = f["path"]
        visited = set()
        queue = [(f_path, 0)]
        max_depth = 3
        while queue:
            curr, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for up in impact_map[curr]["upstream"]:
                if up not in visited:
                    visited.add(up)
                    queue.append((up, depth + 1))
        
        impact_map[f_path]["blast_radius"] = len(visited)

    return impact_map

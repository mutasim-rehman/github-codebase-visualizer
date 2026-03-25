import os

def detect_architecture_issues(all_files, impact_map):
    issues = []
    
    # 1. Mass Duplication
    duplicate_count = sum(1 for f in all_files if f.get("is_duplicate"))
    if len(all_files) > 0 and (duplicate_count / len(all_files)) > 0.1:
        issues.append({
            "title": "Mass Duplication",
            "severity": "High",
            "description": f"Over 10% ({duplicate_count} files) of the codebase consists of exact duplicates.",
            "files": [],
            "recommendation": "Perform a major refactoring to abstract common logic into shared modules, reducing maintenance overhead."
        })

    # 2. God Files (Highly Centralized Modules)
    god_files = []
    for f in all_files:
        path = f["path"]
        loc = f.get("loc", 0)
        impact = impact_map.get(path, {})
        blast_radius = impact.get("blast_radius", 0)
        upstream_count = len(impact.get("upstream", []))
        
        if loc > 1000 and blast_radius > 15 and upstream_count > 5:
            god_files.append(path)
            
    if god_files:
        issues.append({
            "title": "God Files Detected",
            "severity": "High",
            "description": f"Found {len(god_files)} oversized, highly-depended-upon files that represent single points of failure.",
            "files": god_files[:5],
            "recommendation": "Break down these massive files into smaller, specialized modules to improve maintainability and decouple downstream dependents."
        })
        
    # 3. Logical Layering Violations
    layer_violations = []
    low_level = ["utils", "util", "core", "shared", "helpers", "lib"]
    high_level = ["components", "pages", "app", "features", "ui", "views"]
    
    for path, impact in impact_map.items():
        folder = path.replace('\\', '/').split('/')[0].lower()
        if folder in low_level:
            downstream = impact.get("downstream", [])
            for down in downstream:
                down_folder = down.replace('\\', '/').split('/')[0].lower()
                if down_folder in high_level:
                    if path not in layer_violations:
                        layer_violations.append(path)
                    break
                    
    if layer_violations:
        issues.append({
            "title": "Logical Layering Violation",
            "severity": "Medium",
            "description": f"Low-level utility/core modules are directly importing high-level UI/feature modules.",
            "files": layer_violations[:5],
            "recommendation": "Invert the dependency direction. Utilities should be domain-agnostic and should not depend on specific features or UI components."
        })

    # 4. Circular Dependencies (Basic DFS cycle detection)
    visited = set()
    rec_stack = set()
    cycles_found = set()
    
    def dfs(node, path_stack):
        visited.add(node)
        rec_stack.add(node)
        
        downstream = impact_map.get(node, {}).get("downstream", [])
        for neighbor in downstream:
            if neighbor not in visited:
                dfs(neighbor, path_stack + [neighbor])
            elif neighbor in rec_stack:
                idx = path_stack.index(neighbor)
                cycle = path_stack[idx:]
                cycle_tuple = tuple(sorted(cycle))
                if cycle_tuple not in cycles_found:
                    cycles_found.add(cycle_tuple)
                    if len(cycles_found) <= 5: # Limit reporting
                        issues.append({
                            "title": "Circular Dependency",
                            "severity": "Medium",
                            "description": f"A dependency cycle was found: {' -> '.join(cycle)} -> {neighbor}",
                            "files": cycle,
                            "recommendation": "Refactor to break the cycle, typically by extracting the shared dependency into a third module or using dependency inversion."
                        })
                        
        rec_stack.remove(node)

    for node in impact_map:
        if node not in visited:
            dfs(node, [node])

    return issues

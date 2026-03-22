from analyzer.python_ast import analyze_python_file

def detect_hotspots(files_list):
    """
    Identifies files that are large or highly complex.
    Expects files_list from core.analyze_directory
    Returns a list of hotspot dicts.
    """
    hotspots = []
    
    for f in files_list:
        score = 0
        reasons = []
        
        # LOC heuristics
        if f["loc"] > 500:
            score += 1
            reasons.append(f"Large file ({f['loc']} lines)")
        if f["loc"] > 1000:
            score += 2
            
        # Complexity heuristics for Python files
        if f["lang"] == "Python":
            ast_metrics = analyze_python_file(f["full_path"])
            f["ast_metrics"] = ast_metrics  # Attach for reporting
            
            if ast_metrics:
                if ast_metrics["max_nesting"] > 3:
                    score += 2
                    reasons.append(f"Deep nesting (depth {ast_metrics['max_nesting']})")
                
                lf = ast_metrics["longest_function"]
                if lf["loc"] > 100:
                    score += 1
                    reasons.append(f"Long function '{lf['name']}' ({lf['loc']} lines)")
                    
                pf = ast_metrics.get("problematic_functions", [])
                score += len(pf) * 2
                for p in pf:
                    reasons.append(f"Problematic func '{p['name']}' (LOC: {p['loc']}, Nesting: {p['nesting']})")
                    
                deps = ast_metrics.get("imports", [])
                if len(deps) > 15:
                    score += 1
                    reasons.append(f"High coupling ({len(deps)} imports)")
                    
                f["imports"] = deps
                f["classes"] = ast_metrics["classes"]
                f["functions"] = ast_metrics["functions"]
                    
        # Consider it a hotspot if score >= 2
        if score >= 2:
            risk_level = "High" if score >= 4 else "Medium"
            hotspots.append({
                "path": f["path"],
                "score": score,
                "reasons": reasons,
                "loc": f["loc"],
                "risk_level": risk_level
            })
            
    # Sort by score descending, then loc
    hotspots.sort(key=lambda x: (x["score"], x["loc"]), reverse=True)
    return hotspots

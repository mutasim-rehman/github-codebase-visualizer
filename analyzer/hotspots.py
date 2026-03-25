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
        recommendations = []
        
        # Duplication heuristic
        if f.get("is_duplicate"):
            score += 3
            reasons.append("Duplicate file")
            recommendations.append({
                "issue": "Duplicate file",
                "action": "Abstract common logic into a shared utility or remove one of the copies."
            })
            
        # LOC heuristics
        if f["loc"] > 500:
            score += 1
            reasons.append(f"Large file ({f['loc']} lines)")
            recommendations.append({
                "issue": f"Large file ({f['loc']} lines)",
                "action": "Consider splitting this file into smaller, logical modules or components."
            })
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
                    recommendations.append({
                        "issue": f"Deep nesting (depth {ast_metrics['max_nesting']})",
                        "action": "Extract deeply nested blocks into separate helper functions to reduce cyclomatic complexity."
                    })
                
                lf = ast_metrics["longest_function"]
                if lf["loc"] > 100:
                    score += 1
                    reasons.append(f"Long function '{lf['name']}' ({lf['loc']} lines)")
                    recommendations.append({
                        "issue": f"Long function '{lf['name']}' ({lf['loc']} lines)",
                        "action": "Refactor the function by extracting reusable parts into smaller functions."
                    })
                    
                pf = ast_metrics.get("problematic_functions", [])
                score += len(pf) * 2
                for p in pf:
                    reasons.append(f"Problematic func '{p['name']}' (LOC: {p['loc']}, Nesting: {p['nesting']})")
                    recommendations.append({
                        "issue": f"Problematic func '{p['name']}' (LOC: {p['loc']}, Nesting: {p['nesting']})",
                        "action": "Refactor this function to reduce both its length and nesting depth."
                    })
                    
                deps = ast_metrics.get("imports", [])
                if len(deps) > 15:
                    score += 1
                    reasons.append(f"High coupling ({len(deps)} imports)")
                    recommendations.append({
                        "issue": f"High coupling ({len(deps)} imports)",
                        "action": "Introduce a facade or use dependency injection to reduce the number of direct imports."
                    })
                    
                f["imports"] = deps
                f["classes"] = ast_metrics["classes"]
                f["functions"] = ast_metrics["functions"]
                
        elif f["lang"] in ["JavaScript", "TypeScript", "React", "React TypeScript", "Vue", "Svelte"]:
            from analyzer.ts_extractor import extract_ts_structure
            ts_metrics = extract_ts_structure(f["full_path"])
            f["ts_metrics"] = ts_metrics
            
            if ts_metrics:
                # Add light score heuristics for huge JS classes/components
                if len(ts_metrics.get("classes", [])) > 5:
                    score += 1
                    reasons.append(f"Too many classes/components ({len(ts_metrics['classes'])})")
                    recommendations.append({
                        "issue": f"Too many classes/components ({len(ts_metrics['classes'])})",
                        "action": "Split into separate files per component/class to improve maintainability."
                    })
                if len(ts_metrics.get("functions", [])) > 15:
                    score += 1
                    reasons.append(f"Too many functions/hooks ({len(ts_metrics['functions'])})")
                    recommendations.append({
                        "issue": f"Too many functions/hooks ({len(ts_metrics['functions'])})",
                        "action": "Extract related functions into custom hooks or utility modules."
                    })
                
        f["score"] = score
        f["reasons"] = reasons
        f["recommendations"] = recommendations
        
        if score >= 4:
            f["risk_level"] = "High"
        elif score >= 2:
            f["risk_level"] = "Medium"
        else:
            f["risk_level"] = "Low"
                    
        # Consider it a hotspot if score >= 2
        if score >= 2:
            hotspots.append({
                "path": f["path"],
                "score": score,
                "reasons": reasons,
                "recommendations": recommendations,
                "loc": f["loc"],
                "risk_level": f["risk_level"]
            })
            
    # Sort by score descending, then loc
    hotspots.sort(key=lambda x: (x["score"], x["loc"]), reverse=True)
    return hotspots

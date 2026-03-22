import os
import json

def export_frontend_data(stats, hotspots, output_dir="frontend/public"):
    all_files = stats["all_files"]
    
    file_data = []
    
    for f in all_files:
        path = f["path"]
        loc = f["loc"]
        lang = f["lang"]
        is_dup = f.get("is_duplicate", False)
        is_gen = f.get("is_generated", False)
        risk = f.get("risk_level", "Low")
        score = f.get("score", 0)
        
        functions = []
        classes = []
        if "ast_metrics" in f and f["ast_metrics"] and "structure" in f["ast_metrics"]:
            s = f["ast_metrics"]["structure"]
            functions = [{"name": x["name"], "loc": x.get("loc", 0)} for x in s.get("functions", [])]
            classes = [{"name": x["name"], "methods": len(x.get("methods", []))} for x in s.get("classes", [])]
        elif "ts_metrics" in f and f["ts_metrics"]:
            s = f["ts_metrics"]
            functions = [{"name": x["name"], "loc": x.get("loc", 0)} for x in s.get("functions", [])]
            classes = [{"name": x["name"], "methods": len(x.get("methods", []))} for x in s.get("classes", [])]
            
        imports = f.get("imports", [])
        
        # Calculate Radar data
        loc_val = min(10, f["loc"] / 100)
        functions_val = min(10, len(functions) / 5)
        nesting_val = 0
        if "ast_metrics" in f and f["ast_metrics"]:
            nesting_val = min(10, f["ast_metrics"].get("max_nesting", 0))
        deps_val = min(10, len(imports) / 3)
        score_val = min(10, score * 1.5)
        
        if nesting_val == 0 and score_val > 0:
            nesting_val = min(10, score_val / 2)
            
        radar_data = [loc_val, functions_val, nesting_val, deps_val, score_val]
        
        file_data.append({
            "path": path,
            "loc": loc,
            "lang": lang,
            "risk": risk,
            "score": score,
            "is_dup": is_dup,
            "is_gen": is_gen,
            "functions": functions,
            "classes": classes,
            "imports": imports[:20],
            "radar": radar_data
        })
        
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "data.json")
    
    # Also save overall stats summary
    overall_stats = {
        "total_files": stats.get("total_files", 0),
        "total_loc": stats.get("total_loc", 0),
        "languages": stats.get("languages", {}),
        "hotspots_count": len(hotspots)
    }
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"files": file_data, "stats": overall_stats}, f, indent=2)
        
    return out_path

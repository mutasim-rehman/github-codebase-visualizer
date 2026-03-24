import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

from analyzer.git_utils import clone_repo
from analyzer.core import analyze_directory
from analyzer.hotspots import detect_hotspots
from analyzer.git_history import analyze_git_history
from analyzer.suggestions import get_file_suggestions
from analyzer.core import LANG_MAP

app = Flask(__name__)
CORS(app)  # Allow the Vite dev server to call this API


def build_export_payload(stats, hotspots):
    """Converts raw stats + hotspots into a clean JSON payload for the frontend."""
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

        # Compute radar dimensions
        loc_val = min(10, loc / 100)
        functions_val = min(10, len(functions) / 5)
        nesting_val = 0
        if "ast_metrics" in f and f["ast_metrics"]:
            nesting_val = min(10, f["ast_metrics"].get("max_nesting", 0))
        deps_val = min(10, len(imports) / 3)
        score_val = min(10, score * 1.5)
        if nesting_val == 0 and score_val > 0:
            nesting_val = min(10, score_val / 2)

        file_data.append({
            "path": path,
            "loc": loc,
            "lang": lang,
            "risk": risk,
            "score": score,
            "reasons": f.get("reasons", []),
            "is_dup": is_dup,
            "is_gen": is_gen,
            "functions": functions,
            "classes": classes,
            "imports": imports[:20],
            "radar": [loc_val, functions_val, nesting_val, deps_val, score_val]
        })

    lang_stats = stats.get("lang_stats", {})
    languages_summary = {lang: info.get("loc", 0) for lang, info in lang_stats.items()}

    diagrams = build_diagrams(all_files)
    hotspot_radar = build_hotspot_radar(hotspots, all_files)

    return {
        "files": file_data,
        "stats": {
            "total_files": stats.get("total_files", 0),
            "total_loc": stats.get("total_loc", 0),
            "languages": languages_summary,
            "hotspots_count": len(hotspots),
            "duplicates_count": len(stats.get("duplicates", [])),
            "session_path": stats.get("session_path", ""),
        },
        "diagrams": diagrams,
        "hotspot_radar": hotspot_radar,
    }


def build_diagrams(all_files):
    """Generate Mermaid diagram strings in memory (no file write) with top-down layouts, subgraphs, and size limits."""
    MAX_NODES = 30
    DEPTH_LIMIT = 2

    def get_folder(path_str):
        path_str = path_str.replace("\\", "/")
        parts = path_str.split("/")
        if len(parts) > 1:
            return parts[0]
        return "root"

    def is_utility(folder_name):
        return folder_name.lower() in ["utils", "util", "helpers", "shared", "tests", "test", "common", "lib"]

    # --- 1. Module Dependency Graph ---
    def file_score(f):
        return f.get("loc", 0) + len(f.get("imports", [])) * 10

    sorted_files = sorted(all_files, key=file_score, reverse=True)
    top_files = sorted_files[:MAX_NODES]

    dep_lines = ["graph TB"]
    folders = {}
    node_map = {}
    placeholder_nodes = set()

    for i, f in enumerate(top_files):
        folder = get_folder(f["path"])
        fid = f"F{i}"
        
        if is_utility(folder):
            fid = f"GRP_DEP_{folder}"
            node_map[f["path"]] = fid
            if fid not in placeholder_nodes:
                placeholder_nodes.add(fid)
                folders.setdefault("Utilities", []).append((fid, f"{folder}/*"))
        else:
            node_map[f["path"]] = fid
            folders.setdefault(folder, []).append((fid, os.path.basename(f["path"]).replace('"', "'")))

    for folder, nodes in folders.items():
        if len(nodes) == 1 and folder == "root":
            dep_lines.append(f'    {nodes[0][0]}["{nodes[0][1]}"]')
        else:
            dep_lines.append(f'    subgraph {folder}')
            for fid, name in nodes:
                dep_lines.append(f'        {fid}["{name}"]')
            dep_lines.append('    end')

    added_edges = set()
    MAX_DEP_EDGES = 80
    for f in top_files:
        if len(added_edges) >= MAX_DEP_EDGES:
            break
        fid = node_map[f["path"]]
        for imp in f.get("imports", [])[:6]:
            for path, nid in node_map.items():
                if isinstance(imp, str) and imp in path and nid != fid:
                    edge = (fid, nid)
                    if edge not in added_edges and len(added_edges) < MAX_DEP_EDGES:
                        added_edges.add(edge)
                        dep_lines.append(f"    {fid} --> {nid}")
                    break

    if len(all_files) > MAX_NODES:
        dep_lines.append(f"    truncNote[\"⚠ Showing Top {MAX_NODES} modules\"]")


    # --- 2. Class / Interface Diagram ---
    class_lines = ["classDiagram"]
    seen_classes = set()
    class_folders = {}
    
    class_list = []
    class_file_map = {}
    for f in all_files:
        folder = get_folder(f["path"])
        if "ast_metrics" in f and f["ast_metrics"] and "structure" in f["ast_metrics"]:
            classes_list = f["ast_metrics"]["structure"].get("classes", [])
        elif "ts_metrics" in f and f["ts_metrics"]:
            classes_list = f["ts_metrics"].get("classes", [])
        else:
            classes_list = []
            
        for cls in classes_list:
            class_list.append(cls)
            class_file_map[cls["name"]] = folder

    class_list = sorted(class_list, key=lambda c: len(c.get("methods", [])), reverse=True)[:MAX_NODES]
    
    for cls in class_list:
        cname = cls["name"].replace(" ", "_").replace(".", "_")
        if cname in seen_classes:
            continue
        seen_classes.add(cname)
        folder = class_file_map.get(cls["name"], "root")
        class_folders.setdefault(folder, []).append(cls)
        
    for folder, classes in class_folders.items():
        if folder != "root":
            class_lines.append(f"    namespace {folder} {{")
        for cls in classes:
            cname = cls["name"].replace(" ", "_").replace(".", "_")
            prefix = "        " if folder != "root" else "    "
            class_lines.append(f"{prefix}class {cname} {{")
            for m in cls.get("methods", [])[:5]:
                mname = m["name"].replace(" ", "_").replace("<", "").replace(">", "")
                class_lines.append(f"{prefix}    +{mname}()")
            class_lines.append(f"{prefix}}}")
        if folder != "root":
            class_lines.append("    }")
            
    for cls in class_list:
        cname = cls["name"].replace(" ", "_").replace(".", "_")
        for base in cls.get("bases", []):
            bname = base.replace(" ", "_").replace(".", "_")
            if bname in seen_classes:
                class_lines.append(f"    {bname} <|-- {cname}")

    if len(class_lines) <= 2:
        class_lines.append("    %% No classes or interfaces detected")


    # --- 3. Function Call Graph ---
    func_map = {}
    for f in all_files:
        filepath = f["path"]
        folder = get_folder(filepath)
        
        if "ast_metrics" in f and f["ast_metrics"] and "structure" in f["ast_metrics"]:
            funcs_list = f["ast_metrics"]["structure"].get("functions", [])
        elif "ts_metrics" in f and f["ts_metrics"]:
            funcs_list = f["ts_metrics"].get("functions", [])
        else:
            funcs_list = []
            
        for fn in funcs_list:
            name = fn["name"]
            if name not in func_map:
                func_map[name] = {
                    "name": name,
                    "loc": fn.get("loc", 0),
                    "file": filepath,
                    "folder": folder,
                    "calls": fn.get("calls", [])
                }
                
    sorted_funcs = sorted(func_map.values(), key=lambda x: x["loc"] + len(x["calls"])*10, reverse=True)
    top_funcs = sorted_funcs[:MAX_NODES]

    included_funcs = set()
    call_edges = set()
    
    for start_fn in top_funcs:
        queue = [(start_fn["name"], 0)]
        while queue:
            curr_name, depth = queue.pop(0)
            if curr_name not in included_funcs:
                included_funcs.add(curr_name)
            if depth < DEPTH_LIMIT:
                func_data = func_map.get(curr_name)
                if func_data:
                    for call_target in func_data["calls"][:5]:
                        if call_target in func_map:
                            call_edges.add((curr_name, call_target))
                            if call_target not in included_funcs:
                                queue.append((call_target, depth + 1))

    call_folders = {}
    collapsed_utils = set()
    
    for fn_name in included_funcs:
        fdata = func_map.get(fn_name)
        if fdata:
            folder = fdata["folder"]
            # To ensure compatibility with Mermaid nodes, strip special chars
            safe_fn = fn_name.replace('"', '').replace(" ", "_").replace("<", "").replace(">", "")
            if not safe_fn.strip():
                continue

            if is_utility(folder):
                collapsed_utils.add(folder)
            else:
                call_folders.setdefault(folder, []).append((fn_name, safe_fn))

    call_lines = ["graph TB"]
    for folder in collapsed_utils:
         call_lines.append(f'    GRP_CALL_{folder}["{folder}/* (Utils)"]')
         
    for folder, fn_tuples in call_folders.items():
        if folder == "root":
            for orig, safe in fn_tuples:
                call_lines.append(f'    {safe}["{safe}()"]')
        else:
            call_lines.append(f'    subgraph {folder}')
            for orig, safe in fn_tuples:
                call_lines.append(f'        {safe}["{safe}()"]')
            call_lines.append('    end')

    MAX_CALL_EDGES_LIMIT = 150
    final_edges = 0
    for src, dst in call_edges:
        if final_edges >= MAX_CALL_EDGES_LIMIT:
            break
        src_data = func_map.get(src)
        dst_data = func_map.get(dst)
        
        src_safe = src.replace('"', '').replace(" ", "_").replace("<", "").replace(">", "")
        dst_safe = dst.replace('"', '').replace(" ", "_").replace("<", "").replace(">", "")
        if not src_safe.strip() or not dst_safe.strip():
            continue

        if src_data and is_utility(src_data["folder"]):
            src_safe = f'GRP_CALL_{src_data["folder"]}'
            
        if dst_data and is_utility(dst_data["folder"]):
            dst_safe = f'GRP_CALL_{dst_data["folder"]}'
            
        if src_safe != dst_safe:
            # check if edges inside call lines already
            edge_str = f'    {src_safe} --> {dst_safe}'
            if edge_str not in call_lines:
                call_lines.append(edge_str)
                final_edges += 1

    if len(call_lines) == 1:
        call_lines.append("    %% No internal call data detected")


    # --- 4. React Render Tree ---
    render_lines = ["graph TB"]
    render_edges = set()
    MAX_RENDER_NODES = 30
    
    react_components = []
    
    for f in all_files:
        if "ts_metrics" in f and f["ts_metrics"]:
            struct = f["ts_metrics"]
            folder = get_folder(f["path"])
            for fn in struct.get("functions", []):
                if fn.get("renders"):
                    react_components.append({
                        "name": fn["name"],
                        "folder": folder,
                        "renders": fn["renders"]
                    })
                    
    react_components = sorted(react_components, key=lambda x: len(x["renders"]), reverse=True)[:MAX_RENDER_NODES]
    comp_map = {rc["name"]: rc for rc in react_components}
    
    for rc in react_components:
        for render in rc.get("renders", [])[:6]:
            if render in comp_map:
                render_edges.add((rc["name"], render))

    ren_folders = {}
    for rc in react_components:
        safe_name = rc["name"].replace('"', "").replace("<", "").replace(">", "")
        if safe_name.strip():
            ren_folders.setdefault(rc["folder"], []).append(safe_name)
        
    for folder, comps in ren_folders.items():
        if folder == "root":
            for c in comps:
                render_lines.append(f'    {c}["<{c} />"]')
        else:
            render_lines.append(f'    subgraph {folder}')
            for c in comps:
                render_lines.append(f'        {c}["<{c} />"]')
            render_lines.append('    end')
            
    for src, dst in render_edges:
        ss = src.replace('"', "").replace("<", "").replace(">", "")
        ds = dst.replace('"', "").replace("<", "").replace(">", "")
        if ss.strip() and ds.strip():
            render_lines.append(f'    {ss} --> {ds}')

    if len(render_lines) == 1:
        render_lines.append("    %% No React component rendering detected")

    return {
        "dependency": "\n".join(dep_lines),
        "class_diagram": "\n".join(class_lines),
        "call_graph": "\n".join(call_lines),
        "render_tree": "\n".join(render_lines),
    }



def build_hotspot_radar(hotspots, all_files):
    """Build multi-dataset radar data for top-5 riskiest files."""
    top = sorted(hotspots, key=lambda x: x["score"], reverse=True)[:5]
    file_map = {f["path"]: f for f in all_files}
    colors = [
        {"bg": "rgba(248,81,73,0.2)", "border": "rgb(248,81,73)"},
        {"bg": "rgba(163,113,247,0.2)", "border": "rgb(163,113,247)"},
        {"bg": "rgba(210,153,34,0.2)", "border": "rgb(210,153,34)"},
        {"bg": "rgba(56,139,253,0.2)", "border": "rgb(56,139,253)"},
        {"bg": "rgba(63,185,80,0.2)", "border": "rgb(63,185,80)"},
    ]
    datasets = []
    for idx, h in enumerate(top):
        f = file_map.get(h["path"], {})
        loc = f.get("loc", 0)
        imports = f.get("imports", [])
        functions = f.get("functions", [])
        if isinstance(functions, list) and functions and isinstance(functions[0], dict):
            fn_count = len(functions)
        else:
            fn_count = f.get("ast_metrics", {}).get("functions", 0) if f.get("ast_metrics") else 0

        nesting = 0
        if f.get("ast_metrics"):
            nesting = f["ast_metrics"].get("max_nesting", 0)

        radar = [
            min(10, loc / 100),
            min(10, fn_count / 5),
            min(10, nesting),
            min(10, len(imports) / 3),
            min(10, h["score"] * 1.5),
        ]
        c = colors[idx % len(colors)]
        datasets.append({
            "label": os.path.basename(h["path"]),
            "data": radar,
            "backgroundColor": c["bg"],
            "borderColor": c["border"],
        })

    return {"datasets": datasets}


@app.route("/api/analyze", methods=["POST"])
def analyze():
    import pathlib
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Missing request body."}), 400

    url = body.get("url", "").strip()
    local_path = body.get("path", "").strip()
    depth = int(body.get("depth", 1))

    if not url and not local_path:
        return jsonify({"error": "Provide either a GitHub 'url' or a local 'path'."}), 400

    if local_path:
        # ── Local path analysis ──────────────────────────────────────────
        p = pathlib.Path(local_path)
        if not p.exists():
            return jsonify({"error": f"Path does not exist: {local_path}"}), 400
        if not p.is_dir():
            return jsonify({"error": f"Path is not a directory: {local_path}"}), 400
        target_path = str(p.resolve())
    else:
        # ── Remote GitHub analysis ───────────────────────────────────────
        if not (url.startswith("http://") or url.startswith("https://")):
            return jsonify({"error": "Only remote GitHub URLs are supported via this endpoint."}), 400
        try:
            target_path = clone_repo(url, depth)
        except Exception as e:
            return jsonify({"error": f"Failed to clone repository: {str(e)}"}), 500

    try:
        stats = analyze_directory(target_path)
        stats["session_path"] = target_path
        stats["trend"] = analyze_git_history(target_path)
        hotspots = detect_hotspots(stats["all_files"])
        payload = build_export_payload(stats, hotspots)
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/api/file", methods=["GET"])
def get_file():
    session_path = request.args.get("session_path", "")
    file_path = request.args.get("path", "")
    
    if not session_path or not file_path:
        return jsonify({"error": "Missing session_path or path."}), 400
        
    if ".." in file_path:
        return jsonify({"error": "Invalid path."}), 400
        
    full_path = os.path.join(session_path, file_path)
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found."}), 404
        
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        _, ext = os.path.splitext(file_path)
        lang = LANG_MAP.get(ext.lower(), "Other")
        
        suggestions = get_file_suggestions(full_path, content, lang)
        
        return jsonify({
            "content": content,
            "suggestions": suggestions
        })
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("🚀 Codebase Visualizer API Server starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

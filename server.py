import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

from analyzer.git_utils import clone_repo
from analyzer.core import analyze_directory
from analyzer.hotspots import detect_hotspots
from analyzer.git_history import analyze_git_history

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
        },
        "diagrams": diagrams,
        "hotspot_radar": hotspot_radar,
    }


def build_diagrams(all_files):
    """Generate Mermaid diagram strings in memory (no file write)."""

    # --- 1. Module Dependency Graph ---
    dep_lines = ["graph TD"]
    node_map = {f["path"]: f"F{i}" for i, f in enumerate(all_files)}
    added_edges = set()

    for f in all_files:
        fid = node_map[f["path"]]
        name = os.path.basename(f["path"]).replace('"', "'")
        dep_lines.append(f'    {fid}["{name}"]')

    for f in all_files:
        fid = node_map[f["path"]]
        for imp in f.get("imports", [])[:8]:
            for path, nid in node_map.items():
                if isinstance(imp, str) and imp in path and nid != fid:
                    edge = (fid, nid)
                    if edge not in added_edges:
                        added_edges.add(edge)
                        dep_lines.append(f"    {fid} --> {nid}")
                    break

    # --- 2. Class / Interface Diagram ---
    class_lines = ["classDiagram"]
    seen_classes = set()
    for f in all_files:
        if "ast_metrics" in f and f["ast_metrics"] and "structure" in f["ast_metrics"]:
            struct = f["ast_metrics"]["structure"]
            for cls in struct.get("classes", []):
                cname = cls["name"].replace(" ", "_")
                if cname in seen_classes:
                    continue
                seen_classes.add(cname)
                class_lines.append(f"    class {cname} {{")
                for m in cls.get("methods", [])[:8]:
                    mname = m["name"].replace(" ", "_")
                    class_lines.append(f"        +{mname}()")
                class_lines.append("    }")
                for base in cls.get("bases", []):
                    bname = base.replace(" ", "_")
                    class_lines.append(f"    {bname} <|-- {cname}")

        if "ts_metrics" in f and f["ts_metrics"]:
            struct = f["ts_metrics"]
            for cls in struct.get("classes", []):
                cname = cls["name"].replace(" ", "_")
                if cname in seen_classes:
                    continue
                seen_classes.add(cname)
                class_lines.append(f"    class {cname} {{")
                class_lines.append("    }")
                for base in cls.get("bases", []):
                    bname = base.replace(" ", "_")
                    class_lines.append(f"    {bname} <|-- {cname}")
            for intf in struct.get("interfaces", []):
                iname = intf["name"].replace(" ", "_")
                if iname in seen_classes:
                    continue
                seen_classes.add(iname)
                class_lines.append(f"    class {iname} {{")
                class_lines.append("        <<interface>>")
                class_lines.append("    }")

    if len(class_lines) == 1:
        class_lines.append("    %% No classes or interfaces detected")

    # --- 3. Function Call Graph ---
    call_lines = ["graph TD"]
    call_edges = set()
    for f in all_files:
        if "ast_metrics" in f and f["ast_metrics"] and "structure" in f["ast_metrics"]:
            struct = f["ast_metrics"]["structure"]
            for fn in struct.get("functions", []):
                fname = fn["name"]
                for call in fn.get("calls", [])[:6]:
                    edge = (fname, call)
                    if edge not in call_edges:
                        call_edges.add(edge)
                        call_lines.append(f"    {fname} --> {call}")

        if "ts_metrics" in f and f["ts_metrics"]:
            struct = f["ts_metrics"]
            for fn in struct.get("functions", []):
                fname = fn["name"]
                for call in fn.get("calls", [])[:6]:
                    edge = (fname, call)
                    if edge not in call_edges:
                        call_edges.add(edge)
                        call_lines.append(f"    {fname} --> {call}")

    if len(call_lines) == 1:
        call_lines.append("    %% No internal call data detected")

    # --- 4. React Render Tree ---
    render_lines = ["graph TD"]
    render_edges = set()
    for f in all_files:
        if "ts_metrics" in f and f["ts_metrics"]:
            struct = f["ts_metrics"]
            for fn in struct.get("functions", []):
                for render in fn.get("renders", []):
                    edge = (fn["name"], render)
                    if edge not in render_edges:
                        render_edges.add(edge)
                        render_lines.append(f'    {fn["name"]} --> {render}')

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
    body = request.get_json(silent=True)
    if not body or "url" not in body:
        return jsonify({"error": "Missing 'url' in request body."}), 400

    url = body["url"].strip()
    depth = int(body.get("depth", 1))

    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"error": "Only remote GitHub URLs are supported via this endpoint."}), 400

    try:
        target_path = clone_repo(url, depth)
    except Exception as e:
        return jsonify({"error": f"Failed to clone repository: {str(e)}"}), 500

    try:
        stats = analyze_directory(target_path)
        stats["trend"] = analyze_git_history(target_path)
        hotspots = detect_hotspots(stats["all_files"])
        payload = build_export_payload(stats, hotspots)
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("🚀 Codebase Visualizer API Server starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

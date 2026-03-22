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

    return {
        "files": file_data,
        "stats": {
            "total_files": stats.get("total_files", 0),
            "total_loc": stats.get("total_loc", 0),
            "languages": languages_summary,
            "hotspots_count": len(hotspots),
            "duplicates_count": len(stats.get("duplicates", [])),
        }
    }


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

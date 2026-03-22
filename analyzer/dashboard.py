import os
import webbrowser
import tempfile
import json

def generate_dashboard(stats, hotspots):
    all_files = stats["all_files"]
    
    # We need to serialize all files safely for the JS context.
    hotspot_map = {h["path"]: h for h in hotspots}
    
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
        
    files_json = json.dumps(file_data)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Codebase Interactive Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{
                --bg: #1e1e1e;
                --panel: #2d2d2d;
                --text: #e0e0e0;
                --border: #444;
                --high: #ff4d4d;
                --medium: #ff9933;
                --low: #4CAF50;
                --dim: #888;
                --dup: #ffd700;
                --primary: #4dc9f6;
            }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; display: flex; height: 100vh; overflow: hidden; }}
            
            #sidebar {{ width: 380px; background: var(--panel); border-right: 1px solid var(--border); overflow-y: auto; padding: 1rem; flex-shrink: 0; }}
            #sidebar h2 {{ color: var(--primary); font-size: 1.4rem; margin-top: 5px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
            ul.tree {{ list-style-type: none; padding-left: 15px; margin: 0; }}
            ul.tree li {{ margin: 4px 0; cursor: pointer; user-select: none; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            ul.tree li:hover {{ opacity: 0.8; text-shadow: 0px 0px 5px rgba(255,255,255,0.3); }}
            .folder {{ font-weight: bold; color: #a0c4ff; }}
            .file {{ padding-left: 5px; }}
            
            .badge-high {{ color: var(--high); font-weight: bold; }}
            .badge-medium {{ color: var(--medium); font-weight: bold; }}
            .badge-low {{ color: var(--low); }}
            .badge-dup {{ color: var(--dup); }}
            .badge-gen {{ color: var(--dim); }}
            
            #main {{ flex-grow: 1; padding: 2rem; overflow-y: auto; display: flex; flex-direction: column; background: radial-gradient(circle at top right, #252528, var(--bg)); }}
            #header {{ margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }}
            #header h1 {{ margin: 0 0 10px 0; font-size: 1.8rem; color: #fff; }}
            .metric-cards {{ display: flex; gap: 15px; margin-top: 15px; }}
            .card {{ background: rgba(0,0,0,0.2); padding: 15px 20px; border-radius: 8px; flex: 1; border: 1px solid var(--border); text-align: center; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3); }}
            .card-title {{ font-size: 0.85rem; color: var(--dim); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
            .card-value {{ font-size: 1.5rem; font-weight: bold; }}
            
            #content-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; flex-grow: 1; }}
            .chart-container {{ background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 8px; border: 1px solid var(--border); min-height: 400px; display: flex; justify-content: center; align-items: center; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3); }}
            
            .details-panel {{ background: rgba(0,0,0,0.2); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); overflow-y: auto; max-height: 600px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3); }}
            .details-panel h3 {{ margin-top: 0; color: var(--primary); font-size: 1.2rem; margin-bottom: 1.5rem; border-bottom: 1px solid #444; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; background: rgba(255,255,255,0.02); border-radius: 4px; overflow: hidden; }}
            th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
            th {{ color: #a0c4ff; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; background: rgba(0,0,0,0.4); }}
            tr:hover td {{ background: rgba(255,255,255,0.05); }}
            
            #placeholder {{ height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--dim); font-size: 1.3rem; }}
            .hint-icon {{ font-size: 4rem; opacity: 0.2; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div id="sidebar">
            <h2>📦 Structural File Tree</h2>
            <div id="tree-root"></div>
        </div>
        
        <div id="main">
            <div id="placeholder">
                <div class="hint-icon">👈🔘</div>
                <p>Click any file on the heatmap tree to dynamically generate its Risk Dashboard</p>
                <p style="font-size: 0.9rem; margin-top: 10px;">Color Legend: <span style="color:var(--low)">🟢 Safe</span> | <span style="color:var(--medium)">⚡ Scaled</span> | <span style="color:var(--high)">🔥 Hotspot/Risky</span></p>
            </div>
            
            <div id="dashboard-content" style="display: none;">
                <div id="header">
                    <h1 id="file-title">filename.js</h1>
                    <div class="metric-cards">
                        <div class="card">
                            <div class="card-title">Risk Level</div>
                            <div class="card-value" id="val-risk">-</div>
                        </div>
                        <div class="card">
                            <div class="card-title">LOC</div>
                            <div class="card-value" id="val-loc">-</div>
                        </div>
                        <div class="card">
                            <div class="card-title">Language</div>
                            <div class="card-value" id="val-lang">-</div>
                        </div>
                        <div class="card">
                            <div class="card-title">Functions</div>
                            <div class="card-value" id="val-func">-</div>
                        </div>
                    </div>
                </div>
                
                <div id="content-grid">
                    <div class="chart-container">
                        <canvas id="radarChart"></canvas>
                    </div>
                    
                    <div class="details-panel">
                        <h3>Detailed Module Anatomy</h3>
                        
                        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <h4 style="margin:0; color:#fff;">Classes & Components</h4>
                        </div>
                        <table id="table-classes"><tbody></tbody></table>
                        
                        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <h4 style="margin:0; color:#fff;">Methods & Functions</h4>
                        </div>
                        <table id="table-functions"><tbody></tbody></table>
                        
                        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 style="margin:0; color:#fff;">Imports / Dependencies</h4>
                        </div>
                        <ul id="list-imports" style="font-size: 0.9rem; color: #a0c4ff; padding-left: 20px; line-height: 1.6;"></ul>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const fileData = {files_json};
            let radarInstance = null;
            
            const tree = {{}};
            fileData.forEach(f => {{
                const parts = f.path.replace(/\\\\/g, "/").split("/");
                let current = tree;
                for (let i = 0; i < parts.length; i++) {{
                    const part = parts[i];
                    if (!current[part]) {{
                        current[part] = i === parts.length - 1 ? f : {{}};
                    }}
                    current = current[part];
                }}
            }});
            
            function buildTreeHTML(node, container) {{
                const ul = document.createElement("ul");
                ul.className = "tree";
                
                const keys = Object.keys(node).sort((a, b) => {{
                    const isFileA = node[a].loc !== undefined;
                    const isFileB = node[b].loc !== undefined;
                    if (isFileA !== isFileB) return isFileA ? 1 : -1;
                    return a.localeCompare(b);
                }});
                
                keys.forEach(key => {{
                    const child = node[key];
                    const li = document.createElement("li");
                    
                    if (child.loc !== undefined) {{
                        let icon = "🟢";
                        let styleClass = "badge-low";
                        
                        if (child.is_dup) {{ icon = "⚠"; styleClass = "badge-dup"; }}
                        else if (child.is_gen) {{ icon = "⚙"; styleClass = "badge-gen"; }}
                        else if (child.risk === "High") {{ icon = "🔥"; styleClass = "badge-high"; }}
                        else if (child.risk === "Medium") {{ icon = "⚡"; styleClass = "badge-medium"; }}
                        
                        li.innerHTML = `<span class="file ${{styleClass}}">${{icon}} ${{key}}</span>`;
                        li.onclick = (e) => {{
                            e.stopPropagation();
                            loadDashboard(child);
                            
                            // Highlight selection
                            document.querySelectorAll(".tree li").forEach(el => el.style.backgroundColor = "transparent");
                            li.style.backgroundColor = "rgba(255,255,255,0.1)";
                            li.style.borderRadius = "4px";
                        }};
                    }} else {{
                        const folderSpan = document.createElement("span");
                        folderSpan.className = "folder";
                        folderSpan.innerHTML = `📁 ${{key}}/`;
                        li.appendChild(folderSpan);
                        
                        const subTree = document.createElement("div");
                        subTree.style.display = "block";
                        buildTreeHTML(child, subTree);
                        li.appendChild(subTree);
                        
                        folderSpan.onclick = (e) => {{
                            e.stopPropagation();
                            subTree.style.display = subTree.style.display === "none" ? "block" : "none";
                            folderSpan.innerHTML = subTree.style.display === "none" ? `📁 ${{key}}` : `📂 ${{key}}/`;
                        }};
                    }}
                    ul.appendChild(li);
                }});
                container.appendChild(ul);
            }}
            
            buildTreeHTML(tree, document.getElementById("tree-root"));
            
            function loadDashboard(file) {{
                document.getElementById("placeholder").style.display = "none";
                document.getElementById("dashboard-content").style.display = "block";
                
                document.getElementById("file-title").innerText = file.path;
                document.getElementById("val-loc").innerText = file.loc;
                document.getElementById("val-lang").innerText = file.lang;
                document.getElementById("val-func").innerText = file.functions.length;
                
                const riskVal = document.getElementById("val-risk");
                riskVal.innerText = file.is_dup ? "Duplicate" : file.is_gen ? "Generated" : file.risk;
                riskVal.style.color = file.risk === "High" ? "var(--high)" : file.risk === "Medium" ? "var(--medium)" : file.is_dup ? "var(--dup)" : "var(--low)";
                
                const cTbody = document.querySelector("#table-classes tbody");
                cTbody.innerHTML = `<tr><th>Name</th><th>Methods Count</th></tr>` + 
                    file.classes.map(c => `<tr><td>${{c.name}}</td><td>${{c.methods}}</td></tr>`).join("");
                if (file.classes.length === 0) cTbody.innerHTML = "<tr><td colspan='2' style='color:var(--dim)'>No classes instantiated</td></tr>";
                    
                const fTbody = document.querySelector("#table-functions tbody");
                fTbody.innerHTML = `<tr><th>Name</th><th>Lines of Code</th></tr>` + 
                    file.functions.map(fn => `<tr><td>${{fn.name}}</td><td>${{fn.loc}}</td></tr>`).join("");
                if (file.functions.length === 0) fTbody.innerHTML = "<tr><td colspan='2' style='color:var(--dim)'>No functions mapped</td></tr>";
                    
                const iList = document.getElementById("list-imports");
                iList.innerHTML = file.imports.map(i => `<li>${{i}}</li>`).join("");
                if(file.imports.length === 0) iList.innerHTML = "<li style='color:var(--dim)'>No recorded dependencies</li>";
                
                updateChart(file.radar);
            }}
            
            function updateChart(dataArray) {{
                const ctx = document.getElementById('radarChart').getContext('2d');
                Chart.defaults.color = "#e0e0e0";
                
                if (radarInstance) radarInstance.destroy();
                
                radarInstance = new Chart(ctx, {{
                    type: 'radar',
                    data: {{
                        labels: ["LOC Scale", "Functions", "Nesting Depth", "Dependencies", "Overall Risk Score"],
                        datasets: [{{
                            label: "Module Complexity Profile",
                            data: dataArray,
                            fill: true,
                            backgroundColor: "rgba(255, 77, 77, 0.4)",
                            borderColor: "rgb(255, 77, 77)",
                            pointBackgroundColor: "rgb(255, 77, 77)",
                            pointBorderColor: "#fff",
                            pointHoverBackgroundColor: "#fff",
                            pointHoverBorderColor: "rgb(255, 77, 77)"
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            r: {{
                                angleLines: {{ color: 'rgba(255, 255, 255, 0.15)' }},
                                grid: {{ color: 'rgba(255, 255, 255, 0.15)' }},
                                pointLabels: {{ color: '#fff', font: {{ size: 14, weight: 'bold' }} }},
                                ticks: {{ display: false, min: 0, max: 10 }}
                            }}
                        }},
                        plugins: {{
                            legend: {{ display: false }}
                        }}
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    """
    
    fd, path = tempfile.mkstemp(suffix=".html", prefix="codebase_dashboard_")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    webbrowser.open(f"file://{path}")
    return path

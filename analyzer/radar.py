import os
import webbrowser
import tempfile
import json

def generate_radar_chart(hotspots):
    # Take top 5 highest risk hotspots
    top_files = sorted(hotspots, key=lambda x: x["score"], reverse=True)[:5]
    if not top_files:
        return None
        
    labels = ["LOC Scale", "Functions", "Nesting Depth", "Dependencies", "Overall Risk"]
    
    datasets = []
    colors = [
        "rgba(255, 99, 132, 0.5)",
        "rgba(54, 162, 235, 0.5)",
        "rgba(255, 206, 86, 0.5)",
        "rgba(75, 192, 192, 0.5)",
        "rgba(153, 102, 255, 0.5)"
    ]
    border_colors = [
        "rgb(255, 99, 132)",
        "rgb(54, 162, 235)",
        "rgb(255, 206, 86)",
        "rgb(75, 192, 192)",
        "rgb(153, 102, 255)"
    ]
    
    for idx, f in enumerate(top_files):
        # Normalize Data (roughly mapping to 0-10 scale for the radar to look balanced)
        loc_val = min(10, f["loc"] / 100)
        functions_val = min(10, f.get("functions", 0) / 5)
        
        nesting_val = 0
        deps_val = 0
        
        # Pull directly from properties if available
        if "ast_metrics" in f and f["ast_metrics"]:
            nesting_val = min(10, f["ast_metrics"].get("max_nesting", 0))
            
        deps_val = min(10, len(f.get("imports", [])) / 3) 
        score_val = min(10, f["score"] * 1.5)
        
        # Fallbacks for non python files without nesting data
        if nesting_val == 0 and score_val > 0:
            nesting_val = min(10, score_val / 2) # Just a filler to form a polygon
            
        datasets.append({
            "label": f["path"],
            "data": [loc_val, functions_val, nesting_val, deps_val, score_val],
            "fill": True,
            "backgroundColor": colors[idx % len(colors)],
            "borderColor": border_colors[idx % len(border_colors)],
            "pointBackgroundColor": border_colors[idx % len(border_colors)],
            "pointBorderColor": "#fff",
            "pointHoverBackgroundColor": "#fff",
            "pointHoverBorderColor": border_colors[idx % len(border_colors)]
        })
        
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Codebase Complexity Radar</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: sans-serif; background-color: #1e1e1e; color: #fff; text-align: center; padding: 2rem; }}
            .chart-wrapper {{ width: 800px; height: 800px; margin: 0 auto; background: #2d2d2d; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
            h1 {{ color: #4dc9f6; margin-bottom: 0.5rem; }}
            p {{ padding-bottom: 2rem; color: #ccc; }}
        </style>
    </head>
    <body>
        <h1>🔥 Codebase Complexity Radar</h1>
        <p>Visualizing the overlapping risk profiles of the Top 5 most complex modules.</p>
        <div class="chart-wrapper">
            <canvas id="radarChart"></canvas>
        </div>

        <script>
            const ctx = document.getElementById('radarChart').getContext('2d');
            
            Chart.defaults.color = "#ccc";
            Chart.defaults.font.size = 14;

            new Chart(ctx, {{
                type: 'radar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: {json.dumps(datasets)}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        r: {{
                            angleLines: {{ color: 'rgba(255, 255, 255, 0.2)' }},
                            grid: {{ color: 'rgba(255, 255, 255, 0.2)' }},
                            pointLabels: {{ color: '#fff', font: {{ size: 16 }} }},
                            ticks: {{ display: false, min: 0, max: 10 }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ color: '#fff', padding: 20 }} }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Save to a temporary file
    fd, path = tempfile.mkstemp(suffix=".html", prefix="codebase_radar_")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    # Open in browser
    webbrowser.open(f"file://{path}")
    return path

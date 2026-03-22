import subprocess
import os
from collections import defaultdict

def analyze_git_history(target_path):
    # Check if git exists
    git_dir = os.path.join(target_path, ".git")
    if not os.path.exists(git_dir):
        return None
        
    try:
        # Get log for the last 12 months
        result = subprocess.run(
            ["git", "log", "--since=12 months ago", "--shortstat", "--date=short", "--format=%ad"],
            cwd=target_path,
            capture_output=True,
            text=True,
            check=True
        )
    except Exception:
        return None
        
    lines = result.stdout.strip().split('\n')
    
    monthly_net = defaultdict(int)
    current_month = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line[0].isdigit() and len(line) >= 7:
            # It's a date: YYYY-MM-DD
            current_month = line[:7] # YYYY-MM
        elif "changed" in line:
            if current_month:
                # Parse insertions and deletions
                # e.g. "3 files changed, 100 insertions(+), 50 deletions(-)"
                insertions = 0
                deletions = 0
                
                parts = line.split(',')
                for p in parts:
                    if "insertion" in p:
                        try:
                            insertions = int(p.strip().split(' ')[0])
                        except ValueError:
                            pass
                    elif "deletion" in p:
                        try:
                            deletions = int(p.strip().split(' ')[0])
                        except ValueError:
                            pass
                        
                monthly_net[current_month] += (insertions - deletions)
                
    if not monthly_net:
        return None
        
    # Build timeline
    months = sorted(monthly_net.keys())
    trend = []
    cumulative = 0
    for m in months:
        cumulative += monthly_net[m]
        trend.append({"month": m, "net": monthly_net[m], "cumulative": cumulative})
        
    return trend

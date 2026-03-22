import argparse
import sys
import os
from rich.console import Console
from analyzer.core import analyze_directory
from analyzer.git_utils import clone_repo
from analyzer.hotspots import detect_hotspots
from analyzer.output import print_summary
from analyzer.git_history import analyze_git_history

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Analyze a codebase and output complexity metrics, languages, and dependencies.")
    parser.add_argument("path", help="Local directory path or GitHub URL to analyze")
    parser.add_argument("--depth", type=int, default=1, help="Depth for GitHub shallow clone (default 1)")
    parser.add_argument("--dashboard", action="store_true", help="Generate and launch an interactive HTML Risk Dashboard in your browser")
    parser.add_argument("--frontend", action="store_true", help="Export data to React frontend and launch it")
    parser.add_argument("--minimap", action="store_true", help="Print a detailed File-to-Function Mini-Map for top risky files")
    parser.add_argument("--diagram", action="store_true", help="Generate a Mermaid architecture diagram file")
    
    args = parser.parse_args()
    
    console.print(f"[bold cyan]Analyzing:[/bold cyan] {args.path}")
    
    target_path = args.path
    is_temp = False
    
    if args.path.startswith("http://") or args.path.startswith("https://"):
        try:
            target_path = clone_repo(args.path, args.depth)
            is_temp = True
        except Exception as e:
            console.print(f"[bold red]Error cloning repo:[/bold red] {e}")
            return 1
    elif not os.path.exists(target_path):
        console.print(f"[bold red]Error:[/bold red] Path does not exist: {target_path}")
        return 1
        
    with console.status("[bold green]Crunching numbers...[/bold green]"):
        stats = analyze_directory(target_path)
        stats["trend"] = analyze_git_history(target_path)
        hotspots = detect_hotspots(stats["all_files"])
        
    print_summary(stats, hotspots)
    
    if args.dashboard:
        from analyzer.dashboard import generate_dashboard
        with console.status("[bold green]Generating Interactive Risk Dashboard...[/bold green]"):
            path = generate_dashboard(stats, hotspots)
            console.print(f"\n🚀 [bold magenta]Risk Dashboard launched in browser![/bold magenta] [dim]({path})[/dim]")
                
    if args.minimap:
        from analyzer.output import print_minimap
        print_minimap(stats["all_files"])
        
    if args.diagram:
        from analyzer.mermaid_generator import generate_mermaid_diagrams
        with console.status("[bold green]Generating Mermaid Architecture Diagrams...[/bold green]"):
            path = generate_mermaid_diagrams(stats)
            console.print(f"\n✨ [bold cyan]Architecture diagrams saved successfully to {path}![/bold cyan]")
            
    if args.frontend:
        from analyzer.export import export_frontend_data
        import subprocess
        import webbrowser
        import time
        with console.status("[bold green]Exporting data for React Frontend...[/bold green]"):
            out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "public")
            out_path = export_frontend_data(stats, hotspots, output_dir=out_dir)
            console.print(f"\n✨ [bold cyan]Data exported to {out_path}![/bold cyan]")
            console.print("[bold yellow]Starting React dev server (this may take a moment)...[/bold yellow]")
            subprocess.Popen(["npm", "run", "dev"], cwd=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"), shell=True)
            time.sleep(3)
            webbrowser.open("http://localhost:5173")
            
    return 0

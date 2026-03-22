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
    parser.add_argument("--radar", action="store_true", help="Generate and open an interactive HTML Radar Chart of file complexity")
    
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
    
    if args.radar:
        from analyzer.radar import generate_radar_chart
        with console.status("[bold green]Generating Interactive Radar Chart...[/bold green]"):
            path = generate_radar_chart(hotspots)
            if path:
                console.print(f"\n🚀 [bold magenta]Complexity Radar Chart launched in browser![/bold magenta] [dim]({path})[/dim]")
            else:
                console.print("\n[yellow]Not enough data to generate radar chart![/yellow]")
    
    return 0

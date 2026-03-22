from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text

console = Console()

def print_summary(stats, hotspots):
    print_basic_stats(stats)
    if stats.get("trend"):
        print_loc_trend(stats["trend"])
    print_tree(stats["all_files"])
    print_language_stats(stats["lang_stats"])
    print_top_files(stats["top_files"])
    print_dependency_graph(stats["all_files"])
    print_duplicates(stats.get("duplicates", []))
    print_priority_fixes(hotspots)
    print_hotspots(hotspots)
    
def print_basic_stats(stats):
    console.print("\n")
    summary_text = (
        f"[bold green]Total Files:[/bold green] {stats['total_files']} | "
        f"[bold green]App LOC:[/bold green] {stats['total_loc']} | "
        f"[dim]Generated/Vendor LOC: {stats.get('generated_loc', 0)}[/dim]"
    )
    console.print(Panel(summary_text, title="Codebase Summary"))

def print_loc_trend(trend_data):
    if not trend_data:
        return
        
    console.print(Panel(
        "Net LOC additions vs deletions aggregated per month.",
        title="[magenta]Codebase LOC Growth Timeline[/magenta]",
        subtitle="12-Month Git History Analysis"
    ))
    
    max_cum = max((t["cumulative"] for t in trend_data), default=0)
    min_cum = min((t["cumulative"] for t in trend_data), default=0)
    baseline = 0 if min_cum >= 0 else min_cum
    range_val = (max_cum - baseline) if (max_cum - baseline) > 0 else 1
    
    table = Table(box=None, show_header=False)
    table.add_column("Month", style="cyan")
    table.add_column("Bar")
    table.add_column("Net", justify="right")
    
    for t in trend_data:
        val = t["cumulative"] - baseline
        length = int((val / range_val) * 40)
        bar = "█" * length
        bar_str = f"[blue]{bar}[/blue]"
        
        net_str = f"+{t['net']}" if t['net'] >= 0 else str(t['net'])
        net_color = "green" if t['net'] >= 0 else "red"
        
        table.add_row(t["month"], bar_str, f"[{net_color}]{net_str}[/{net_color}] LOC")
        
    console.print(table)
    console.print("")

def print_language_stats(lang_stats):
    table = Table(title="Language Distribution")
    table.add_column("Language", style="cyan")
    table.add_column("Files", justify="right", style="magenta")
    table.add_column("LOC", justify="right", style="green")
    
    # Sort by LOC
    sorted_langs = sorted(lang_stats.items(), key=lambda x: x[1]['loc'], reverse=True)
    
    for lang, metrics in sorted_langs:
        table.add_row(lang, str(metrics['files']), str(metrics['loc']))
        
    console.print(table)
    
def print_tree(all_files):
    """Renders a color-coded hierarchical directory tree."""
    # Build a set of duplicate paths for fast lookup
    dup_paths = set()
    # We need the duplicates list; reconstruct from all_files if needed
    # (It's already embedded as a flag inside file dicts if added)
    # We'll rely on duplicate_of key injected into files during traversal. 
    # For now, detect by checking if file was seen twice - we'll use a simpler approach:
    # build from stats duplicates list instead, which is passed via all_files side-channel
    # Actually we only have all_files here. Let's mark duplicate paths via a separate set.
    # We embed is_duplicate on the file dict in core.py, handled below.
    
    # Build nested dict representing the tree structure
    tree_data = {}
    for f in all_files:
        parts = f["path"].replace("\\", "/").split("/")
        node = tree_data
        for part in parts:
            node = node.setdefault(part, {})
        node["__file__"] = f

    def _get_label(name, file_info=None):
        if file_info is None:
            # Directory
            return Text(f"📁 {name}/", style="bold blue")
        
        loc = file_info.get("loc", 0)
        is_generated = file_info.get("is_generated", False)
        is_duplicate = file_info.get("is_duplicate", False)
        risk_level = file_info.get("risk_level", "Low")
        
        badge = f" [{loc} LOC]"
        
        if is_duplicate:
            style = "bright_yellow"
            icon = "⚠ "
        elif is_generated:
            style = "dim"
            icon = "⚙ "
        elif risk_level == "High":
            style = "bold red"
            icon = "🔥 "
        elif risk_level == "Medium":
            style = "orange1"
            icon = "⚡ "
        else:
            style = "green"
            icon = "🟢 "
        
        return Text(f"{icon}{name}{badge}", style=style)

    def _build_rich_tree(node, rich_node):
        for key, value in sorted(node.items()):
            if key == "__file__":
                continue
            file_info = value.get("__file__")
            if file_info is not None and len(value) == 1:
                # It's a leaf file
                rich_node.add(_get_label(key, file_info))
            else:
                # It's a directory
                branch = rich_node.add(_get_label(key))
                _build_rich_tree(value, branch)
    
    root = Tree(Text("📦 Project Root", style="bold white"))
    _build_rich_tree(tree_data, root)
    
    console.print("")
    console.print(Panel(
        "[green]🟢 Normal[/green]  [orange1]⚡ Medium Risk[/orange1]  [red]🔥 High Risk[/red]  [bright_yellow]⚠  Duplicate[/bright_yellow]  [dim]⚙  Generated[/dim]",
        title="Hotspot Heatmap",
        subtitle="Risk Intensity"
    ))
    console.print(root)
    console.print("")

def print_top_files(top_files):
    table = Table(title="Top 5 Largest Files")
    table.add_column("File", style="cyan")
    table.add_column("LOC", justify="right", style="green")
    table.add_column("Language", style="magenta")
    
    for f in top_files:
        table.add_row(f['path'], str(f['loc']), f['lang'])
        
    console.print(table)
    
def print_python_stats(all_files):
    # Filter Python files to list their functions, classes and dependencies
    py_files = [f for f in all_files if f.get("lang") == "Python" and f.get("ast_metrics")]
    if not py_files:
        return
        
    table = Table(title="Python Files Breakdown")
    table.add_column("File", style="cyan")
    table.add_column("Classes", justify="right", style="blue")
    table.add_column("Functions", justify="right", style="blue")
    table.add_column("Dependencies", style="yellow")
    
    for f in sorted(py_files, key=lambda x: x['loc'], reverse=True)[:10]: # Top 10 Python files to not spam output
        ast = f["ast_metrics"]
        deps = ", ".join(ast["imports"]) if ast["imports"] else "-"
        # limit deps string size if it's too long
        if len(deps) > 40:
            deps = deps[:37] + "..."
        table.add_row(f['path'], str(ast['classes']), str(ast['functions']), deps)
        
    console.print(table)

def print_minimap(all_files):
    # Only print for top 10 files by risk_score so it doesn't flood terminal
    minimap_files = sorted(all_files, key=lambda x: x.get("score", 0), reverse=True)[:10]
    
    console.print(Panel(
        "Detailed functional tree mapping for the most complex modules.",
        title="[blue]File-to-Function Mini-Map[/blue]",
        subtitle="Top 10 High Risk Modules"
    ))
    
    for f in minimap_files:
        has_py = "ast_metrics" in f and f["ast_metrics"] and "structure" in f["ast_metrics"]
        has_ts = "ts_metrics" in f and f["ts_metrics"]
        
        if not has_py and not has_ts:
            continue
            
        risk = f.get('risk_level', 'Low')
        color = "red" if risk == "High" else "orange1" if risk == "Medium" else "green"
        tree = Tree(f"📄 [{color}]{f['path']}[/{color}] [dim]({f['loc']} LOC)[/dim]")
        
        if has_py:
            struct = f["ast_metrics"]["structure"]
            for c in struct["classes"]:
                c_tree = tree.add(f"🏗️  [bold yellow]class {c['name']}[/bold yellow]")
                for b in c.get("bases", []):
                    c_tree.add(f"  ↳ [dim]inherits {b}[/dim]")
                for m in c["methods"]:
                    c_tree.add(f"⚡ [green]def {m['name']}[/green] [dim]({m['loc']} LOC)[/dim]")
            for fn in struct["functions"]:
                tree.add(f"⚡ [green]def {fn['name']}[/green] [dim]({fn['loc']} LOC)[/dim]")
                
        if has_ts:
            struct = f["ts_metrics"]
            for c in struct["classes"]:
                c_tree = tree.add(f"🏗️  [bold yellow]class {c['name']}[/bold yellow]")
                for b in c.get("bases", []):
                    c_tree.add(f"  ↳ [dim]extends {b}[/dim]")
            for i in struct["interfaces"]:
                tree.add(f"🧩 [blue]interface {i['name']}[/blue]")
            for fn in struct["functions"]:
                tree.add(f"⚡ [green]func/const {fn['name']}[/green]")
                
        if len(tree.children) > 0:
            console.print(tree)
            console.print("")

def print_dependency_graph(all_files):
    # Filter files with >= 1 imports
    coupled_files = [f for f in all_files if len(f.get("imports", [])) > 0]
    coupled_files.sort(key=lambda x: len(x["imports"]), reverse=True)
    
    if not coupled_files:
        return
        
    console.print(Panel(
        "Directed graph showing heavily coupled modules and their imported dependencies.",
        title="[blue]Dependency Graph[/blue]",
        subtitle="Top Coupled Files"
    ))
    
    for f in coupled_files[:10]:
        tree = Tree(f"📄 [bold cyan]{f['path']}[/bold cyan] [dim]({f['lang']}) - {len(f['imports'])} imports[/dim]")
        for imp in sorted(f["imports"])[:15]:
            icon = "📦" if not imp.startswith('.') and not imp.startswith('/') else "🔗"
            tree.add(Text(f"{icon} {imp}", style="blue"))
        if len(f["imports"]) > 15:
            tree.add(Text(f"   ... and {len(f['imports']) - 15} more", style="dim"))
        console.print(tree)
    console.print("")

def print_duplicates(duplicates):
    if not duplicates:
        return
        
    from collections import defaultdict
    groups = defaultdict(list)
    for d in duplicates:
        groups[d["duplicate_of"]].append(d["path"])
        
    console.print(Panel(
        "Files with exactly identical code content detected via hashing.", 
        title="[yellow]Duplicate File Graph[/yellow]", 
        subtitle="Edges point to redundant copies"
    ))
    
    for original, dup_list in list(groups.items())[:15]: # Limit to 15 duplicate groups
        tree = Tree(f"📄 [bold cyan]{original}[/bold cyan] [dim](Original)[/dim]")
        for dup in dup_list:
            tree.add(f"🔗 [yellow]{dup}[/yellow] [dim](Duplicate)[/dim]")
        console.print(tree)
    console.print("")

def print_priority_fixes(hotspots):
    # Filter only High Risk items
    priority = [h for h in hotspots if h.get("risk_level") == "High"]
    if not priority:
        console.print("\n[bold green]No Priority Fixes needed![/bold green] 🎉\n")
        return
        
    table = Table(title="🚨 Priority Fixes (Actionable Insights)")
    table.add_column("File", style="cyan")
    table.add_column("Risk", style="red bold")
    table.add_column("Action Items", style="yellow")
    
    for p in priority[:5]:
        table.add_row(p['path'], p['risk_level'], "\n".join(p['reasons']))
        
    console.print(table)
    console.print("\n")

def print_hotspots(hotspots):
    # Show medium risk hotspots since high risk are handled by priority
    medium = [h for h in hotspots if h.get("risk_level", "Medium") == "Medium"]
    if not medium:
        return
        
    table = Table(title="🔥 Code Hotspots (Medium Risk)")
    table.add_column("File", style="cyan")
    table.add_column("Issues", style="red")
    table.add_column("LOC", justify="right", style="green")
    
    # Show top 5 medium hotspots max
    for h in medium[:5]:
        table.add_row(h['path'], "\n".join(h['reasons']), str(h['loc']))
        
    console.print(table)
    console.print("\n")

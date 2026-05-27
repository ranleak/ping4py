import os
import re
import sys
import argparse
import subprocess
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

def get_binary_path():
    """Locate the bundled ping binary inside the package structure."""
    base_dir = Path(__file__).parent
    binary_path = base_dir / "bin" / "ping"
    
    # Fallback to system ping if bundled binary isn't available/compatible
    if not binary_path.exists():
        return "ping"
        
    # Ensure it's executable in local environments
    if os.name != 'nt' and not os.access(binary_path, os.X_OK):
        os.chmod(binary_path, 0o755)
        
    return str(binary_path)

def generate_dashboard(target: str, pings_data: list, status_msg: str) -> Panel:
    """Renders a beautiful tracking table inside an encompassing layout box."""
    table = Table(title=f"Ping Targets Log: [bold cyan]{target}[/bold cyan]", expand=True)
    table.add_column("Seq", justify="right", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("TTL", justify="right", style="green")
    table.add_column("Latency (ms)", justify="right", style="bold yellow")

    # Only show the last 10 attempts to keep the terminal compact
    for row in pings_data[-10:]:
        table.add_row(
            str(row['seq']),
            "[bold green]SUCCESS[/bold green]" if row['success'] else "[bold red]FAILED[/bold red]",
            str(row['ttl']) if row['ttl'] else "-",
            f"{row['time']:.2f}" if row['time'] else "-"
        )

    # Calculate basic summary metrics
    latencies = [r['time'] for r in pings_data if r['success'] and r['time'] is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    loss_pct = ((len(pings_data) - len(latencies)) / len(pings_data) * 100) if pings_data else 0

    summary_text = Text.assemble(
        ("Status: ", "bold"), (f"{status_msg}\n", "italic blue"),
        ("Packets Sent: ", "bold"), (f"{len(pings_data)}   ", "cyan"),
        ("Loss Rate: ", "bold"), (f"{loss_pct:.1f}%   ", "red" if loss_pct > 0 else "green"),
        ("Avg Latency: ", "bold"), (f"{avg_latency:.2f} ms", "yellow")
    )

    return Panel(
        table,
        title="[bold reverse] Rich-Ping Live Dashboard [/bold reverse]",
        subtitle=summary_text,
        subtitle_align="left",
        padding=(1, 2)
    )

def main():
    parser = argparse.ArgumentParser(description="Interactive Rich Wrapper for Bundled Ping Binary")
    parser.add_argument("target", help="Host or IP address to ping")
    parser.add_argument("-c", "--count", type=int, default=20, help="Number of packets to send")
    args = parser.parse_args()

    binary = get_binary_path()
    
    # Standard format: 64 bytes from 8.8.8.8: icmp_seq=1 ttl=56 time=11.4 ms
    ping_regex = re.compile(r"bytes from .*?icmp_seq=(\d+)\s+ttl=(\d+)\s+time=([\d.]+)")

    # Execute the bundled binary as an unbuffered stream
    cmd = [binary, "-c", str(args.count), args.target]
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    except PermissionError:
        console.print("[bold red]Permission Error:[/bold red] The binary requires administrative privileges for raw network sockets.")
        console.print("[yellow]Tip: Run with 'sudo' or assign capabilities via: 'sudo setcap cap_net_raw+ep <path_to_binary>'[/yellow]")
        sys.exit(1)

    history = []
    status = "Transmitting echo requests..."

    # Create the Live context manager to swap out output frames seamlessly
    with Live(generate_dashboard(args.target, history, status), refresh_per_second=4, screen=False) as live:
        for line in iter(process.stdout.readline, ""):
            line = line.strip()
            if not line:
                continue
            
            # Look for active match profiles
            match = ping_regex.search(line)
            if match:
                seq, ttl, rtt = match.groups()
                history.append({
                    "seq": int(seq),
                    "success": True,
                    "ttl": int(ttl),
                    "time": float(rtt)
                })
            elif "Timeout" in line or "Failure" in line:
                history.append({
                    "seq": len(history) + 1,
                    "success": False,
                    "ttl": None,
                    "time": None
                })
            
            live.update(generate_dashboard(args.target, history, status))
        
        process.stdout.close()
        return_code = process.wait()
        status = f"Finished with return code {return_code}"
        live.update(generate_dashboard(args.target, history, status))

if __name__ == "__main__":
    main()
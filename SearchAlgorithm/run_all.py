"""Runner untuk mendemonstrasikan seluruh algoritma pencarian di SearchAlgorithm."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCRIPTS = [
    ("Linear Search", "linearsearch.py"),
    ("Binary Search", "binarysearch.py"),
    ("Breadth-First Search (BFS)", "bfsearch.py"),
    ("Depth-First Search (DFS)", "dfsearch.py"),
    ("Uniform Cost Search (UCS)", "ucsearch.py"),
    ("Iterative Deepening DFS (IDDFS)", "iddfsearch.py"),
    ("A* Search (A-Star)", "astarsearch.py"),
    ("Dijkstra's Algorithm", "dijkstrasearch.py"),
]

def main():
    print("=" * 60)
    print("      DEMONSTRASI SELURUH ALGORITMA PENCARIAN (PYTHON)")
    print("=" * 60)
    
    for title, script in SCRIPTS:
        print(f"\n[+] {title} ({script}):")
        script_path = HERE / script
        if script_path.exists():
            res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
            print(res.stdout.strip())
            if res.stderr:
                print(f"Error: {res.stderr.strip()}", file=sys.stderr)
        else:
            print(f"File {script} tidak ditemukan.")
    
    print("\n" + "=" * 60)
    print("  Semua demonstrasi algoritma pencarian selesai dijalankan!")
    print("=" * 60)

if __name__ == "__main__":
    main()

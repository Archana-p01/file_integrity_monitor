import hashlib
import os
import json
import datetime

# ─── CONFIG ───────────────────────────────────────────────
MONITOR_FOLDER = "/home/kali/fim_project"   # Path to be monitered
BASELINE_FILE  = "baseline.json"            # where hashes are saved
# ──────────────────────────────────────────────────────────


def hash_file(filepath):
    """Generate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (IOError, OSError) as e:
        print(f"  [ERROR] Could not read {filepath}: {e}")
        return None


def scan_folder(folder):
    """Walk folder and return dict of {filepath: hash}."""
    hashes = {}
    if not os.path.exists(folder):
        print(f"[ERROR] Folder not found: {folder}")
        return hashes
    for root, dirs, files in os.walk(folder):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_hash = hash_file(filepath)
            if file_hash:
                hashes[filepath] = file_hash
    return hashes


def create_baseline():
    """Scan folder and save hashes as baseline."""
    print(f"\n{'='*55}")
    print("  FILE INTEGRITY MONITOR — Creating Baseline")
    print(f"{'='*55}")
    print(f"  Scanning folder: {MONITOR_FOLDER}")

    hashes = scan_folder(MONITOR_FOLDER)

    if not hashes:
        print("  [WARNING] No files found to baseline.")
        return

    baseline = {
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "folder": MONITOR_FOLDER,
        "files": hashes
    }

    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=4)

    print(f"  [OK] Baseline created — {len(hashes)} files hashed")
    print(f"  [OK] Saved to: {BASELINE_FILE}")
    print(f"{'='*55}\n")


def check_integrity():
    """Compare current hashes against baseline and report changes."""
    print(f"\n{'='*55}")
    print("  FILE INTEGRITY MONITOR — Checking Integrity")
    print(f"{'='*55}")

    # Load baseline
    if not os.path.exists(BASELINE_FILE):
        print("  [ERROR] No baseline found. Run with --baseline first.")
        return

    with open(BASELINE_FILE, "r") as f:
        baseline = json.load(f)

    baseline_hashes = baseline["files"]
    baseline_time   = baseline.get("created_at", "unknown")

    print(f"  Baseline created : {baseline_time}")
    print(f"  Scanning folder  : {MONITOR_FOLDER}")
    print(f"  Files in baseline: {len(baseline_hashes)}")
    print()

    current_hashes = scan_folder(MONITOR_FOLDER)

    alerts = []

    # Check for modified or deleted files
    for filepath, old_hash in baseline_hashes.items():
        if filepath not in current_hashes:
            alerts.append(("DELETED", filepath, old_hash, None))
        elif current_hashes[filepath] != old_hash:
            alerts.append(("MODIFIED", filepath, old_hash, current_hashes[filepath]))

    # Check for new files
    for filepath in current_hashes:
        if filepath not in baseline_hashes:
            alerts.append(("ADDED", filepath, None, current_hashes[filepath]))

    # Print results
    if not alerts:
        print("  [PASS] No changes detected. All files intact.")
    else:
        print(f"  [ALERT] {len(alerts)} change(s) detected!\n")
        for change_type, filepath, old_hash, new_hash in alerts:
            if change_type == "MODIFIED":
                print(f"  [MODIFIED] {filepath}")
                print(f"             Old hash: {old_hash}")
                print(f"             New hash: {new_hash}")
            elif change_type == "DELETED":
                print(f"  [DELETED]  {filepath}")
                print(f"             Hash was: {old_hash}")
            elif change_type == "ADDED":
                print(f"  [ADDED]    {filepath}")
                print(f"             New hash: {new_hash}")
            print()

    print(f"  Scan completed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")


def create_test_files():
    """Create sample files to monitor (for demo purposes)."""
    os.makedirs(MONITOR_FOLDER, exist_ok=True)
    files = {
        "config.txt":   "server=192.168.1.1\nport=8080\n",
        "users.txt":    "admin\nalice\nbob\n",
        "settings.cfg": "[database]\nhost=localhost\nport=5432\n",
    }
    for filename, content in files.items():
        path = os.path.join(MONITOR_FOLDER, filename)
        with open(path, "w") as f:
            f.write(content)
    print(f"\n  [OK] Created {len(files)} test files in '{MONITOR_FOLDER}/'")


# ─── MAIN MENU ────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    print("\n  File Integrity Monitor")
    print("  ----------------------")

    if len(sys.argv) < 2:
        print("  Usage:")
        print("    python3 fim.py --setup      Create test files to monitor")
        print("    python3 fim.py --baseline   Scan and save baseline hashes")
        print("    python3 fim.py --check      Check for changes vs baseline")
        sys.exit(0)

    arg = sys.argv[1]

    if arg == "--setup":
        create_test_files()
    elif arg == "--baseline":
        create_baseline()
    elif arg == "--check":
        check_integrity()
    else:
        print(f"  [ERROR] Unknown argument: {arg}")
        print("  Use --setup, --baseline, or --check")

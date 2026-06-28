import subprocess
import os
import sys

def get_files_to_commit():
    status_res = subprocess.run(["git", "status", "--porcelain", "-uall"], capture_output=True, text=True)
    files = []
    for line in status_res.stdout.splitlines():
        if len(line) > 3:
            filepath = line[3:].strip().strip('"')
            files.append(filepath)
    return files

def run_git(args):
    print(f"Running: git {' '.join(args)}")
    res = subprocess.run(["git"] + args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr.strip()}")
    else:
        print(res.stdout.strip())
    return res

def main():
    files_to_commit = get_files_to_commit()
    print(f"Found {len(files_to_commit)} files to commit and push one by one.")
    
    for f in files_to_commit:
        if not os.path.exists(f):
            print(f"Skipping {f} (does not exist)")
            continue
            
        print(f"\n>>> Processing {f}...")
        
        # Git Add
        run_git(["add", f])
        
        # Git Commit
        filename = os.path.basename(f)
        commit_msg = f"Integrate and update {filename} for exoplanet platform"
        if "main.py" in f or "App.tsx" in f:
            commit_msg = f"Upgrade {filename} with real data search integration"
        elif "service" in f:
            commit_msg = f"Configure {filename} for real-time archive queries"
        elif "App.css" in f or "index.css" in f or "gallery" in f.lower() or "catalog" in f.lower():
            commit_msg = f"Enhance UI/UX and styling in {filename}"
        elif "package.json" in f or "package-lock.json" in f or "vite.config" in f or "tsconfig" in f:
            commit_msg = f"Configure frontend environment and dependencies in {filename}"
        elif ".pyc" in f:
            commit_msg = f"Update compiled bytecode {filename}"
            
        commit_res = run_git(["commit", "-m", commit_msg])
        if commit_res.returncode == 0:
            # Git Push
            print(f"Pushing commit for {f}...")
            push_res = run_git(["push", "origin", "main"])
            if push_res.returncode != 0:
                print("Failed to push. Stopping script to prevent issues.")
                sys.exit(1)
        else:
            print(f"Failed to commit {f}.")

if __name__ == "__main__":
    main()

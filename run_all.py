import subprocess
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# List of project folders
folders = [
     "gorhumour",
     "gorenter",
     "gornews",
     "gorpolitics",
     "gorrelation",
     "gorhotdeals",
     "gorannounce",
     "clienft",   
     "zdnetai"
     "goridol"
    # "nittertweet"
]

def clear_logs():
    for folder in folders:
        log_file = Path(folder) / "steps.log"
        if log_file.exists():
            log_file.unlink()
            print(f"Deleted {log_file}")

def run_script(folder):
    main_script = Path(folder) / "main.py"
    if main_script.exists():
        print(f"Running {main_script}")
        try:
            subprocess.run(["python", str(main_script)], check=True)
            return f"{folder}: Completed"
        except subprocess.CalledProcessError as e:
            return f"{folder}: Failed - {e}"
    else:
        return f"{folder}: main.py not found"

def run_all_main_scripts_concurrently():
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(run_script, folder): folder for folder in folders}
        for future in as_completed(futures):
            print(future.result())

def git_commit_and_push():
    print("Adding files to git...")
    subprocess.run(["git", "add", "."], check=True)
    print("Committing...")
    subprocess.run(["git", "commit", "-m", "Auto update"], check=True)
    print("Pushing to GitHub...")
    subprocess.run(["git", "push"], check=True)

if __name__ == "__main__":
    clear_logs()
    run_all_main_scripts_concurrently()
    git_commit_and_push()

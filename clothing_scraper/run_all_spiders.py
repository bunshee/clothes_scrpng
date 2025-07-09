import subprocess
import sys
import os

# Add the project root to the Python path to allow for absolute imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from api.spiders import SpiderName

def run_all_spiders():
    print("Starting execution of all spiders...")
    for spider in SpiderName:
        spider_name = spider.value
        print(f"\n--- Running spider: {spider_name} ---")
        command = ["python", "main.py", "scrape", "--spider", spider_name]
        try:
            # Run the command and capture output
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            print(process.stdout)
            if process.stderr:
                print(f"Error output for {spider_name}:\n{process.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Command failed for {spider_name} with exit code {e.returncode}:\n{e.stdout}\n{e.stderr}")
        except Exception as e:
            print(f"An unexpected error occurred while running {spider_name}: {e}")
    print("\nAll spiders execution finished.")

if __name__ == "__main__":
    run_all_spiders()
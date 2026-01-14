#!/usr/bin/env python3
"""
Clone the actual reviews_scraper from GitHub using sparse checkout.
"""
import subprocess
import sys
import os
import shutil

def run_command(cmd, cwd=None):
    """Run a shell command and return success status."""
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def main():
    """Clone the reviews_scraper."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 60)
    print("Cloning Sephora Reviews Scraper from GitHub")
    print("=" * 60)
    
    # Step 1: Initialize git repo
    print("\n1. Initializing git repository...")
    if not run_command(['git', 'init'], cwd=script_dir):
        print("⚠ Git init failed, but continuing...")
    
    # Step 2: Add remote
    print("\n2. Adding remote origin...")
    if not run_command(['git', 'remote', 'add', 'origin', 'https://github.com/nadyinky/sephora-analysis'], cwd=script_dir):
        # Remote might already exist
        print("⚠ Remote might already exist, continuing...")
    
    # Step 3: Configure sparse checkout
    print("\n3. Configuring sparse checkout...")
    run_command(['git', 'config', 'core.sparseCheckout', 'true'], cwd=script_dir)
    
    # Step 4: Set sparse checkout path
    print("\n4. Setting sparse checkout path...")
    sparse_path = 'sephora_scraper/reviews_scraper'
    
    # Create .git/info/sparse-checkout file
    git_info_dir = os.path.join(script_dir, '.git', 'info')
    os.makedirs(git_info_dir, exist_ok=True)
    sparse_checkout_file = os.path.join(git_info_dir, 'sparse-checkout')
    with open(sparse_checkout_file, 'w') as f:
        f.write(sparse_path + '\n')
    print(f"✓ Created sparse-checkout file: {sparse_path}")
    
    # Step 5: Pull from main branch
    print("\n5. Pulling from origin main...")
    if run_command(['git', 'pull', 'origin', 'main'], cwd=script_dir):
        print("\n✓ Successfully cloned reviews_scraper!")
        
        # Move files from sephora_scraper/reviews_scraper to current directory
        source_dir = os.path.join(script_dir, 'sephora_scraper', 'reviews_scraper')
        if os.path.exists(source_dir):
            print("\n6. Moving files to current directory...")
            for item in os.listdir(source_dir):
                source = os.path.join(source_dir, item)
                dest = os.path.join(script_dir, item)
                if os.path.isdir(source):
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
                print(f"  ✓ Moved {item}")
            
            # Clean up
            shutil.rmtree(os.path.join(script_dir, 'sephora_scraper'), ignore_errors=True)
            print("\n✓ Cleanup complete")
        
        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Install dependencies: cd reviews_scraper && pip install -r requirements.txt")
        print("2. Configure proxy in reviews_scraper.py (if needed)")
        print("3. Add product IDs to product_ids.txt")
        print("4. Run: python reviews_scraper.py")
    else:
        print("\n✗ Failed to pull from repository")
        print("You may need to run this manually:")
        print("  git pull origin main")

if __name__ == "__main__":
    main()





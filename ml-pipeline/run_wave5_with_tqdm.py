#!/usr/bin/env python3
"""Simple TQDM wrapper for the Wave 5 bash pipeline script."""

import subprocess
import sys
import re
from tqdm import tqdm
import time

def run_pipeline_with_tqdm():
    """Run the bash pipeline script with TQDM progress tracking."""
    
    # Create main progress bar
    with tqdm(total=5, desc="Wave 5 Pipeline", unit="step", 
              bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}') as pbar:
        
        # Run the bash script
        process = subprocess.Popen(
            ['bash', 'run_wave5_pipeline.sh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        current_step = ""
        
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
                
            # Print the line (removes newline and re-adds it to avoid double spacing)
            print(line.rstrip())
            
            # Detect progress updates
            if "Progress:" in line and "Step" in line:
                # Extract step info
                match = re.search(r'Step (\d+)/(\d+): (.+)', line)
                if match:
                    step_num = int(match.group(1))
                    step_name = match.group(3)
                    pbar.update(1)
                    pbar.set_postfix_str(f"Current: {step_name}")
            
            # Track training progress
            elif "Epoch" in line:
                # Extract epoch info if present
                epoch_match = re.search(r'Epoch (\d+)/(\d+)', line)
                if epoch_match:
                    epoch = int(epoch_match.group(1))
                    total_epochs = int(epoch_match.group(2))
                    pbar.set_postfix_str(f"Training: Epoch {epoch}/{total_epochs}")
            
            # Track accuracy results
            elif "accuracy" in line.lower() and ":" in line:
                pbar.set_postfix_str(line.strip()[:50])
        
        # Wait for process to complete
        return_code = process.wait()
        
        # Final update
        if return_code == 0:
            pbar.set_postfix_str("✅ Pipeline completed successfully!")
        else:
            pbar.set_postfix_str("❌ Pipeline failed!")
        
        return return_code

if __name__ == "__main__":
    print("\n🚀 Starting Wave 5 Pipeline with TQDM Progress Tracking\n")
    
    try:
        exit_code = run_pipeline_with_tqdm()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
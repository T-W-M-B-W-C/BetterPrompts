#!/usr/bin/env python3
"""
Reassemble training data chunks on RunPod
"""

import json
import glob
import os

def reassemble_chunks():
    """Reassemble all chunks into the complete training data"""
    
    # Find all chunk files
    chunk_files = sorted(glob.glob('training_chunk_*.json'))
    
    if not chunk_files:
        print("❌ No chunk files found!")
        return
    
    print(f"📥 Found {len(chunk_files)} chunks to reassemble")
    
    # Load and combine all chunks
    all_data = []
    for chunk_file in chunk_files:
        with open(chunk_file, 'r') as f:
            chunk_data = json.load(f)
            all_data.extend(chunk_data)
            print(f"  ✅ Loaded {chunk_file}: {len(chunk_data)} samples")
    
    # Save the complete dataset
    os.makedirs('data/raw', exist_ok=True)
    with open('data/raw/training_data_large.json', 'w') as f:
        json.dump(all_data, f, indent=2)
    
    print(f"✅ Reassembled {len(all_data)} total samples")
    print(f"📁 Saved to: data/raw/training_data_large.json")
    
    # Clean up chunks
    for chunk_file in chunk_files:
        os.remove(chunk_file)
    print("🧹 Cleaned up chunk files")

if __name__ == "__main__":
    reassemble_chunks()

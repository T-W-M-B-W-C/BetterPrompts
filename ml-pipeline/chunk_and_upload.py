#!/usr/bin/env python3
"""
Split training data into chunks for easier transfer to RunPod
"""

import json
import base64
import os

def split_training_data():
    """Split the training data into smaller chunks"""
    
    # Load the training data
    with open('data/raw/training_data_large.json', 'r') as f:
        data = json.load(f)
    
    # Split into chunks of 1000 samples each
    chunk_size = 1000
    chunks = []
    
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        chunks.append(chunk)
    
    print(f"📊 Split {len(data)} samples into {len(chunks)} chunks")
    
    # Save each chunk
    os.makedirs('data/chunks', exist_ok=True)
    
    for idx, chunk in enumerate(chunks):
        chunk_file = f'data/chunks/training_chunk_{idx:02d}.json'
        with open(chunk_file, 'w') as f:
            json.dump(chunk, f)
        
        # Also create a base64 encoded version for easy copy-paste
        chunk_b64_file = f'data/chunks/training_chunk_{idx:02d}.b64'
        chunk_json = json.dumps(chunk)
        chunk_b64 = base64.b64encode(chunk_json.encode()).decode()
        
        with open(chunk_b64_file, 'w') as f:
            f.write(chunk_b64)
        
        file_size = os.path.getsize(chunk_file) / 1024  # KB
        print(f"✅ Chunk {idx}: {len(chunk)} samples, {file_size:.1f} KB")
    
    # Create a reassembly script
    reassembly_script = '''#!/usr/bin/env python3
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
'''
    
    with open('data/chunks/reassemble_chunks.py', 'w') as f:
        f.write(reassembly_script)
    
    print("\n📝 Created reassembly script: data/chunks/reassemble_chunks.py")
    print(f"📦 Total chunks created: {len(chunks)}")
    
    return len(chunks)

if __name__ == "__main__":
    num_chunks = split_training_data()
    
    print("\n" + "="*60)
    print("📋 NEXT STEPS:")
    print("="*60)
    print("1. Each chunk can be sent individually using:")
    print("   runpodctl send data/chunks/training_chunk_XX.json")
    print("")
    print("2. On RunPod, receive each chunk with the codes provided")
    print("")
    print("3. After all chunks are received, run:")
    print("   python reassemble_chunks.py")
    print("")
    print("4. Then run the training script")
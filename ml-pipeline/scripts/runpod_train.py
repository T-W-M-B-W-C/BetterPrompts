#!/usr/bin/env python3
"""Automated training script for RunPod with monitoring and optimization."""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
import argparse

try:
    import nvidia_ml_py3 as nvml
    GPU_AVAILABLE = True
except ImportError:
    print("⚠️  nvidia-ml-py3 not installed, GPU monitoring disabled")
    GPU_AVAILABLE = False

from tqdm import tqdm
from loguru import logger


class RunPodTrainer:
    """Manages training on RunPod with monitoring and optimization."""
    
    def __init__(self, auto_shutdown=True, shutdown_delay=10):
        self.auto_shutdown = auto_shutdown
        self.shutdown_delay = shutdown_delay
        self.start_time = datetime.now()
        self.results = {
            "start_time": self.start_time.isoformat(),
            "gpu_info": self.get_gpu_info(),
            "training_complete": False,
            "accuracy": None,
            "duration_minutes": None
        }
        
    def get_gpu_info(self):
        """Get GPU information."""
        if not GPU_AVAILABLE:
            return {"error": "GPU monitoring not available"}
            
        try:
            nvml.nvmlInit()
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            
            # Get GPU name and memory
            name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
            mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
            
            return {
                "name": name,
                "memory_total_gb": round(mem_info.total / 1e9, 1),
                "driver_version": nvml.nvmlSystemGetDriverVersion().decode('utf-8')
            }
        except Exception as e:
            return {"error": str(e)}
    
    def monitor_gpu(self):
        """Monitor current GPU usage."""
        if not GPU_AVAILABLE:
            return
            
        try:
            nvml.nvmlInit()
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            
            # Memory info
            mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
            mem_used_gb = mem_info.used / 1e9
            mem_total_gb = mem_info.total / 1e9
            
            # Utilization
            util = nvml.nvmlDeviceGetUtilizationRates(handle)
            
            # Temperature
            temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
            
            # Power
            power = nvml.nvmlDeviceGetPowerUsage(handle) / 1000  # Convert to W
            
            logger.info(f"GPU: {util.gpu}% | Memory: {mem_used_gb:.1f}/{mem_total_gb:.1f}GB | Temp: {temp}°C | Power: {power:.0f}W")
            
            return {
                "utilization": util.gpu,
                "memory_used_gb": round(mem_used_gb, 1),
                "temperature": temp,
                "power_watts": round(power, 0)
            }
        except Exception as e:
            logger.warning(f"GPU monitoring error: {e}")
            return None
    
    def verify_environment(self):
        """Verify RunPod environment is properly set up."""
        logger.info("🔍 Verifying RunPod environment...")
        
        checks = {
            "cuda_available": torch.cuda.is_available() if 'torch' in sys.modules else False,
            "workspace_exists": os.path.exists("/workspace"),
            "training_data_exists": os.path.exists("data_generation/openai_training_data.json"),
            "gpu_visible": subprocess.run(["nvidia-smi"], capture_output=True).returncode == 0
        }
        
        # Show results
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"{status} {check}: {passed}")
        
        if not all(checks.values()):
            logger.error("Environment verification failed!")
            if not checks["workspace_exists"]:
                logger.error("Not running on RunPod? /workspace directory not found")
            if not checks["training_data_exists"]:
                logger.error("Training data not found. Upload data_generation/openai_training_data.json")
            return False
            
        # Show GPU details
        gpu_info = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True
        )
        if gpu_info.returncode == 0:
            logger.info(f"GPU Details: {gpu_info.stdout.strip()}")
            
        return True
    
    def optimize_batch_size(self):
        """Determine optimal batch size based on GPU memory."""
        gpu_info = self.get_gpu_info()
        memory_gb = gpu_info.get("memory_total_gb", 24)
        
        # Batch size recommendations based on GPU memory
        if memory_gb >= 40:  # A100, A40
            return 128
        elif memory_gb >= 24:  # RTX 3090, 4090
            return 64
        elif memory_gb >= 16:  # V100, RTX 3080
            return 32
        else:
            return 16
    
    def run_training(self):
        """Run the complete training pipeline."""
        if not self.verify_environment():
            return False
        
        logger.info("🚀 Starting DistilBERT training on RunPod...")
        
        # Determine optimal settings
        batch_size = self.optimize_batch_size()
        logger.info(f"Using batch size: {batch_size}")
        
        # Training command
        cmd = [
            "python", "train_distilbert.py",
            "--data-path", "data_generation/openai_training_data.json",
            "--output-dir", "models/distilbert_intent_classifier",
            "--num-epochs", "5",
            "--batch-size", str(batch_size),
            "--learning-rate", "5e-5",
            "--fp16",  # Always use mixed precision on GPU
            "--export-onnx"
        ]
        
        # Run training with monitoring
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True,
            bufsize=1
        )
        
        step_count = 0
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
            
            # Monitor GPU periodically
            if "step" in line.lower():
                step_count += 1
                if step_count % 50 == 0:  # Every 50 steps
                    self.monitor_gpu()
        
        return_code = process.wait()
        
        if return_code == 0:
            logger.success("✅ Training completed successfully!")
            self.results["training_complete"] = True
        else:
            logger.error(f"❌ Training failed with code {return_code}")
            
        return return_code == 0
    
    def run_validation(self):
        """Run model validation."""
        logger.info("📊 Running validation...")
        
        cmd = [
            "python", "scripts/validate_model_accuracy.py",
            "--model-path", "models/distilbert_intent_classifier",
            "--data-path", "data_generation/openai_training_data.json",
            "--output-dir", "validation_results"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Try to extract accuracy from validation results
            try:
                with open("validation_results/validation_results.json", "r") as f:
                    val_results = json.load(f)
                    accuracy = val_results["intent"]["accuracy"]
                    self.results["accuracy"] = accuracy
                    logger.success(f"✅ Validation complete! Accuracy: {accuracy*100:.2f}%")
            except:
                logger.warning("Could not extract accuracy from results")
        else:
            logger.error("Validation failed")
            
        return result.returncode == 0
    
    def package_results(self):
        """Package all results for download."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"runpod_training_results_{timestamp}.tar.gz"
        
        logger.info(f"📦 Packaging results as {archive_name}...")
        
        # Save training summary
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration_minutes"] = (datetime.now() - self.start_time).total_seconds() / 60
        
        with open("training_summary.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Create archive
        cmd = [
            "tar", "-czf", archive_name,
            "models/distilbert_intent_classifier",
            "validation_results",
            "training_summary.json"
        ]
        
        # Add ONNX model if it exists
        if os.path.exists("models/onnx"):
            cmd.append("models/onnx")
        
        subprocess.run(cmd)
        
        # Get pod IP for download instructions
        try:
            hostname = subprocess.run(
                ["hostname", "-I"], 
                capture_output=True, 
                text=True
            ).stdout.strip().split()[0]
        except:
            hostname = "[POD_IP]"
        
        logger.info("\n" + "="*60)
        logger.info("🎉 Training complete! Results packaged.")
        logger.info(f"📥 Download with:")
        logger.info(f"   scp root@{hostname}:/workspace/betterprompts/ml-pipeline/{archive_name} ./")
        logger.info("="*60)
        
        return archive_name
    
    def auto_shutdown_pod(self):
        """Auto-shutdown pod after delay."""
        if not self.auto_shutdown:
            logger.info("Auto-shutdown disabled. Pod will remain active.")
            return
            
        logger.warning(f"⏰ Pod will shut down in {self.shutdown_delay} minutes...")
        logger.warning("Press Ctrl+C to cancel shutdown")
        
        try:
            for i in range(self.shutdown_delay * 60):
                time.sleep(1)
                if i % 60 == 0:
                    remaining = self.shutdown_delay - (i // 60)
                    logger.warning(f"Shutdown in {remaining} minutes...")
        except KeyboardInterrupt:
            logger.info("Shutdown cancelled")
            return
            
        logger.warning("Shutting down pod...")
        subprocess.run(["shutdown", "-h", "now"])
    
    def run(self):
        """Run complete pipeline."""
        try:
            # Import torch to check CUDA
            global torch
            import torch
            
            # Training
            if not self.run_training():
                logger.error("Training failed!")
                return 1
            
            # Validation
            self.run_validation()
            
            # Package results
            self.package_results()
            
            # Auto-shutdown
            self.auto_shutdown_pod()
            
            return 0
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="RunPod training pipeline")
    parser.add_argument(
        "--no-shutdown", 
        action="store_true",
        help="Disable auto-shutdown after training"
    )
    parser.add_argument(
        "--shutdown-delay",
        type=int,
        default=10,
        help="Minutes to wait before shutdown (default: 10)"
    )
    
    args = parser.parse_args()
    
    trainer = RunPodTrainer(
        auto_shutdown=not args.no_shutdown,
        shutdown_delay=args.shutdown_delay
    )
    
    return trainer.run()


if __name__ == "__main__":
    sys.exit(main())
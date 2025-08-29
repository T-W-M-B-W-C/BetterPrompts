#!/usr/bin/env python3
"""Real-time monitoring dashboard for RunPod training."""

import time
import subprocess
import psutil
from datetime import datetime
from typing import Dict, Any
import json

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    print("Installing rich for better visualization...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"])
    RICH_AVAILABLE = False

try:
    import nvidia_ml_py3 as nvml
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


class RunPodMonitor:
    """Monitors RunPod training progress and resources."""
    
    def __init__(self):
        self.console = Console()
        self.start_time = datetime.now()
        self.training_log_path = "models/distilbert_intent_classifier/trainer_state.json"
        
    def get_gpu_stats(self) -> Dict[str, Any]:
        """Get detailed GPU statistics."""
        if not GPU_AVAILABLE:
            return {"error": "GPU monitoring not available"}
            
        try:
            nvml.nvmlInit()
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            
            # Basic info
            name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
            
            # Memory
            mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
            mem_used_gb = mem_info.used / 1e9
            mem_total_gb = mem_info.total / 1e9
            mem_percent = (mem_info.used / mem_info.total) * 100
            
            # Utilization
            util = nvml.nvmlDeviceGetUtilizationRates(handle)
            
            # Temperature
            temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
            
            # Power
            try:
                power = nvml.nvmlDeviceGetPowerUsage(handle) / 1000  # W
                power_limit = nvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000  # W
            except:
                power = 0
                power_limit = 0
            
            # Clock speeds
            try:
                gpu_clock = nvml.nvmlDeviceGetClockInfo(handle, nvml.NVML_CLOCK_GRAPHICS)
                mem_clock = nvml.nvmlDeviceGetClockInfo(handle, nvml.NVML_CLOCK_MEM)
            except:
                gpu_clock = 0
                mem_clock = 0
            
            return {
                "name": name,
                "utilization": util.gpu,
                "memory_used_gb": round(mem_used_gb, 2),
                "memory_total_gb": round(mem_total_gb, 2),
                "memory_percent": round(mem_percent, 1),
                "temperature": temp,
                "power_watts": round(power, 0),
                "power_limit_watts": round(power_limit, 0),
                "gpu_clock_mhz": gpu_clock,
                "memory_clock_mhz": mem_clock
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system CPU and memory statistics."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_count": psutil.cpu_count(),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_gb": round(psutil.virtual_memory().used / 1e9, 2),
            "memory_total_gb": round(psutil.virtual_memory().total / 1e9, 2),
            "disk_percent": psutil.disk_usage('/').percent,
            "disk_used_gb": round(psutil.disk_usage('/').used / 1e9, 2),
            "disk_total_gb": round(psutil.disk_usage('/').total / 1e9, 2)
        }
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training progress from trainer state."""
        try:
            with open(self.training_log_path, 'r') as f:
                state = json.load(f)
                
            # Extract relevant info
            current_epoch = state.get("epoch", 0)
            total_epochs = state.get("num_train_epochs", 5)
            current_step = state.get("global_step", 0)
            total_steps = state.get("max_steps", 0)
            
            # Get latest metrics
            log_history = state.get("log_history", [])
            latest_metrics = {}
            for entry in reversed(log_history):
                if "loss" in entry:
                    latest_metrics["loss"] = round(entry["loss"], 4)
                if "eval_accuracy" in entry:
                    latest_metrics["eval_accuracy"] = round(entry["eval_accuracy"], 4)
                if "learning_rate" in entry:
                    latest_metrics["learning_rate"] = entry["learning_rate"]
                if latest_metrics.get("loss") and latest_metrics.get("eval_accuracy"):
                    break
            
            return {
                "current_epoch": current_epoch,
                "total_epochs": total_epochs,
                "current_step": current_step,
                "total_steps": total_steps,
                "progress_percent": round((current_step / total_steps * 100) if total_steps > 0 else 0, 1),
                **latest_metrics
            }
        except:
            return {
                "status": "No training data yet",
                "current_epoch": 0,
                "total_epochs": 5,
                "progress_percent": 0
            }
    
    def estimate_cost(self, gpu_name: str, runtime_minutes: float) -> Dict[str, float]:
        """Estimate RunPod cost based on GPU and runtime."""
        # RunPod pricing (approximate)
        gpu_hourly_rates = {
            "RTX 3090": 0.34,
            "RTX 4090": 0.44,
            "A40": 0.79,
            "A100": 1.89,
            "H100": 3.99
        }
        
        # Find matching GPU
        hourly_rate = 0.5  # Default
        for gpu, rate in gpu_hourly_rates.items():
            if gpu.lower() in gpu_name.lower():
                hourly_rate = rate
                break
        
        cost = (runtime_minutes / 60) * hourly_rate
        
        return {
            "hourly_rate": hourly_rate,
            "current_cost": round(cost, 3),
            "projected_total": round(cost * (1 / (self.get_training_stats()["progress_percent"] / 100)) if self.get_training_stats()["progress_percent"] > 0 else cost, 3)
        }
    
    def create_dashboard(self) -> Table:
        """Create the monitoring dashboard."""
        # Get all stats
        gpu_stats = self.get_gpu_stats()
        sys_stats = self.get_system_stats()
        train_stats = self.get_training_stats()
        runtime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        cost_stats = self.estimate_cost(gpu_stats.get("name", "Unknown"), runtime_minutes)
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=4)
        )
        
        # Header
        header_text = f"[bold cyan]BetterPrompts RunPod Training Monitor[/bold cyan]\n"
        header_text += f"Runtime: {int(runtime_minutes)}m {int((runtime_minutes % 1) * 60)}s"
        layout["header"].update(Panel(header_text, box=box.ROUNDED))
        
        # Main content
        layout["main"].split_row(
            Layout(name="gpu", ratio=1),
            Layout(name="system", ratio=1),
            Layout(name="training", ratio=1)
        )
        
        # GPU Panel
        gpu_table = Table(show_header=False, box=None)
        gpu_table.add_column("Metric", style="cyan")
        gpu_table.add_column("Value", style="green")
        
        if "error" not in gpu_stats:
            gpu_table.add_row("GPU", gpu_stats["name"])
            gpu_table.add_row("Utilization", f"{gpu_stats['utilization']}%")
            gpu_table.add_row("Memory", f"{gpu_stats['memory_used_gb']}/{gpu_stats['memory_total_gb']}GB ({gpu_stats['memory_percent']}%)")
            gpu_table.add_row("Temperature", f"{gpu_stats['temperature']}°C")
            gpu_table.add_row("Power", f"{gpu_stats['power_watts']}/{gpu_stats['power_limit_watts']}W")
            gpu_table.add_row("GPU Clock", f"{gpu_stats['gpu_clock_mhz']} MHz")
        else:
            gpu_table.add_row("Status", "GPU monitoring unavailable")
        
        layout["main"]["gpu"].update(Panel(gpu_table, title="🎮 GPU Stats", box=box.ROUNDED))
        
        # System Panel
        sys_table = Table(show_header=False, box=None)
        sys_table.add_column("Metric", style="cyan")
        sys_table.add_column("Value", style="green")
        
        sys_table.add_row("CPU", f"{sys_stats['cpu_percent']}% ({sys_stats['cpu_count']} cores)")
        sys_table.add_row("Memory", f"{sys_stats['memory_used_gb']}/{sys_stats['memory_total_gb']}GB ({sys_stats['memory_percent']}%)")
        sys_table.add_row("Disk", f"{sys_stats['disk_used_gb']}/{sys_stats['disk_total_gb']}GB ({sys_stats['disk_percent']}%)")
        
        layout["main"]["system"].update(Panel(sys_table, title="💻 System Stats", box=box.ROUNDED))
        
        # Training Panel
        train_table = Table(show_header=False, box=None)
        train_table.add_column("Metric", style="cyan")
        train_table.add_column("Value", style="green")
        
        train_table.add_row("Epoch", f"{train_stats['current_epoch']}/{train_stats['total_epochs']}")
        train_table.add_row("Progress", f"{train_stats['progress_percent']}%")
        if "loss" in train_stats:
            train_table.add_row("Loss", f"{train_stats['loss']}")
        if "eval_accuracy" in train_stats:
            train_table.add_row("Val Accuracy", f"{train_stats['eval_accuracy']*100:.2f}%")
        if "learning_rate" in train_stats:
            train_table.add_row("Learning Rate", f"{train_stats['learning_rate']:.2e}")
        
        layout["main"]["training"].update(Panel(train_table, title="📊 Training Progress", box=box.ROUNDED))
        
        # Footer - Cost estimation
        cost_text = f"[yellow]💰 Cost Estimate:[/yellow] ${cost_stats['current_cost']:.3f} "
        cost_text += f"(Projected Total: ${cost_stats['projected_total']:.3f} @ ${cost_stats['hourly_rate']}/hr)"
        layout["footer"].update(Panel(cost_text, box=box.ROUNDED))
        
        return layout
    
    def run(self):
        """Run the monitoring dashboard."""
        self.console.print("\n[bold]Starting RunPod Training Monitor...[/bold]\n")
        self.console.print("Press Ctrl+C to exit\n")
        
        try:
            with Live(self.create_dashboard(), refresh_per_second=1, console=self.console) as live:
                while True:
                    time.sleep(1)
                    live.update(self.create_dashboard())
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Monitor stopped[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")


if __name__ == "__main__":
    monitor = RunPodMonitor()
    monitor.run()
#!/usr/bin/env python3
import yaml
import subprocess
import sys
import time
import requests
from pathlib import Path

def check_device_availability(device):
    """Check if specified device is available"""
    try:
        import torch
        if device == "cuda":
            if not torch.cuda.is_available():
                return False, "CUDA is not available. Please install CUDA and appropriate drivers."
        elif device == "mps":
            if not torch.backends.mps.is_available():
                return False, "MPS is not available. Please ensure you're using macOS 12.3+ and PyTorch 1.12+ on Apple Silicon."
        return True, None
    except ImportError:
        return False, "PyTorch is not installed. Please install PyTorch."

def read_config():
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            
            # Check if MPS is specified and raise error
            device = config.get("embedding", {}).get("device", "cpu").lower()
            if device == "mps":
                print("❌ Error: MPS is not supported in Docker environment")
                print("💡 Please use either:")
                print("   • device: 'cpu'    (works everywhere)")
                print("   • device: 'cuda'   (requires NVIDIA GPU)")
                print("\nTo change this, edit your backend/config.yaml")
                sys.exit(1)
            
            # Automatically set Ollama base_url for Docker environment
            if config.get("llm", {}).get("provider") == "ollama":
                # Override base_url for Docker environment
                config["llm"]["base_url"] = "http://ollama:11434"
                print("ℹ️  Setting Ollama base_url to http://ollama:11434 for Docker environment")
                
                # Write the modified config back to file
                with open("config.yaml", "w") as f:
                    yaml.dump(config, f, default_flow_style=False)
            
            # Check device availability
            if config["embedding"]["device"] != "cpu":
                is_available, error_msg = check_device_availability(config["embedding"]["device"])
                if not is_available:
                    print(f"❌ Error: {error_msg}")
                    print("💡 Please either:")
                    print(f"   1. Set up {config['embedding']['device'].upper()} properly")
                    print("   2. Or change device to 'cpu' in backend/config.yaml")
                    sys.exit(1)
            return config
    except FileNotFoundError:
        print("Error: config.yaml not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml: {e}")
        sys.exit(1)

def clean_docker():
    """Clean up Docker resources"""
    print("🧹 Cleaning up Docker resources...")
    commands = [
        "docker-compose down",
        "docker volume rm simba_redis_data 2>/dev/null || true"
    ]
    for cmd in commands:
        subprocess.run(cmd, shell=True)

def build_compose_command(config):
    """Build docker-compose command based on config"""
    device = config.get("embedding", {}).get("device", "cpu").lower()
    
    # Base compose file
    compose_files = [f"docker-compose.{device}.yml"]
    
    # Build the command
    cmd_parts = ["docker-compose"]
    for f in compose_files:
        if not Path(f).exists():
            print(f"Error: {f} not found")
            sys.exit(1)
        cmd_parts.extend(["-f", f])
    
    return cmd_parts

def main():
    # Read configuration
    print("📖 Reading configuration...")
    config = read_config()
    
    # Clean up first
    clean_docker()
    
    # Build the command
    cmd_parts = build_compose_command(config)
    cmd_parts.extend(["up", "--build"])
    
    # Print configuration info
    device = config["embedding"]["device"]
    provider = config["llm"]["provider"]
    model = config["llm"]["model_name"]
    print(f"\n🚀 Launching with configuration:")
    print(f"   • Device: {device}")
    print(f"   • LLM Provider: {provider}")
    print(f"   • Model: {model}")
    print(f"   • Ollama base_url: {config['llm']['base_url']}")
    print(f"   • Using compose files: {', '.join(cmd_parts[2::2])}\n")
    
    
    # Execute docker-compose
    try:
        subprocess.run(" ".join(cmd_parts), shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running docker-compose: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
        clean_docker()

if __name__ == "__main__":
    main() 
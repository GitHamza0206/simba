#!/usr/bin/env python3
import yaml
import subprocess
import sys
import time
import requests
from pathlib import Path


def read_config():
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            
            # Check if MPS is specified and raise error
            device = config.get("embedding", {}).get("device", "cpu").lower()
            
            # Block CUDA on macOS
            if device == "cuda" and sys.platform == "darwin":
                print("❌ Error: NVIDIA GPU acceleration is not supported on macOS")
                print("💡 Please use either:")
                print("   • device: 'cpu'    (works everywhere)")
                print("\nTo change this, edit your backend/config.yaml")
                sys.exit(1)
                
            if device == "mps":
                print("❌ Error: MPS is not supported in Docker environment")
                print("💡 Please use either:")
                print("   • device: 'cpu'    (works everywhere)")
                print("   • device: 'cuda'   (requires NVIDIA GPU)")
                print("\nTo change this, edit your backend/config.yaml")
                sys.exit(1)
            
            # Check device availability
            if device not in ["cpu", "cuda"]:
                print(f"❌ Error: {device.upper()} device is not available")
                print("💡 Please either:")
                print(f"  1. Should be 'cpu' or 'cuda'")
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
    if device == "cuda":
        device = "gpu" 
    
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
# Kubernetes the Hard Way - Local Lab

Simple containerized setup for Kelsey Hightower's "Kubernetes the Hard Way" tutorial.

## Usage

```bash
# Start the lab (creates containers if needed, starts if they exist)
start-lab.bat

# Connect to any machine
connect.bat jumpbox
connect.bat server
connect.bat node-0
connect.bat node-1

# Stop the lab (preserves containers and data)
stop-lab.bat

# Clean up everything (removes containers completely)
clean-lab.bat
```

## Lab Environment

| Machine | IP | SSH Port | Role | Specs |
|---------|----|---------|----|-------|
| jumpbox | 172.20.0.10 | 2210 | Admin host | 1 CPU, 512MB RAM |
| server | 172.20.0.11 | 2211 | Control plane | 1 CPU, 2GB RAM |
| node-0 | 172.20.0.12 | 2212 | Worker node | 1 CPU, 2GB RAM |
| node-1 | 172.20.0.13 | 2213 | Worker node | 1 CPU, 2GB RAM |

**Default password:** `k8s-hard-way`

## Container States

- **start-lab.bat**: Creates containers (first time) or starts existing ones
- **stop-lab.bat**: Stops containers but preserves all data/configs
- **clean-lab.bat**: Completely removes containers (fresh start)

Your work inside containers persists between start/stop cycles!
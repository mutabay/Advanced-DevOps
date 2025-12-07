@echo off
echo Cleaning up Kubernetes the Hard Way lab...

podman stop jumpbox server node-0 node-1 2>nul
podman rm jumpbox server node-0 node-1 2>nul
podman network rm k8s-network 2>nul

echo.
echo Lab completely removed! Use start-lab.bat to create fresh containers.
echo.
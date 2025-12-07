@echo off
echo Stopping Kubernetes the Hard Way lab...

podman stop jumpbox server node-0 node-1

echo.
echo Lab stopped! Containers are preserved and can be restarted with start-lab.bat
echo.
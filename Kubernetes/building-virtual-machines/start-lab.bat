@echo off
echo Starting Kubernetes the Hard Way lab...

REM Create network if it doesn't exist
podman network create --subnet=172.20.0.0/16 k8s-network 2>nul

REM Start containers (they'll be created if they don't exist)
podman start jumpbox 2>nul || podman run -d --name jumpbox --network k8s-network --ip 172.20.0.10 -p 2210:22 --memory=512m debian-k8s:latest
podman start server 2>nul || podman run -d --name server --network k8s-network --ip 172.20.0.11 -p 2211:22 --memory=2g debian-k8s:latest
podman start node-0 2>nul || podman run -d --name node-0 --network k8s-network --ip 172.20.0.12 -p 2212:22 --memory=2g debian-k8s:latest
podman start node-1 2>nul || podman run -d --name node-1 --network k8s-network --ip 172.20.0.13 -p 2213:22 --memory=2g debian-k8s:latest

echo.
echo Lab is running!
echo.
echo Machines:
echo - jumpbox: ssh -p 2210 root@localhost
echo - server:  ssh -p 2211 root@localhost
echo - node-0:  ssh -p 2212 root@localhost
echo - node-1:  ssh -p 2213 root@localhost
echo.
echo Password: k8s-hard-way
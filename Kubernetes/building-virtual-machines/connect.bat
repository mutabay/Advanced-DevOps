@echo off
if "%1"=="jumpbox" (
    ssh -p 2210 root@localhost
) else if "%1"=="server" (
    ssh -p 2211 root@localhost
) else if "%1"=="node-0" (
    ssh -p 2212 root@localhost
) else if "%1"=="node-1" (
    ssh -p 2213 root@localhost
) else (
    echo Usage: connect.bat [jumpbox^|server^|node-0^|node-1]
    echo.
    echo Available machines:
    echo - jumpbox: Administration host
    echo - server:  Kubernetes control plane
    echo - node-0:  Worker node
    echo - node-1:  Worker node
    echo.
    echo Password: k8s-hard-way
)
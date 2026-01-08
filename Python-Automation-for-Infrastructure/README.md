# Python Automation for Infrastructure

**Goal**: Create Python-based infrastructure automation using FastAPI, async I/O, background workers, and intelligent task orchestration to build production-ready automation systems.

## Learning Objectives

By the end of this:
- Build FastAPI backends for infrastructure automation
- Async/await patterns for high-concurrency operations
- Implement background task processing with Celery and Dramatiq
- Create intelligent remediation systems and health monitoring agents
- Design scalable task orchestration and workflow automation
- Build production-ready infrastructure automation platforms

## Quick Reference: Core Concepts

### FastAPI Fundamentals
- **Async Endpoints**: Non-blocking API operations for high throughput
- **Dependency Injection**: Reusable components and database connections
- **Background Tasks**: Immediate response with async processing
- **WebSocket Support**: Real-time infrastructure monitoring dashboards

### Async Programming Patterns
- **Concurrency vs Parallelism**: Async I/O vs multi-processing
- **Event Loop**: Single-threaded cooperative multitasking
- **async/await**: Non-blocking function calls
- **aiohttp/httpx**: Async HTTP clients for external API calls

### Background Workers
- **Celery**: Distributed task queue with Redis/RabbitMQ
- **Dramatiq**: Simple, reliable background task processing
- **Task Types**: Immediate, scheduled, periodic, retry-enabled
- **Result Storage**: Task status and result persistence

### Infrastructure Automation Patterns
- **Health Agents**: Continuous monitoring with automatic remediation
- **Task Runners**: Script orchestration and workflow management
- **Configuration Management**: Dynamic infrastructure configuration
- **Event-Driven Automation**: React to infrastructure events

## Module 1: FastAPI for Infrastructure APIs

### 1.1 Why FastAPI for Infrastructure Automation?

**Traditional Infrastructure Management:**
```python
# Synchronous blocking operations
def restart_service(service_name):
    result = subprocess.run(['systemctl', 'restart', service_name])
    return result.returncode == 0

# Limited concurrency, slow for multiple operations
```

**FastAPI Async Infrastructure Management:**
```python
# Non-blocking, high-concurrency operations
@app.post("/services/{service_name}/restart")
async def restart_service(service_name: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(perform_restart, service_name)
    return {"status": "restart_initiated", "service": service_name}

async def perform_restart(service_name):
    # Non-blocking subprocess execution
    process = await asyncio.create_subprocess_exec(
        'systemctl', 'restart', service_name
    )
    return await process.wait()
```

**Benefits:**
- **High Concurrency**: Handle thousands of simultaneous requests
- **Non-blocking I/O**: Don't wait for slow operations
- **Real-time Updates**: WebSocket support for live monitoring
- **Type Safety**: Automatic validation and documentation
- **Production Ready**: Built-in metrics, logging, and error handling

### 1.2 FastAPI Architecture Patterns

**Request Lifecycle:**
```
HTTP Request → FastAPI Router → Dependency Injection → Business Logic → Background Task → HTTP Response
                    ↓              ↓                      ↓               ↓
                Route Handler → Database/Auth → Async Operation → Task Queue → Client Gets Immediate Response
```

**Core Components:**
- **Routers**: Organize endpoints by functionality (servers, databases, monitoring)
- **Dependencies**: Shared resources (database connections, authentication)
- **Middleware**: Cross-cutting concerns (logging, metrics, CORS)
- **Background Tasks**: Async operations that continue after response

### 1.3 Infrastructure API Design Patterns

**Resource Management APIs:**
```python
# Server management
POST /servers/{server_id}/restart
GET  /servers/{server_id}/status
POST /servers/{server_id}/deploy
PUT  /servers/{server_id}/configuration

# Service management  
POST /services/{service_name}/restart
GET  /services/{service_name}/health
POST /services/{service_name}/scale
PUT  /services/{service_name}/config

# Database operations
POST /databases/{db_name}/backup
POST /databases/{db_name}/restore
GET  /databases/{db_name}/metrics
PUT  /databases/{db_name}/maintenance
```

## Module 2: Async Programming for Infrastructure

### 2.1 Understanding Async vs Sync

**Synchronous Infrastructure Operations (Blocking):**
```python
def check_server_health():
    servers = ['web1', 'web2', 'db1', 'cache1']
    results = []
    
    for server in servers:  # Sequential - 4 seconds total
        response = requests.get(f'http://{server}/health', timeout=1)
        results.append({server: response.status_code})
    
    return results  # Takes 4+ seconds for 4 servers
```

**Asynchronous Infrastructure Operations (Non-blocking):**
```python
async def check_server_health():
    servers = ['web1', 'web2', 'db1', 'cache1']
    
    async def check_single_server(server):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f'http://{server}/health', timeout=1) as response:
                    return {server: response.status}
            except asyncio.TimeoutError:
                return {server: 'timeout'}
    
    # Concurrent - all servers checked simultaneously
    tasks = [check_single_server(server) for server in servers]
    results = await asyncio.gather(*tasks)
    
    return results  # Takes ~1 second for 4 servers
```

### 2.2 Common Async Patterns for Infrastructure

**Pattern 1: Concurrent API Calls**
```python
async def deploy_to_multiple_environments():
    environments = ['staging', 'prod-east', 'prod-west']
    
    async def deploy_to_env(env):
        async with httpx.AsyncClient() as client:
            response = await client.post(f'https://{env}.company.com/deploy')
            return {env: response.status_code}
    
    # Deploy to all environments concurrently
    tasks = [deploy_to_env(env) for env in environments]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**Pattern 2: Async File Operations**
```python
async def process_log_files():
    log_files = ['app.log', 'error.log', 'access.log']
    
    async def process_single_log(filename):
        async with aiofiles.open(filename, 'r') as file:
            content = await file.read()
            # Process log content
            return analyze_log_content(content)
    
    tasks = [process_single_log(log) for log in log_files]
    results = await asyncio.gather(*tasks)
    return results
```

**Pattern 3: Long-running Monitoring**
```python
async def continuous_health_monitoring():
    while True:
        try:
            # Check all services concurrently
            health_results = await check_all_services()
            
            # Send alerts for failed services
            failed_services = [s for s in health_results if s['status'] != 'healthy']
            if failed_services:
                await send_alerts(failed_services)
            
            # Wait before next check
            await asyncio.sleep(30)  # Non-blocking sleep
            
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
            await asyncio.sleep(60)  # Back off on error
```

### 2.3 Async Best Practices for Infrastructure

**Error Handling with Timeouts:**
```python
async def robust_service_call(service_url):
    try:
        async with asyncio.timeout(10):  # 10-second timeout
            async with httpx.AsyncClient() as client:
                response = await client.get(service_url)
                return response.json()
    except asyncio.TimeoutError:
        return {"error": "service_timeout"}
    except httpx.RequestError:
        return {"error": "network_error"}
    except Exception as e:
        return {"error": f"unexpected_error: {e}"}
```

## Module 3: Background Workers Deep Dive

### 3.1 Celery vs Dramatiq Comparison

| Feature | Celery | Dramatiq | Use Case |
|---------|--------|----------|----------|
| **Complexity** | High | Low | Dramatiq for simplicity, Celery for enterprise |
| **Broker Support** | Redis, RabbitMQ, SQS | Redis, RabbitMQ | Both support major message brokers |
| **Result Storage** | Multiple backends | Redis only | Celery for complex result storage needs |
| **Monitoring** | Flower, built-in | Simple web UI | Celery has richer monitoring ecosystem |
| **Performance** | High throughput | Fast, lightweight | Dramatiq for speed, Celery for scale |
| **Learning Curve** | Steep | Gentle | Start with Dramatiq, upgrade to Celery if needed |

### 3.2 Task Categories for Infrastructure Automation

**Immediate Tasks (Response required):**
```python
# User requests server restart, needs immediate feedback
@dramatiq.actor
def restart_server_immediate(server_id):
    try:
        result = subprocess.run(['systemctl', 'restart', f'service-{server_id}'])
        return {"status": "success" if result.returncode == 0 else "failed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

**Scheduled Tasks (Time-based automation):**
```python
# Daily database backups
@dramatiq.actor
def daily_database_backup():
    databases = ['user_db', 'orders_db', 'analytics_db']
    
    for db in databases:
        backup_filename = f"{db}_backup_{datetime.now().strftime('%Y%m%d')}.sql"
        subprocess.run(['pg_dump', db, '-f', backup_filename])
        
        # Upload to S3 or backup storage
        upload_to_backup_storage(backup_filename)
```

**Periodic Tasks (Continuous monitoring):**
```python
# Every 5 minutes, check system health
@dramatiq.actor
def periodic_health_check():
    services = ['web_server', 'database', 'cache', 'queue']
    
    for service in services:
        health_status = check_service_health(service)
        
        if health_status['status'] != 'healthy':
            # Trigger remediation
            remediate_service.send(service, health_status['error'])
```

**Retry-Enabled Tasks (Fault-tolerant operations):**
```python
# Deployment with automatic retries
@dramatiq.actor(max_retries=3, retry_when=Exception)
def deploy_application(app_name, version):
    try:
        # Download deployment package
        download_deployment_package(app_name, version)
        
        # Stop current version
        stop_application(app_name)
        
        # Deploy new version
        deploy_new_version(app_name, version)
        
        # Start new version
        start_application(app_name)
        
        # Verify deployment
        verify_deployment_health(app_name)
        
    except Exception as e:
        # Log error for debugging
        logger.error(f"Deployment failed for {app_name} v{version}: {e}")
        raise  # Re-raise to trigger retry
```

### 3.3 Advanced Worker Patterns

**Workflow Orchestration:**
```python
# Complex deployment workflow
@dramatiq.actor
def orchestrate_full_deployment(app_name, version):
    # Step 1: Pre-deployment checks
    pre_checks_result = run_pre_deployment_checks.send(app_name)
    
    if pre_checks_result['status'] != 'passed':
        return {"status": "aborted", "reason": "pre_checks_failed"}
    
    # Step 2: Deploy to staging
    staging_result = deploy_to_staging.send(app_name, version)
    
    if staging_result['status'] != 'success':
        return {"status": "failed", "stage": "staging"}
    
    # Step 3: Run integration tests
    test_result = run_integration_tests.send(app_name, version)
    
    if test_result['status'] != 'passed':
        rollback_staging.send(app_name)
        return {"status": "failed", "stage": "testing"}
    
    # Step 4: Deploy to production
    prod_result = deploy_to_production.send(app_name, version)
    
    return {"status": "completed", "deployment_id": prod_result['deployment_id']}
```

## Module 4: Health Monitoring and Remediation

### 4.1 Intelligent Health Agents

**Health Agent Architecture:**
```
[Health Agent] → [Service Checks] → [Status Analysis] → [Auto-Remediation] → [Alert Escalation]
       ↓              ↓                    ↓                    ↓                ↓
   Continuous     Multi-layer         Pattern           Self-healing        Human
   Monitoring     Validation        Recognition         Actions          Intervention
```

**Health Check Types:**
```python
class HealthChecker:
    async def check_service_health(self, service_name):
        checks = {
            'process': await self.check_process_running(service_name),
            'port': await self.check_port_listening(service_name),
            'http': await self.check_http_endpoint(service_name),
            'dependencies': await self.check_dependencies(service_name),
            'resources': await self.check_resource_usage(service_name)
        }
        
        overall_status = 'healthy' if all(checks.values()) else 'unhealthy'
        
        return {
            'service': service_name,
            'status': overall_status,
            'checks': checks,
            'timestamp': datetime.utcnow()
        }
```

### 4.2 Remediation Patterns

**Progressive Remediation Strategy:**
```python
class ServiceRemediator:
    async def remediate_service(self, service_name, health_status):
        failed_checks = [check for check, status in health_status['checks'].items() if not status]
        
        for attempt in range(1, 4):  # 3 attempts with escalating actions
            if attempt == 1:
                # Gentle remediation
                await self.restart_service_gracefully(service_name)
            elif attempt == 2:
                # Forceful remediation
                await self.restart_service_forcefully(service_name)
            elif attempt == 3:
                # Last resort
                await self.restart_entire_system(service_name)
            
            # Wait and recheck
            await asyncio.sleep(30)
            new_health = await self.check_service_health(service_name)
            
            if new_health['status'] == 'healthy':
                return {"remediation": "successful", "attempts": attempt}
        
        # Escalate to human intervention
        await self.escalate_to_human(service_name, health_status)
        return {"remediation": "escalated", "attempts": 3}
```

## Module 5: Task Orchestration and Workflows

### 5.1 Complex Workflow Management

**Infrastructure Provisioning Workflow:**
```python
class InfrastructureOrchestrator:
    async def provision_new_environment(self, env_config):
        workflow_id = str(uuid.uuid4())
        
        try:
            # Step 1: Provision compute resources
            compute_result = await self.provision_compute(env_config['compute'])
            
            # Step 2: Setup networking
            network_result = await self.setup_networking(env_config['network'])
            
            # Step 3: Deploy applications
            app_result = await self.deploy_applications(env_config['applications'])
            
            # Step 4: Configure monitoring
            monitoring_result = await self.setup_monitoring(env_config['monitoring'])
            
            # Step 5: Run validation tests
            validation_result = await self.validate_environment(env_config)
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'resources': {
                    'compute': compute_result,
                    'network': network_result,
                    'applications': app_result,
                    'monitoring': monitoring_result
                },
                'validation': validation_result
            }
            
        except Exception as e:
            # Cleanup on failure
            await self.cleanup_partial_environment(workflow_id)
            raise
```

### 5.2 Event-Driven Automation

**Infrastructure Event Processing:**
```python
@dramatiq.actor
def handle_infrastructure_event(event_type, event_data):
    handlers = {
        'server_down': handle_server_failure,
        'high_cpu': handle_resource_alert,
        'disk_full': handle_storage_alert,
        'security_breach': handle_security_incident,
        'deployment_requested': handle_deployment_request
    }
    
    handler = handlers.get(event_type)
    if handler:
        return handler(event_data)
    else:
        logger.warning(f"No handler for event type: {event_type}")

def handle_server_failure(server_data):
    # 1. Immediate response: redirect traffic
    redirect_traffic_from_server(server_data['server_id'])
    
    # 2. Attempt automatic recovery
    restart_server.send(server_data['server_id'])
    
    # 3. If critical server, provision replacement
    if server_data['criticality'] == 'high':
        provision_replacement_server.send(server_data)
    
    # 4. Alert operations team
    send_alert.send('server_failure', server_data)
```

## Hands-On Lab Structure

### Lab 1: FastAPI Infrastructure Dashboard

**Objective**: Build a real-time infrastructure monitoring dashboard with FastAPI

**What You'll Build:**
- Health check API endpoints for multiple services
- WebSocket-based real-time monitoring dashboard
- Background task processing for long-running operations
- Database integration for storing infrastructure metrics

**Skills You'll Learn:**
- FastAPI async endpoints and WebSockets
- Background task processing
- Real-time data streaming
- Infrastructure monitoring patterns

**Your Implementation Tasks:**
1. Create health check endpoints for common services (web, database, cache)
2. Implement WebSocket endpoint for real-time updates
3. Build background tasks for periodic health checks
4. Create a simple HTML dashboard for visualization

### Lab 2: Background Worker System

**Objective**: Implement a robust background task system for infrastructure automation

**What You'll Build:**
- Celery/Dramatiq worker setup with Redis
- Different task types (immediate, scheduled, periodic)
- Task result storage and monitoring
- Error handling and retry mechanisms

**Your Implementation Tasks:**
1. Set up Celery or Dramatiq with Redis
2. Create tasks for common infrastructure operations
3. Implement task scheduling and periodic execution
4. Build task monitoring and result tracking

### Lab 3: Intelligent Health Agent

**Objective**: Create an autonomous health monitoring and remediation system

**What You'll Build:**
- Multi-layer health checking system
- Automatic remediation workflows
- Escalation and alerting mechanisms
- Health metrics and trending analysis

**Your Implementation Tasks:**
1. Implement comprehensive health checking
2. Create remediation workflows with escalation
3. Build alerting and notification system
4. Add health metrics collection and analysis

### Lab 4: Complete Infrastructure Automation Platform

**Objective**: Integrate all components into a production-ready automation platform

**What You'll Build:**
- Unified API for all infrastructure operations
- Event-driven automation workflows
- Configuration management system
- Monitoring and alerting dashboard

**Your Implementation Tasks:**
1. Design and implement unified API architecture
2. Create event-driven workflow orchestration
3. Build configuration management capabilities
4. Integrate comprehensive monitoring and alerting

## Project Structure

Create this directory structure for your hands-on work:

```
Python-Automation-for-Infrastructure/
├── README.md (this file)
├── requirements.txt
├── lab1-fastapi-dashboard/
│   ├── main.py
│   ├── routers/
│   ├── models/
│   ├── static/
│   └── templates/
├── lab2-background-workers/
│   ├── celery_app.py
│   ├── tasks/
│   ├── worker.py
│   └── monitor.py
├── lab3-health-agent/
│   ├── health_checker.py
│   ├── remediator.py
│   ├── alerting.py
│   └── config/
├── lab4-automation-platform/
│   ├── api/
│   ├── workers/
│   ├── workflows/
│   ├── monitoring/
│   └── config/
└── shared/
    ├── database.py
    ├── logging.py
    ├── metrics.py
    └── utils.py
```

## Getting Started

1. **Environment Setup**: Set up Python environment and required services
2. **Basic Concepts**: Study FastAPI and async programming fundamentals
3. **Hands-on Labs**: Complete each lab in sequence, building complexity
4. **Integration Project**: Combine all learnings into final automation platform
5. **Production Deployment**: Deploy and test your automation system

## Success Criteria

You've mastered Python infrastructure automation when you can:
- Build high-performance async APIs with FastAPI
- Implement robust background task processing
- Create intelligent monitoring and remediation systems
- Orchestrate complex infrastructure workflows
- Deploy production-ready automation platforms

Ready to start with Lab 1? Let's build your first FastAPI infrastructure dashboard!
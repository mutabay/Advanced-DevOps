# Prometheus & Observability

This document summarises the key concepts, roadmap, and practice tasks for learning Prometheus observability.
Observability focuses on understanding the internal state of your systems based on the data they produce, which helps determine if your infrastructure is healthy. Prometheus is a core technology for monitoring and observability of systems.

The **Node Exporter** is a component of the Prometheus monitoring ecosystem, used to collect and export information about a node’s (server’s) hardware and operating system in a format that can be read by Prometheus. It is especially useful for providing information about the performance and state of system resources such as CPU, memory, disk, network, and so on.
---

## 1. Prometheus Data Model
Prometheus stores **time series**, identified by:
- **metric name**
- **labels** (key/value pairs)
- **timestamps + values**

Example:http_requests_total{method="GET",status="200"}

Metric types:
- **Counter** → increases only  
- **Gauge** → goes up/down  
- **Histogram** → distributions (e.g., latency)  
- **Summary** → client-side quantiles  

**Key idea:** Labels make queries powerful and flexible.

---

## 2. Custom Exporters
Exporters expose metrics at `/metrics`.  
You can write them in Python/Go.

Example exporter metrics: my_queue_length 42 , my_failures_total 3

**Why:** Lets you monitor your own logic (queues, tasks, latency, domain metrics).

---

## 3. PromQL Basics
Time series data can be stored at any relational database. However, these systems are not developed to store and query large volumes of time series data. Prometheus provide tools to compact and optimize time series data.
PromQL is how you query metrics.

Important functions:
- `rate()` → per-second rate for counters  
- `increase()` → total increase over time  
- `sum by(...)` → grouping  
- `avg`, `max`, `min` → aggregation  
- `topk()` → ranking  

Example: rate(http_requests_total{status=~"5.."}[5m])

---

## 4. Alerting Rules
Alerts are PromQL expressions that detect issues.

Examples: 
HighErrorRate:
expr: rate(http_requests_total{status=~"5.."}[5m]) > 5

HighLatency:
expr: histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) > 0.3


**Purpose:** Notify you when the system is unhealthy.

---

## 5. Recording Rules
Precompute expensive or common PromQL queries.

Example: 
record: job:request_rate:5m
expr: rate(http_requests_total[5m])


**Benefits:**  
- Faster dashboards  
- Faster alerts  
- Less load on Prometheus


---

## 7. Grafana Dashboards (SLO Focus)
Build dashboards for:
- **Latency** (p50/p90/p95/p99)  
- **Error rate**  
- **CPU/Memory saturation**  
- **Node pressure**  
- **OOMKilled events**  
- **Pod restarts**  

**Goal:** Monitor real system health and SLOs.

---

# Prometheus Learning Roadmap

### Phase 1: Basics
- Learn metric types  
- Understand labels and time series  
- Install Prometheus + scrape a target  

### Phase 2: Exporters
- Create a custom Python/Go exporter  
- Expose domain metrics  

### Phase 3: PromQL
- Practice with `rate()`, `increase()`, `sum by()`, and quantiles  

### Phase 4: Alerting
- Create meaningful alert rules  

### Phase 5: Recording Rules
- Optimize frequent queries  

### Phase 6: Grafana
- Build dashboards for SLOs and health metrics  


---

# Summary
Prometheus is built around:
- **Metrics** → exposed by exporters  
- **PromQL** → querying  
- **Alerts** → detect issues  
- **Recording rules** → speed  
- **Grafana dashboards** → visualize health  

---
## Quick Practical Setup

1. Clone this repo and open in VS Code.
2. Make sure Docker Desktop is running.
3. Run `docker compose up --build` in the project folder.
4. Access services:
	- Prometheus: http://localhost:9090
	- Grafana: http://localhost:3000 (admin/admin)
	- Node Exporter: http://localhost:9100/metrics
	- Python Exporter: http://localhost:8000/metrics
5. In Grafana, add Prometheus as a data source (URL: `http://prometheus:9090`).
6. Create a dashboard and visualize the metric `my_queue_length`.

# Prometheus & Observability — Essential Learning Notes

This document summarises the key concepts, roadmap, and practice tasks for mastering Prometheus observability — a core skill for SRE, DevOps, and AIOps work.

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

## 6. Thanos (Optional)
Adds:
- Long-term storage (S3/GCS)  
- Global querying  
- Downsampling  

**Used in production clusters requiring months/years of metrics.**

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

### Phase 7: Thanos (Optional)
- Explore long-term storage and global querying  


---

# Summary
Prometheus is built around:
- **Metrics** → exposed by exporters  
- **PromQL** → querying  
- **Alerts** → detect issues  
- **Recording rules** → speed  
- **Grafana dashboards** → visualize health  
- **Thanos** → scale and long-term retention  

Mastering these gives you a strong foundation for AIOps and SRE work.
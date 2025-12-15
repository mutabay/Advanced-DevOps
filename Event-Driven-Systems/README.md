# Event-Driven Systems Learning Guide

**Goal**: Master event-driven architecture to build scalable, resilient systems that react reliably to events and handle failures gracefully.

## Learning Objectives

By the end of this guide, you will:
- Understand core event-driven concepts and patterns
- Master queues, streams, and consumer groups
- Implement retry logic, dead letter queues, and error handling
- Work hands-on with Kafka and Redis Streams locally
- Design and build production-ready event processing pipelines

## Quick Reference: Key Concepts

### Event-Driven Architecture
- **Events**: Immutable facts about past occurrences (OrderPlaced, UserRegistered)
- **Async Communication**: Non-blocking, loose coupling between services
- **Event vs Command**: Events = past tense notifications, Commands = action requests
- **Delivery Guarantees**: At-most-once (fast), At-least-once (reliable), Exactly-once (complex)

### Redis Streams
- **XADD**: Add events to stream
- **XREADGROUP**: Consumer groups for load balancing
- **Consumer Groups**: Automatic partition assignment and rebalancing
- **Persistent Storage**: Events remain after consumption for replay

### Error Handling Patterns
- **Exponential Backoff**: Progressive retry delays (1s, 2s, 4s, 8s...)
- **Dead Letter Queue**: Separate queue for permanently failed messages
- **Circuit Breaker**: Fail-fast when downstream services degraded
- **Poison Message Detection**: Identify malformed data that breaks processing

### Apache Kafka
- **Topics & Partitions**: Logical streams divided for parallelism
- **Consumer Groups**: Load balancing with partition assignment
- **Offset Management**: Track processing position per consumer group
- **Replication**: Multiple copies across brokers for fault tolerance

### Microservices Event Patterns
- **Event Sourcing**: Store events instead of current state
- **CQRS**: Separate read and write operations
- **Saga Pattern**: Distributed transactions via event choreography
- **Database per Service**: Each service owns its data

### Monitoring Essentials
- **Throughput**: Messages/second produced and consumed
- **Latency**: End-to-end processing time (p50, p95, p99)
- **Consumer Lag**: How far behind consumers are from latest events
- **Error Rate**: Failed processing percentage

## Module 1: Core Concepts & Theory

### What is Event-Driven Architecture (EDA)?

Event-driven architecture is a design pattern where components communicate through the production and consumption of events. Instead of direct API calls, services react to events asynchronously.

**Core Principles:**
- **Decoupling**: Producers and consumers don't need to know about each other
- **Asynchronous**: Non-blocking communication allows for better resource utilization
- **Scalability**: Components can scale independently based on load
- **Resilience**: System continues functioning even if some components fail
- **Event Sovereignty**: Events represent immutable facts that occurred

### 1.1 Traditional vs Event-Driven Communication

**Traditional Synchronous (Request-Response):**
```
[Service A] --HTTP Request--> [Service B]
           <--HTTP Response--
```
- Tight coupling between services
- Blocking operations
- Cascading failures
- Difficult to scale independently

**Event-Driven Asynchronous:**
```
[Service A] --Event--> [Event Broker] --Event--> [Service B]
                                    --Event--> [Service C]
                                    --Event--> [Service D]
```
- Loose coupling
- Non-blocking
- Multiple consumers can react to same event
- Better fault tolerance

### 1.2 Events vs Messages vs Commands - Deep Dive

| Type | Intent | Direction | Timing | Example | Response Expected |
|------|--------|-----------|---------|---------|------------------|
| **EVENT** | Notification of past occurrence | One-to-many | Past tense | "Order was placed" | No |
| **COMMAND** | Request for action | One-to-one | Imperative | "Place order" | Yes/No |
| **MESSAGE** | General communication | Any | Any tense | "Process payment" | Maybe |

**Event Characteristics:**
- **Immutable**: Once created, events cannot be changed
- **Timestamped**: Always include when the event occurred
- **Factual**: Represent something that already happened
- **Rich in context**: Contain all necessary data for consumers


### 1.3 Event Processing Patterns

**1. Simple Event Processing (SEP)**
- Pattern: One event triggers one immediate action
- Use case: User registration → Send welcome email
- Characteristics: Direct, immediate, simple logic

**2. Event Stream Processing (ESP)**
- Pattern: Continuous processing of event sequences
- Use case: Real-time analytics, monitoring dashboards
- Characteristics: Stateful processing, windowing, aggregations

**3. Complex Event Processing (CEP)**
- Pattern: Pattern detection across multiple events
- Use case: Fraud detection, system health monitoring
- Characteristics: Correlation rules, temporal patterns, complex logic

### 1.4 Message Delivery Guarantees

**At-Most-Once Delivery:**
```
Producer → [Message Lost?] → Consumer
```
- Implementation: Send and forget
- Use cases: Metrics, logs, non-critical notifications
- Trade-offs: Fast but may lose data

**At-Least-Once Delivery:**
```
Producer → [Duplicate possible] → Consumer → Deduplication needed
```
- Implementation: Acknowledgments with retries
- Use cases: Financial transactions, critical business events
- Trade-offs: Guaranteed delivery but requires deduplication

**Exactly-Once Delivery:**
```
Producer → [Transactional] → Consumer → [Idempotent processing]
```
- Implementation: Distributed transactions, idempotency keys
- Use cases: Payment processing, inventory updates
- Trade-offs: Strong guarantees but complex and slower


### 1.5 Event Ordering and Partitioning

**Why Ordering Matters:**
```
Event 1: "User created account"      (timestamp: 10:00:00)
Event 2: "User deleted account"      (timestamp: 10:00:01)

Wrong order processing: Delete → Create = Account exists (incorrect)
Correct order processing: Create → Delete = Account deleted (correct)
```

**Partitioning Strategies:**
- **By Entity ID**: All events for user_123 go to same partition
- **By Event Type**: All "order_placed" events go to partition 1
- **By Time Window**: Events grouped by time periods
- **Custom Logic**: Business-specific partitioning rules

## Module 2: Queues vs Streams - Comprehensive Understanding

### 2.1 Queue Model Deep Dive

**Message Queue Characteristics:**
```
[Producer] → [Queue: MSG1, MSG2, MSG3] → [Consumer A takes MSG1]
                   [MSG2, MSG3]      → [Consumer B takes MSG2]
                   [MSG3]            → [Consumer A takes MSG3]
```

**Queue Properties:**
- **Destructive consumption**: Message removed after processing
- **Load balancing**: Work distributed among consumers
- **Temporary storage**: Messages exist until consumed
- **Order preservation**: FIFO within queue
- **Back pressure**: Queue grows if consumers are slow

**Use Cases:**
- Task distribution (job queues)
- Load leveling (handle traffic spikes)
- Work processing (background jobs)

### 2.2 Stream Model Deep Dive

**Event Stream Characteristics:**
```
[Producer] → [Stream: E1, E2, E3, E4, E5, E6] 
                 ↓    ↓    ↓    ↓    ↓    ↓
Consumer Group A: [C1 reads E1,E3,E5] [C2 reads E2,E4,E6]
Consumer Group B: [C3 reads E1,E2,E3,E4,E5,E6]
```

**Stream Properties:**
- **Persistent storage**: Events remain after consumption
- **Multiple consumers**: Many applications can read same stream
- **Position tracking**: Each consumer tracks its position (offset)
- **Replay capability**: Can reprocess from any point
- **Partitioned**: Distributed across multiple partitions

**Use Cases:**
- Event sourcing (audit trails)
- Real-time analytics
- Data replication
- Change data capture

### 2.3 Consumer Groups - Advanced Concepts

**Consumer Group Mechanics:**
```
Stream Partitions:    [P1: E1, E3, E5]  [P2: E2, E4, E6]  [P3: E7, E8, E9]
                           ↓                 ↓                 ↓
Consumer Group A:     [Consumer-1]     [Consumer-2]     [Consumer-3]

If Consumer-2 fails:  [Consumer-1]     [FAILED]         [Consumer-3]
After rebalance:      [Consumer-1: P1,P2]              [Consumer-3: P3]
```

**Key Concepts:**
- **Partition lab**: Each partition assigned to one consumer in group
- **Rebalancing**: Automatic redistribution when consumers join/leave
- **Offset management**: Group tracks progress through stream
- **Parallelism**: Degree of parallelism = number of partitions

**Consumer Group Benefits:**
- **Fault tolerance**: Failed consumers trigger rebalancing
- **Load distribution**: Work spread across available consumers
- **Scalability**: Add/remove consumers dynamically
- **Progress tracking**: Group offset prevents duplicate processing

### 2.4 Event Durability and Retention

**Retention Policies:**
- **Time-based**: Keep events for X days/hours
- **Size-based**: Keep latest X GB of events
- **Compaction**: Keep only latest value for each key

**Storage Considerations:**
- **Replication**: Multiple copies for fault tolerance
- **Compression**: Reduce storage costs
- **Archiving**: Move old events to cheaper storage

## Module 3: Technology Deep Dive

### 3.1 Redis Streams - Internal Architecture

**Redis Streams Structure:**
```
Stream: mystream
├── Entry 1: 1609459200000-0 {field1: value1, field2: value2}
├── Entry 2: 1609459200001-0 {field1: value3, field2: value4}
└── Entry 3: 1609459200002-0 {field1: value5, field2: value6}

Consumer Groups:
├── group1: last_id=1609459200001-0
│   ├── consumer-a: pending=[1609459200002-0]
│   └── consumer-b: pending=[]
└── group2: last_id=1609459200000-0
    └── consumer-c: pending=[1609459200001-0, 1609459200002-0]
```

**Redis Streams Commands:**
- `XADD`: Add entry to stream
- `XREAD`: Read from stream
- `XGROUP`: Manage consumer groups
- `XREADGROUP`: Read as part of consumer group
- `XACK`: Acknowledge message processing
- `XPENDING`: Check pending messages

### 3.2 Apache Kafka - Architecture Overview

**Kafka Cluster Components:**
```
Kafka Cluster:
├── Broker 1 (Leader for Topic-A-Partition-1)
├── Broker 2 (Leader for Topic-A-Partition-2, Follower for Topic-A-Partition-1)
└── Broker 3 (Follower for Topic-A-Partition-1 and Topic-A-Partition-2)

ZooKeeper Cluster:
├── ZK Node 1 (Stores metadata, coordinates brokers)
├── ZK Node 2
└── ZK Node 3
```

**Kafka Concepts:**
- **Topics**: Logical event streams
- **Partitions**: Physical storage units for parallelism
- **Brokers**: Kafka servers that store and serve data
- **Producers**: Applications that publish events
- **Consumers**: Applications that subscribe to events
- 
## Module 4: Local Development Setup

### 4.1 Environment Setup with Podman

```bash
# Create a project network for isolated development
podman network create event-driven-lab

# Redis for streams and basic messaging
podman run -d --name redis-server \
  --network event-driven-lab \
  -p 6379:6379 \
  redis:7-alpine

# Kafka ecosystem (for advanced exercises)
podman run -d --name zookeeper \
  --network event-driven-lab \
  -p 2181:2181 \
  -e ZOOKEEPER_CLIENT_PORT=2181 \
  -e ZOOKEEPER_TICK_TIME=2000 \
  confluentinc/cp-zookeeper:latest

podman run -d --name kafka \
  --network event-driven-lab \
  -p 9092:9092 \
  -e KAFKA_BROKER_ID=1 \
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  confluentinc/cp-kafka:latest
```


### 4.2 Required Python Dependencies

Create a requirements.txt file:
```txt
redis
aioredis
kafka-python
confluent-kafka
asyncio
```

Install dependencies:
```bash
pip install -r requirements.txt
```


**Directory Structure You Should Create:**
```
Event-Driven-Systems/
├── lab-1-redis-basics/
│   ├── producer.py
│   ├── consumer.py
│   └── requirements.txt
├── lab-2-error-handling/
│   ├── advanced_consumer.py
│   ├── dlq_monitor.py
│   └── error_simulator.py
├── lab-3-kafka/
│   ├── kafka_producer.py
│   ├── kafka_consumer.py
│   └── docker-compose.yml
└── lab-4-microservices/
    ├── order_service.py
    ├── inventory_service.py
    ├── notification_service.py
    └── analytics_service.py
```

## Module 5: Practical Lab Guide

### lab 1: Basic Event Producer/Consumer (Redis Streams)

**Goal**: Build your first event-driven system using Redis Streams

### lab 2: Advanced Error Handling & Retry Logic

**Goal**: Implement production-ready error handling patterns

### lab 3: Apache Kafka Deep Dive

**Goal**: Work with enterprise-grade streaming using Apache Kafka

### lab 4: Multi-Service Event Architecture

**Goal**: Design and implement a complete microservices system with event-driven communication

**System Components to Build:**

**1. Order Service (order_service.py):**
- Manages order lifecycle and state transitions
- Publishes: OrderPlaced, OrderConfirmed, OrderCancelled, OrderShipped
- Subscribes to: PaymentProcessed, InventoryReserved, ShipmentCreated

**2. Inventory Service (inventory_service.py):**
- Tracks product availability and reservations
- Publishes: StockUpdated, StockReserved, StockReleased, LowStockAlert
- Subscribes to: OrderPlaced, OrderCancelled

**3. Notification Service (notification_service.py):**
- Handles customer and admin communications
- Publishes: EmailSent, SMSSent, PushNotificationSent
- Subscribes to: All order and inventory events

**4. Analytics Service (analytics_service.py):**
- Real-time metrics and business intelligence
- Publishes: DailyReport, AlertTriggered, MetricUpdated
- Subscribes to: All system events

**Event Schema Design:**
Design comprehensive event schemas with:
- Standard event envelope (id, timestamp, version, source)
- Domain-specific payload structure
- Event versioning strategy
- Backward compatibility considerations

**Integration Patterns:**
- Event sourcing for audit trail
- CQRS for read/write separation
- Saga pattern for distributed transactions
- Event streaming for real-time analytics

## Module 6: Advanced Patterns & Production Considerations

### 6.1 Error Handling Strategy Guide

| Pattern | Use Case | Implementation | Monitoring |
|---------|----------|----------------|------------|
| **Retry with Backoff** | Transient failures | Exponential delays, max attempts | Retry success/failure rates |
| **Dead Letter Queue** | Poison messages | Separate stream/topic for failures | DLQ size and message age |
| **Circuit Breaker** | Downstream failures | Fail-fast when service degraded | Circuit state and trip frequency |
| **Bulkhead** | Resource isolation | Separate thread pools/connections | Resource utilization metrics |

### 6.2 Monitoring & Observability Implementation

**Essential Metrics You Should Track:**
- **Throughput**: Messages produced/consumed per second
- **Latency**: End-to-end processing time (p50, p95, p99)
- **Error Rates**: Processing failures as percentage
- **Consumer Lag**: How far behind consumers are
- **Queue Depth**: Unprocessed message counts

**Monitoring Implementation Approaches:**
- Use Redis streams to capture metrics
- Implement health check endpoints
- Create simple dashboards with real-time data
- Set up alerting thresholds for critical metrics

### 6.3 Performance Optimization Techniques

**Producer Optimizations:**
- Batch message publishing for higher throughput
- Async publishing to reduce blocking
- Connection pooling and reuse
- Message compression when appropriate

**Consumer Optimizations:**
- Parallel processing with multiple workers
- Batch message processing
- Efficient deserialization
- Connection management and pooling

**System-Level Optimizations:**
- Proper partitioning strategies
- Resource allocation and scaling
- Network optimization
- Storage and persistence tuning

## Module 7: Final Project Guidelines

### Capstone Project: Event-Driven Order Management Platform

**Project Overview:**
Build a production-ready order management system that demonstrates mastery of event-driven patterns.

**System Requirements:**
1. **Complete Order Lifecycle**: From placement through delivery
2. **Real-time Inventory**: Stock tracking with reservations
3. **Async Payment Processing**: Payment workflows with retries
4. **Multi-channel Notifications**: Email, SMS, push notifications
5. **Live Analytics**: Real-time dashboards and reporting
6. **Error Recovery**: Comprehensive error handling and recovery

**Technical Implementation Requirements:**
- Use both Redis Streams (for fast operations) and Kafka (for durability)
- Implement all error handling patterns learned
- Include comprehensive monitoring and alerting
- Support horizontal scaling of all components
- Handle realistic load testing scenarios

**Deliverables You Should Create:**
1. **Architecture Document**: System design and event flow diagrams
2. **Event Schema Definitions**: Complete event catalog with examples
3. **Source Code**: All microservices and supporting components
4. **Deployment Guide**: Step-by-step setup instructions
5. **Test Results**: Performance and load testing documentation
6. **Monitoring Dashboard**: Real-time system health visualization

## Assessment Checklist & Learning Validation

### Theory Understanding (Self-Assessment)

**Core Concepts Mastery:**
- [ ] Can explain event-driven architecture benefits and trade-offs
- [ ] Understand differences between queues and streams
- [ ] Know when to use different consistency models
- [ ] Can design appropriate error handling strategies

**Advanced Patterns Knowledge:**
- [ ] Understand event sourcing and CQRS patterns
- [ ] Know how to implement saga patterns for distributed transactions
- [ ] Can design schema evolution strategies
- [ ] Understand performance optimization techniques

### Practical Skills Demonstration

**Basic Implementation Skills:**
- [ ] Successfully implement Redis Streams producer/consumer
- [ ] Build Kafka-based event processing pipeline
- [ ] Create comprehensive error handling with DLQ
- [ ] Implement monitoring and basic alerting

**Advanced Implementation Skills:**
- [ ] Design and build multi-service event architecture
- [ ] Implement exactly-once processing semantics
- [ ] Create real-time analytics and monitoring
- [ ] Handle high-load scenarios with proper scaling

### Bonus Learning Achievements

**Expert-Level Implementations:**
- [ ] Implement custom stream processing logic
- [ ] Build event sourcing with snapshot capabilities
- [ ] Create advanced monitoring dashboards
- [ ] Design fault-tolerant distributed event systems
- [ ] Implement performance optimization techniques

## Study Resources & Next Steps

### Essential Reading Materials
- **"Designing Event-Driven Systems"** by Ben Stopford (Focus: Kafka and streaming)
- **"Building Event-Driven Microservices"** by Adam Bellemare (Focus: Architecture patterns)
- **"Kafka: The Definitive Guide"** by Neha Narkhede (Focus: Deep technical knowledge)
- **Redis Streams Documentation** (Focus: Implementation details)

### Recommended Learning Path After Completion
1. **Distributed Systems Design**: CAP theorem, consensus algorithms, distributed storage
2. **Cloud-Native Event Processing**: Serverless patterns, managed services
3. **Stream Processing Frameworks**: Apache Flink, Kafka Streams, Apache Storm
4. **Event Sourcing Deep Dive**: Advanced patterns and implementation strategies
5. **Observability and Monitoring**: Advanced metrics, tracing, and alerting strategies

### Practical Next Projects
- Build event-driven IoT data processing pipeline
- Implement event sourcing for financial transaction system
- Create real-time recommendation engine with streaming
- Design event-driven CI/CD pipeline
- Build distributed event-driven gaming platform

## Implementation Tips & Best Practices

### Development Workflow Recommendations
1. **Start with Simple Scenarios**: Begin with basic producer/consumer before adding complexity
2. **Design Events First**: Define your event schema before writing code
3. **Implement Error Handling Early**: Don't treat error handling as an afterthought
4. **Test Failure Scenarios**: Always test what happens when things go wrong
5. **Monitor from Day One**: Build observability into your system from the start

### Common Pitfalls to Avoid
- **Event Schema Evolution**: Not planning for schema changes
- **Ordering Dependencies**: Assuming events will be processed in order
- **Error Handling**: Inadequate retry and recovery mechanisms
- **Monitoring Gaps**: Not tracking the right metrics
- **Performance Issues**: Not considering scaling and load patterns

### Success Criteria Summary
You have successfully mastered event-driven systems when you can:
- Design event schemas for complex business domains
- Implement robust error handling and recovery patterns
- Build systems that gracefully handle partial failures
- Monitor and troubleshoot distributed event processing
- Scale event processing systems horizontally
- Choose appropriate technologies for specific use cases
- Architect event-driven microservices systems

**Remember**: Event-driven systems require careful design and thorough testing. Focus on understanding the core principles before implementing complex patterns. Always consider failure modes and design for resilience from the beginning.
```
Event-Driven-Systems/
├── lab1-redis-streams/
│   ├── producer.py
│   ├── consumer.py
│   ├── advanced_consumer.py
│   └── requirements.txt
```
**Learning Objectives:**
- Understand producer/consumer patterns
- Implement consumer groups and load balancing
- Handle event processing with Redis Streams
- Build specialized event processors

**Setup Instructions:**

```bash
# 1. Start Redis with Podman
podman run -d --name redis-server -p 6379:6379 redis:7-alpine

# 2. Install Python dependencies
pip install -r lab1-redis-streams/requirements.txt

# 3. Verify Redis connection
podman exec -it redis-server redis-cli ping
```

**Running the Lab:**

```bash
# Terminal 1: Start the consumer group
cd lab1-redis-streams
python consumer.py

# Terminal 2: Run the event producer
python producer.py

# Terminal 3: Monitor Redis streams
podman exec -it redis-server redis-cli
# In Redis CLI:
XLEN ecommerce_events
XRANGE ecommerce_events - +
```

**What You'll Learn:**
- How consumer groups distribute load automatically
- Event processing patterns in action
- Real-time metrics and analytics
- Inventory management through events

#### Exercise Tasks:

1. **Basic Understanding**: Run producer and consumer, observe load balancing
2. **Scale Testing**: Add more consumers and see automatic rebalancing
3. **Failure Simulation**: Stop one consumer and observe recovery
4. **Custom Processor**: Create a notification processor for user events

---

### Lab 2: Advanced Retry Logic and Dead Letter Queues

**Objective**: Implement production-ready error handling with retry mechanisms and DLQ patterns.

Create: `lab3-advanced-patterns/advanced_consumer.py`
```python
# Key Features:
# - Automatic retry with exponential backoff
# - Dead Letter Queue for failed messages
# - Poison message detection
# - Comprehensive error handling
# - Monitoring and alerting integration
```

---

### Lab 3: Kafka Deep Dive

**Objective**: Master enterprise-grade streaming with Apache Kafka.

**Setup Kafka with Podman:**

```bash
# Start Kafka ecosystem
cd lab2-kafka
podman-compose up -d

# Verify Kafka is running
podman exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

**Learning Objectives:**
- Understand Kafka partitioning and replication
- Implement exactly-once processing
- Master Kafka consumer groups
- Build real-time data pipelines

---

## 🎯 Module 6: Advanced Patterns & Production Considerations

### 6.1 Error Handling Strategies

| Pattern | Use Case | Pros | Cons |
|---------|----------|------|------|
| **Retry with Backoff** | Transient failures | Simple, effective | Can amplify load |
| **Dead Letter Queue** | Poison messages | Prevents blocking | Requires monitoring |
| **Circuit Breaker** | Downstream failures | Protects system | Adds complexity |
| **Bulkhead** | Resource isolation | Limits blast radius | Resource overhead |

### 6.2 Monitoring & Observability

**Essential Metrics:**
- Message throughput (messages/sec)
- Processing latency (p50, p95, p99)
- Error rate (%)
- Consumer lag
- Dead letter queue size

**Alerting Rules:**
```yaml
# Example Prometheus alerts
- alert: HighConsumerLag
  expr: kafka_consumer_lag_sum > 1000
  for: 5m
  
- alert: HighErrorRate
  expr: error_rate > 5
  for: 2m
```

### 6.3 Security Considerations

- **Authentication**: SASL/SCRAM, mTLS
- **Authorization**: ACLs, RBAC
- **Encryption**: TLS in transit, encryption at rest
- **Network Security**: VPCs, firewalls

---

## 🚀 Module 7: Real-World Project

### Final Project: Multi-Service Event-Driven System

**Build a complete microservices system with:**

1. **User Service**: Registration, authentication
2. **Order Service**: Order processing, state management
3. **Inventory Service**: Stock management, reservations
4. **Notification Service**: Email, SMS, push notifications
5. **Analytics Service**: Real-time metrics, reporting

**Architecture Requirements:**
- Event sourcing for audit trails
- CQRS (Command Query Responsibility Segregation)
- Saga pattern for distributed transactions
- Real-time monitoring dashboard

**Technologies Used:**
- Kafka for event streaming
- Redis for caching and temporary storage
- FastAPI for REST APIs
- PostgreSQL for persistent storage
- Grafana + Prometheus for monitoring

---

## 📚 Learning Resources & Next Steps

### Recommended Reading
- "Designing Event-Driven Systems" by Ben Stopford
- "Building Event-Driven Microservices" by Adam Bellemare
- "Kafka: The Definitive Guide" by Neha Narkhede

### Advanced Topics to Explore
- Event Sourcing & CQRS patterns
- Apache Pulsar vs Kafka
- Stream processing with Kafka Streams
- Event mesh architectures
- Serverless event processing

### Certification Paths
- Confluent Certified Developer for Apache Kafka
- AWS Certified Solutions Architect (for SQS/SNS)
- Apache Kafka certification

---

## 🏆 Assessment Checklist

**Theory (40%)**
- [ ] Explain event-driven architecture benefits
- [ ] Compare queues vs streams
- [ ] Describe consumer group mechanics
- [ ] Design retry and error handling strategies

**Practical Skills (60%)**
- [ ] Implement producer/consumer with Redis Streams
- [ ] Build Kafka-based data pipeline
- [ ] Create advanced error handling with DLQ
- [ ] Deploy monitoring and alerting
- [ ] Design microservices event architecture

**Bonus Points**
- [ ] Implement exactly-once processing
- [ ] Build real-time analytics dashboard
- [ ] Create custom Kafka connectors
- [ ] Implement event sourcing pattern

---

## 💡 Tips for Success

1. **Start Simple**: Begin with basic producer/consumer patterns
2. **Think About Failures**: Always design for error scenarios
3. **Monitor Everything**: Observability is crucial in distributed systems
4. **Practice Scaling**: Test your systems under load
5. **Learn from Others**: Study real-world architectures (Netflix, Uber, etc.)

**Remember**: Event-driven systems are powerful but complex. Master the basics first, then gradually add advanced patterns as needed.

---

*Happy Learning! 🎉*
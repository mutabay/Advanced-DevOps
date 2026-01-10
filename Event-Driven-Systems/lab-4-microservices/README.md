# Lab 4: Multi-Service Event Architecture

**Goal**: Master microservices architecture with event-driven communication.

## What Are Microservices?

**Definition**: Architecture pattern that breaks a large application into small, independent services that communicate over a network.

**Key Principles:**
- **Single Responsibility**: Each service does one thing well
- **Independence**: Services can be developed, deployed, and scaled separately
- **Decentralization**: No central database or coordinator
- **Communication**: Services talk via messages, not direct calls

## Traditional vs Event-Driven Communication

### Synchronous Communication (Bad)
```python
# Service A directly calls Service B
result = payment_service.charge_card(order_data)
if result.success:
    inventory_service.reserve_items(order_data)
```

**Problems:**
- **Blocking**: Service A waits for Service B
- **Tight Coupling**: Services know about each other
- **Single Point of Failure**: If B is down, A fails

### Event-Driven Communication (Good)
```python
# Service A publishes event
event_bus.publish("OrderPlaced", order_data)

# Services B and C listen and react independently
```

**Benefits:**
- **Non-blocking**: Services don't wait
- **Loose Coupling**: Services only know about events
- **Resilient**: Service failures don't cascade

## Core Event-Driven Patterns

### 1. Event Sourcing
**Definition**: Store all changes as events instead of current state.

**Traditional Database:**
```sql
users: {id: 1, name: "John", email: "john@email.com"}
```

**Event Sourcing:**
```json
events: [
  {"type": "UserCreated", "name": "John", "email": "old@email.com"},
  {"type": "EmailChanged", "new_email": "john@email.com"}
]
```

**Current State = Replay All Events**

**Benefits:**
- Complete audit trail
- Can rebuild state from events
- Time-travel debugging

### 2. CQRS (Command Query Responsibility Segregation)
**Definition**: Separate read operations from write operations.

```python
# Write Side (Commands)
class OrderService:
    def place_order(self, data):
        # Validate and store event
        event = OrderPlaced(data)
        self.event_store.save(event)

# Read Side (Queries) 
class OrderQueryService:
    def get_orders(self, customer_id):
        # Optimized for reading
        return self.read_db.query(customer_id)
```

**Benefits:**
- Optimize reads and writes separately
- Multiple read models from same events

### 3. Saga Pattern
**Definition**: Manage distributed transactions using a sequence of events and compensating actions.

**Problem**: How to maintain consistency across multiple services without distributed transactions?

**Solution**: Use events to coordinate, with compensating actions for failures.

```
Happy Path:
1. OrderPlaced → 2. PaymentProcessed → 3. StockReserved → 4. OrderConfirmed

Failure Path:
1. OrderPlaced → 2. PaymentFailed → 3. StockReleased → 4. OrderCancelled
```

## Event Design Standards

### Event Structure
```json
{
  "event_id": "uuid-123",
  "event_type": "OrderPlaced",
  "timestamp": "2025-12-15T10:00:00Z",
  "version": "1.0",
  "source": "order-service",
  "correlation_id": "request-456",
  "data": {
    "order_id": "order-789",
    "customer_id": "customer-321",
    "total": 99.99
  }
}
```

### Naming Rules
- **Past tense**: OrderPlaced, PaymentProcessed
- **Specific**: OrderPlaced not OrderEvent  
- **Business language**: Use domain terms

## What We'll Build

### E-commerce System with 6 Services

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│User Service │  │Order Service│  │Inventory Svc│
│             │  │             │  │             │
│- Register   │  │- Place order│  │- Stock mgmt │
│- Login      │  │- Track order│  │- Reserves   │
└─────────────┘  └─────────────┘  └─────────────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
              ┌─────────────┐
              │   KAFKA     │
              │ (Event Bus) │
              └─────────────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│Payment Svc  │  │Notification │  │Analytics Svc│
│             │  │Service      │  │             │
│- Process    │  │- Emails     │  │- Metrics    │
│  payments   │  │- Alerts     │  │- Reports    │
└─────────────┘  └─────────────┘  └─────────────┘
```

### Service Responsibilities

**User Service**: Registration, authentication, profiles
**Order Service**: Order lifecycle, saga coordination  
**Inventory Service**: Stock management, reservations
**Payment Service**: Payment processing, refunds
**Notification Service**: Emails, SMS, alerts
**Analytics Service**: Metrics, reports, dashboards

### Example: Order Flow

**Happy Path:**
```
1. User places order → OrderPlaced event
2. Payment Service → PaymentProcessed event
3. Inventory Service → StockReserved event  
4. Order Service → OrderConfirmed event
```

**Failure Path:**
```
1. User places order → OrderPlaced event
2. Payment Service → PaymentFailed event
3. Inventory Service → StockReleased event (compensating action)
4. Order Service → OrderCancelled event
```

## Key Benefits

**Scalability**: Scale services independently based on load
**Resilience**: Service failures don't cascade
**Maintainability**: Clear boundaries, independent evolution
**Team Independence**: Different teams can own different services


## Project Structure

```
assignment4-microservices/
├── README.md                    # Project documentation
├── docker-compose.yml          # Infrastructure setup
├── test_infrastructure.py      # Infrastructure testing
├── services/                   # Microservices directory
│   ├── __init__.py
│   ├── user-service/
│   ├── order-service/
│   ├── inventory-service/
│   ├── payment-service/
│   ├── notification-service/
│   └── analytics-service/
└── shared/                     # Common code
    ├── __init__.py
    ├── events.py              # Event schemas
    └── base_service.py        # Base service class
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- Podman or Docker
- Git

### 1. Start Infrastructure
```bash
# Start Kafka, Zookeeper, and PostgreSQL databases
podman-compose up -d

# Verify services are running
podman-compose ps
```

### 2. Install Dependencies
```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install kafka-python asyncio python-dotenv psycopg2
```

### 3. Test Infrastructure
```bash
# Test Kafka connectivity and event framework
python test_infrastructure.py
```

### 4. Check Service Status
```bash
# View container logs
podman logs kafka
podman logs zookeeper

# Check Kafka connectivity
podman exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

## Current Implementation Details

### Event Framework (`shared/events.py`)
- **BaseEvent**: Abstract base class with JSON serialization
- **Specific Events**: UserRegistered, OrderPlaced, PaymentProcessed, etc.
- **EventFactory**: Dynamic event creation from JSON data

### Base Service (`shared/base_service.py`)
- **Kafka Integration**: Producer and consumer setup
- **Event Publishing**: Standardized event sending
- **Topic Management**: Automatic topic creation and mapping
- **Error Handling**: Connection retry logic

### Infrastructure (`docker-compose.yml`)
- **Kafka Cluster**: Single-node Kafka with Zookeeper
- **PostgreSQL**: Individual databases per service
- **Network Configuration**: Internal service communication
- **Port Mapping**: Kafka on 9093, PostgreSQL on 5432

## Testing

### Infrastructure Testing
```bash
# Test event publishing and consumption
python test_infrastructure.py
```

### Manual Kafka Testing
```bash
# Connect to Kafka container
podman exec -it kafka bash

# List topics
kafka-topics --list --bootstrap-server localhost:9092

# Create test topic
kafka-topics --create --topic test --bootstrap-server localhost:9092

# Test producer
kafka-console-producer --topic test --bootstrap-server localhost:9092

# Test consumer (in another terminal)
kafka-console-consumer --topic test --from-beginning --bootstrap-server localhost:9092
```

## Troubleshooting

### Common Issues

1. **Kafka Connection Failed**
   ```bash
   # Check if Kafka is running
   podman logs kafka
   
   # Verify port binding
   netstat -ano | findstr :9093
   ```

2. **Python Import Errors**
   ```bash
   # Ensure you're in the project root directory
   cd assignment4-microservices
   
   # Check PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Database Connection Issues**
   ```bash
   # Check PostgreSQL containers
   podman logs assignment4-user-db
   podman logs assignment4-order-db
   ```


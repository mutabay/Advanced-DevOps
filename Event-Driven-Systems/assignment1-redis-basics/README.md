# Assignment 1: Basic Event Producer/Consumer (Redis Streams)

**Goal**: Build your first event-driven system using Redis Streams

**What You Should Create:**
1. **producer.py** - Event generator that publishes events to Redis streams
2. **consumer.py** - Event processor that consumes events from streams

First the events needs to be designed. Let's choose **E-commerce** domain and design these events:
**Event Schema Design:**
```python
# Event envelope (common structure)
{
    "event_id": "uuid",
    "event_type": "order_placed",
    "timestamp": "2023-12-15T10:30:00Z",
    "source": "order_service",
    "version": "1.0",
    "data": {
        # Event-specific payload
    }
}
```

**Events to implement:**
1. **order_placed**: Customer places an order
2. **payment_processed**: Payment completed
3. **inventory_updated**: Stock levels changed
4. **shipment_created**: Order shipped


**Key Learning Points:**
- How to publish events to Redis Streams
- How to consume events with consumer groups
- How to handle event ordering and persistence
- How to implement basic error handling


## Implementation Highlights

**Producer Features:**
- Realistic event data generation with UUIDs
- Multi-threaded async event publishing
- Proper event naming conventions (past tense verbs)
- Event metadata inclusion (id, timestamp, version)
- Simulated real-world timing patterns

**Consumer Features:**
- Consumer groups for automatic load balancing
- Event type-specific processing logic
- Comprehensive error handling with try/catch
- Message acknowledgment after successful processing
- Clean logging and monitoring output

**Base Utilities Created:**
- EventBase class for standardized event creation
- RedisConnection manager with error handling
- EventProducer for simple event publishing
- EventConsumer with handler registration
- EventMonitor for stream statistics
- EventDataGenerators for realistic test data


## Testing Results

**Test Scenarios:**
1. **Basic Flow**: Producer generates events, consumer processes them
2. **Load Balancing**: Multiple consumers automatically balance load
3. **Fault Tolerance**: Consumer failures trigger rebalancing
4. **Message Persistence**: Events remain in streams after consumption
5. **Async Processing**: Multiple event sources publish simultaneously

**Redis Commands Used:**
```bash
# Monitor stream length and contents
XLEN ecommerce:orders
XRANGE ecommerce:orders - + COUNT 5

# Check consumer groups and status
XINFO GROUPS ecommerce:orders
XINFO CONSUMERS ecommerce:orders ecommerce_processors

# Monitor pending messages
XPENDING ecommerce:orders ecommerce_processors
```

# Single-Server Key-Value Store

This project implements a basic single-server key-value store using Python and Flask. It supports GET, PUT, and DELETE operations, concurrent request handling, logging, persistence, and benchmarking.

## Features

- Store key-value pairs using PUT requests
- Retrieve values using GET requests
- Delete key-value pairs using DELETE requests
- Thread-safe concurrent request handling
- Persistent storage using JSON
- Timestamped operation logging
- Benchmarking for throughput and latency
- Graceful error handling

## Installation

1. Create and activate a Python virtual environment.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```
## Run the Server

Start the key-value store server with:

```bash
python server/app.py
```

The server runs on :
```bash
http://127.0.0.1:8080
```

## API Usage

### PUT

```bash
curl -X POST http://127.0.0.1:8080/mykey -H "Content-Type: application/json" -d "{\"value\":\"hello\"}"
```

### GET
```bash
curl http://127.0.0.1:8080/mykey
```

### DELETE
```bash
curl -X DELETE http://127.0.0.1:8080/mykey
```

## Run the Benchmark

Keep the Flask server running in one terminal.

Open a second terminal and run:

```bash
python benchmark/benchmark.py
```
The benchmark reports:
- Total attempted operations
- Successful operations
- Failed operations
- Total execution time
- Throughput in operations per second
- Average latency per operation

## Benchmark Results

Test configuration:

- Threads: 3
- Total operations: 300

Average results across 3 benchmark runs:

- Successful operations: 300
- Failed operations: 0
- Average throughput: 850.49 operations per second
- Average latency: 0.00352 seconds per operation

Best observed run:

- Throughput: 893.85 operations per second
- Average latency: 0.00335 seconds per operation


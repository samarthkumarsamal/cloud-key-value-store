# Single-Server Key-Value Store

This project implements a single-server key-value store using Python, Flask, and Waitress. The server supports storing, retrieving, updating, and deleting key-value pairs through HTTP requests.

The implementation also provides concurrent request handling, thread safety, periodic persistence, timestamped operation logging, error handling, and performance benchmarking.

## Features

- Store and update key-value pairs using PUT
- POST support for compatibility with the provided benchmark
- Retrieve values using GET
- Delete key-value pairs using DELETE
- Thread-safe concurrent request handling
- Periodic persistent storage using JSON
- Automatic recovery of persisted data after restart
- Timestamped operation logging
- Graceful error handling
- Background persistence to reduce request latency
- Asynchronous logging
- Waitress WSGI server
- Persistent HTTP connection support
- Benchmarking for throughput and average latency

## Project Structure

```text
cloud-key-value-store/
│
├── server/
│   └── app.py
│
├── benchmark/
│   └── benchmark.py
│
├── data/
│   └── store.json
│
├── logs/
│   └── operations.log
│
├── .gitignore
├── README.md
├── REPORT.md
└── requirements.txt
```

The `data/store.json` and `logs/operations.log` files are generated during execution and are excluded from Git through `.gitignore`.

## Installation

### 1. Create a virtual environment

```bash
python -m venv venv
```

### 2. Activate the virtual environment

On Windows Command Prompt:

```cmd
venv\Scripts\activate
```

On macOS or Linux:

```bash
source venv/bin/activate
```

### 3. Install the required dependencies

```bash
pip install -r requirements.txt
```

The required packages are:

```text
Flask
requests
waitress
```

## Run the Server

Start the server from the project root directory:

```bash
python server/app.py
```

The server listens on:

```text
http://127.0.0.1:8080
```

The application uses Waitress as the WSGI server.

To verify that the server is running:

```bash
curl http://127.0.0.1:8080/
```

Expected response:

```text
Key-Value Store Server is Running
```

## API Usage

### PUT - Store or Update a Key-Value Pair

```bash
curl -X PUT http://127.0.0.1:8080/mykey -H "Content-Type: application/json" -d "{\"value\":\"hello\"}"
```

Example response:

```json
{
  "key": "mykey",
  "message": "Value Stored Successfully",
  "value": "hello"
}
```

### POST - Benchmark Compatibility

HTTP POST is also supported for storing values so that the server remains compatible with the benchmark provided for the assignment.

```bash
curl -X POST http://127.0.0.1:8080/mykey -H "Content-Type: application/json" -d "{\"value\":\"hello\"}"
```

### GET - Retrieve a Value

```bash
curl http://127.0.0.1:8080/mykey
```

Example response:

```json
{
  "key": "mykey",
  "value": "hello"
}
```

### DELETE - Remove a Key-Value Pair

```bash
curl -X DELETE http://127.0.0.1:8080/mykey
```

Example response:

```json
{
  "key": "mykey",
  "message": "Key Deleted Successfully",
  "value": "hello"
}
```

## Error Handling

Requesting a key that does not exist returns HTTP status code `404`.

Example response:

```json
{
  "error": "Key Not Found"
}
```

Attempting to store a key without providing a `value` returns HTTP status code `400`.

Example response:

```json
{
  "error": "Value is required"
}
```

## Concurrency

The server supports multiple concurrent requests.

A global `threading.Lock` protects the shared in-memory dictionary. This prevents race conditions when multiple requests attempt to read, update, or delete shared data at the same time.

The check and modification of a key during DELETE are performed while holding the same lock to ensure consistency.

## Persistence

The key-value store is primarily maintained in memory for fast access.

When PUT, POST, or DELETE modifies the store, the application marks the data as changed. A background persistence thread periodically saves a snapshot of the dictionary to:

```text
data/store.json
```

The persistence interval is five seconds.

When the server starts, previously persisted data is automatically loaded back into memory.

The persistence mechanism first writes data to a temporary file and then replaces the existing storage file. This reduces the risk of leaving a partially written persistence file.

A final save is also attempted during normal application shutdown if unsaved changes remain.

## Logging

All GET, PUT, POST, and DELETE operations are recorded with timestamps in:

```text
logs/operations.log
```

Logging is handled asynchronously using a queue and background logging thread so that HTTP requests do not need to wait for log-file writes.

Example log entries:

```text
2026-10-05 14:20:00,123 - PUT key=testkey value=testvalue
2026-10-05 14:20:01,234 - GET key=testkey
2026-10-05 14:20:02,345 - DEL key=testkey
2026-10-05 14:20:03,456 - GET failed key=testkey - Key Not Found
```

## Run the Benchmark

Start the server in one terminal:

```bash
python server/app.py
```

Keep the server running.

Open a second terminal from the project root directory and run:

```bash
python benchmark/benchmark.py
```

The final benchmark configuration uses:

```text
Client threads: 3
Total attempted operations: 300
Client-side batching: No
```

Each store and GET operation is sent as an individual HTTP request.

The benchmark uses `requests.Session` to reuse persistent HTTP connections. Connection reuse does not combine operations into batches; every operation remains an independent HTTP request.

## Benchmark Results

### Test Configuration

- Concurrent client threads: 3
- Total HTTP operations per run: 300
- Server: Waitress
- Environment: Local machine using `127.0.0.1`
- Client-side batching: No
- Successful operations per run: 300
- Failed operations per run: 0

### Final Three Benchmark Runs

| Run | Throughput | Average Latency |
| --- | ---: | ---: |
| 1 | 1873.28 operations/sec | 1.5889 ms |
| 2 | 2119.01 operations/sec | 1.4000 ms |
| 3 | 2069.63 operations/sec | 1.4344 ms |

### Average Results

```text
Average Throughput: 2020.64 operations/second
Average Latency: 1.4744 milliseconds/operation
Successful Operations: 300/300
Failed Operations: 0
```

### Best Observed Run

```text
Throughput: 2119.01 operations/second
Average Latency: 1.4000 milliseconds/operation
```

All benchmark runs completed all 300 attempted operations successfully with zero failures.

Because the benchmark runs locally using `127.0.0.1`, the measured latency mainly represents application processing, HTTP handling, thread scheduling, logging, persistence overhead, and local operating-system activity rather than real network latency.

Benchmark performance may vary depending on CPU utilization, operating-system scheduling, filesystem activity, and other background processes.

## Technology Choices

### Python

Python was selected because it provides simple and readable support for networking, threading, JSON processing, logging, and file handling.

### Flask

Flask is used to define HTTP routes, process requests, and generate JSON responses.

### Waitress

Waitress is used as the WSGI server instead of Flask's built-in development server. It supports persistent HTTP connections and provides more appropriate server behavior for the final application.

### Python Dictionary

A Python dictionary is used as the in-memory key-value store because it provides efficient lookup, insertion, update, and deletion operations.

### Threading Lock

A global lock is used to protect shared data during concurrent access and prevent race conditions.

## Assignment Requirements

The implementation provides:

- Standalone server listening on port 8080
- GET operation
- PUT operation
- POST compatibility with the provided benchmark
- DELETE operation
- Concurrent request handling
- Protection against concurrent PUT and DELETE operations
- Periodic persistence to disk
- Recovery of persisted data after restart
- Missing-key error handling
- Invalid-request error handling
- Timestamped operation logging
- Throughput and latency benchmarking
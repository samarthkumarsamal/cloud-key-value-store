# Single-Server Key-Value Store

This project implements a basic single-server key-value store using Python and Flask. It supports storing, retrieving, and deleting key-value pairs through HTTP requests. The implementation also includes concurrent request handling, persistence, operation logging, error handling, and performance benchmarking.

## Features

- Store and update key-value pairs
- Retrieve values using GET requests
- Delete key-value pairs using DELETE requests
- Thread-safe concurrent request handling
- Periodic persistent storage using JSON
- Timestamped operation logging
- Graceful error handling
- Background persistence to reduce request latency
- Asynchronous logging
- Benchmarking for throughput and average latency

## Installation

1. Create a Python virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment.

   On Windows Command Prompt:

   ```bash
   venv\Scripts\activate
   ```

   On macOS or Linux:

   ```bash
   source venv/bin/activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run the Server

Start the key-value store server from the project root directory:

```bash
python server/app.py
```

The server runs locally at:

```text
http://127.0.0.1:8080
```

## API Usage

### Store a Key-Value Pair

The current implementation uses a POST request for storing values so that it remains compatible with the provided benchmark.

```bash
curl -X POST http://127.0.0.1:8080/mykey -H "Content-Type: application/json" -d "{\"value\":\"hello\"}"
```

Example response:

```json
{
  "key": "mykey",
  "message": "Value Stored Successfully",
  "value": "hello"
}
```

### Retrieve a Value

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

### Delete a Key-Value Pair

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

### Missing Key

Requesting a key that does not exist returns an HTTP 404 response:

```json
{
  "error": "Key Not Found"
}
```

## Persistence

The server stores key-value pairs in memory for fast access.

Modified data is periodically saved to:

```text
data/store.json
```

A background persistence thread performs the disk write so that PUT and DELETE requests do not need to wait for file I/O.

When the server starts, previously saved data is loaded back into memory.

## Logging

GET, store, and DELETE operations are recorded with timestamps in:

```text
logs/operations.log
```

Logging is handled asynchronously using a queue and background logging thread to reduce request latency.

## Run the Benchmark

Keep the Flask server running in one terminal.

Open a second terminal from the project root directory and run:

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

### Test Configuration

- Concurrent worker threads: 3
- Total HTTP operations per run: 300
- Environment: Local machine using `127.0.0.1`

### Average Results Across Three Runs

- Successful operations: 300
- Failed operations: 0
- Average throughput: 919.84 operations per second
- Average latency: 0.00323 seconds per operation

### Best Observed Run

- Throughput: 926.85 operations per second
- Average latency: 0.00322 seconds per operation

All three measured benchmark runs completed 300 out of 300 operations successfully with zero failures.

Because the benchmark runs locally, the measured latency mainly reflects application processing and local operating system overhead rather than real network latency.
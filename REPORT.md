# Single-Server Key-Value Store Report

## Introduction

This project implements a basic single-server key-value store using Python and Flask. The server supports PUT, GET, and DELETE operations through HTTP requests. It also includes thread-safe concurrent access, persistent storage using a JSON file, timestamped operation logging, error handling, and benchmarking for throughput and latency.

## Design Decisions and Justification

Python was selected because it is simple, readable, and well suited for building small network applications. Flask was used to implement the HTTP server because it provides lightweight support for REST-style APIs and allows GET, POST, and DELETE routes to be created with minimal complexity.

The key-value data is stored in a Python dictionary because dictionary lookup, insertion, and deletion operations are efficient for a simple in-memory key-value store.

A global threading lock is used to protect the shared dictionary during concurrent access. This prevents race conditions when multiple requests attempt to read, update, or delete shared data at the same time. A single lock was retained because testing showed that it performed better than lock striping for the small number of concurrent benchmark threads used in this assignment.

Persistence is implemented using a background thread that periodically saves the in-memory store to a JSON file. PUT and DELETE requests update the in-memory dictionary and mark the store as modified, while disk writing occurs separately. This reduces request latency because client requests do not need to wait for file I/O. When the server starts, previously saved data is loaded from the JSON file. A final save is also attempted when the application exits normally.

Operation logging is handled asynchronously using a queue and a background logging thread. GET, PUT, and DELETE operations are recorded with timestamps in a log file. Flask access logging was disabled during benchmarking because the application already records its own operation logs, and repeated console output introduced unnecessary performance overhead.

## Challenges Faced

One major challenge was handling concurrent requests safely. Since multiple request threads can access the same shared dictionary, a threading lock was used to prevent conflicting operations and maintain consistent data.

Another challenge was maintaining persistence without reducing server performance. Saving the entire store after every PUT or DELETE increased latency, so persistence was moved to a background thread that saves modified data periodically.

During development, issues were also encountered with Flask startup output, logging configuration, and Python string formatting. These problems were resolved through testing, direct HTTP requests, and incremental code corrections.

## Assumptions

The server is designed to run on a single machine and listen on port 8080. Keys are treated as strings, while values are expected to contain JSON-compatible data.

The persistence mechanism assumes that only one server instance writes to the JSON file. The benchmark is executed locally against the server on the same machine, so the measured latency primarily represents local processing and operating system overhead rather than real network latency.

## Potential Improvements

Future versions could use a database or log-based storage system instead of a JSON file to provide stronger durability, faster recovery, and better scalability. More advanced concurrency mechanisms could also be considered for workloads with a much larger number of simultaneous clients.

Additional features could include authentication, configurable ports, key expiration, replication, distributed storage across multiple servers, and stronger failure recovery. A production WSGI server could also replace the Flask development server for a more realistic deployment environment.

## Benchmark Results

The benchmark was executed using 3 concurrent worker threads and a total of 300 HTTP operations.

Across three benchmark runs, all 300 operations completed successfully with no failures. The average throughput was approximately 850.49 operations per second, and the average latency was approximately 0.00352 seconds per operation.

The best observed run achieved approximately 893.85 operations per second with an average latency of 0.00335 seconds per operation.

These results indicate that the implementation can handle concurrent local requests efficiently while maintaining correct GET, PUT, DELETE, logging, persistence, and error-handling behavior.
# Single-Server Key-Value Store Report

## Introduction

This project implements a basic single-server key-value store using Python and Flask. The server supports storing, retrieving, and deleting key-value pairs through HTTP requests. It also includes thread-safe concurrent access, persistent storage using a JSON file, timestamped operation logging, error handling, and performance benchmarking for throughput and latency.

## Design Decisions and Justification

Python was selected because it is simple, readable, and well suited for developing small network applications. Flask was used to implement the HTTP server because it provides lightweight support for REST-style APIs and allows the required store, retrieve, and delete operations to be implemented with minimal complexity.

The key-value data is stored in a Python dictionary because dictionary lookup, insertion, and deletion operations are efficient for a simple in-memory key-value store. The logical PUT operation is implemented using HTTP POST so that the server remains compatible with the benchmark provided for the assignment.

A global threading lock is used to protect the shared dictionary during concurrent access. This prevents race conditions when multiple requests attempt to read, update, or delete shared data at the same time. A single global lock was retained because testing showed that it performed better than lock striping for the small number of concurrent worker threads used in the benchmark.

Persistence is implemented using a background thread that periodically saves the in-memory store to a JSON file. Store and DELETE operations update the in-memory dictionary and mark the data as modified, while the actual disk write occurs separately. This reduces request latency because client requests do not need to wait for file I/O. When the server starts, previously saved data is loaded from the JSON file. A final save is also attempted when the application exits normally.

Operation logging is handled asynchronously using a queue and a background logging thread. GET, store, and DELETE operations are recorded with timestamps in a log file. Flask access logging was disabled during benchmarking because the application already records its own operation logs and unnecessary console output introduced additional performance overhead.

## Challenges Faced

One major challenge was handling concurrent requests safely. Since multiple request threads can access the same shared dictionary, a threading lock was used to prevent conflicting operations and maintain consistent data.

Another challenge was maintaining persistence without significantly reducing server performance. Saving the complete store after every modification increased latency, so persistence was moved to a background thread that periodically saves modified data.

During development, issues were also encountered with Flask startup output, logging configuration, thread synchronization, and Python string formatting. These problems were resolved through incremental testing and direct HTTP requests.

## Assumptions

The server is designed to run on a single machine and listen on port 8080. Keys are treated as strings, while values are expected to contain JSON-compatible data.

The persistence mechanism assumes that only one server instance writes to the JSON storage file. The benchmark is executed locally against the Flask server using 127.0.0.1, so the measured latency primarily represents application processing and local operating system overhead rather than real network latency.

## Potential Improvements

Future versions could use a database or log-based storage system instead of a JSON file to provide stronger durability, faster recovery, and improved scalability. More advanced concurrency mechanisms could also be considered for workloads with a much larger number of simultaneous clients.

Additional improvements could include authentication, configurable ports, key expiration, replication, distributed storage across multiple servers, stronger failure recovery, and deployment using a production WSGI server instead of the Flask development server.

## Benchmark Results

The benchmark was executed using 3 concurrent worker threads with a total of 300 HTTP operations per run.

Across three benchmark runs, all 300 operations completed successfully with zero failures in every run. The average throughput was approximately 919.84 operations per second, and the average latency was approximately 0.00323 seconds per operation.

The best observed run achieved approximately 926.85 operations per second with an average latency of 0.00322 seconds per operation.

These results indicate that the implementation can handle concurrent local requests efficiently while maintaining correct store, retrieve, delete, logging, persistence, and error-handling behavior.
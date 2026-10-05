# Single-Server Key-Value Store Report

## Design Decisions and Justification

This project implements a single-server key-value store using Python and Flask. The server runs on port 8080 and supports GET, PUT, and DELETE operations for retrieving, storing, and removing key-value pairs. HTTP POST is also supported for storing values so that the application remains compatible with the benchmark provided for the assignment.

The key-value data is maintained in an in-memory Python dictionary because dictionary lookup, insertion, update, and deletion are efficient for a simple key-value store. A global threading lock protects the shared dictionary during concurrent access. This prevents race conditions when multiple requests attempt to read, update, or delete shared data at the same time.

Persistence is implemented using a background thread that periodically saves the in-memory store to a JSON file. PUT and DELETE operations update memory immediately and mark the store as modified, while the disk write is performed separately every five seconds when necessary. Existing data is restored from the JSON file when the server starts.

All GET, PUT, and DELETE operations are recorded with timestamps. Logging is performed asynchronously using a queue and background logging thread so that requests do not need to wait for log-file writes.

Flask is used for API routing and request handling, while Waitress is used as the WSGI server. Waitress provides persistent HTTP connections and more appropriate server behavior for benchmarking than the Flask development server.

## Challenges Faced

The main challenge was safely handling concurrent requests. Since several request threads can access the same dictionary, a threading lock was used to maintain consistent data and safely handle concurrent modifications.

Another challenge was providing persistence without significantly increasing request latency. Writing the complete store to disk after every modification caused unnecessary overhead, so persistence was moved to a background thread.

Performance testing also showed that the Flask development server closed the TCP connection after each request. Replacing it with Waitress allowed persistent connections and reduced connection overhead. Benchmark performance was also less consistent when the project was stored inside a OneDrive synchronized directory. Running the application from a normal local directory reduced background filesystem interference.

## Assumptions

The application runs as a single server on one machine and listens on port 8080. Keys are represented as strings, and values must be JSON-compatible. Only one server instance is expected to write to the persistence file.

The benchmark is executed locally using `127.0.0.1`, so the measured latency mainly represents application processing, HTTP handling, thread scheduling, logging, persistence overhead, and local operating-system activity rather than real network latency.

## Potential Improvements

Future versions could use a database or append-only log instead of a JSON file for stronger durability and faster recovery. Other improvements could include authentication, configurable ports, key expiration, replication, distributed storage, health monitoring, more advanced concurrency control, and percentile-based latency measurements.

## Benchmark Results

The final benchmark used **3 concurrent client threads** and **300 individual HTTP operations per run**. No client-side batching was used. Persistent HTTP connections were reused through `requests.Session`.

| Run | Throughput | Average Latency |
| --- | ---: | ---: |
| 1 | 1873.28 operations/sec | 1.5889 ms |
| 2 | 2119.01 operations/sec | 1.4000 ms |
| 3 | 2069.63 operations/sec | 1.4344 ms |

Across the three runs, the average throughput was approximately **2020.64 operations per second**, with an average latency of approximately **1.4744 milliseconds per operation**.

All **300 attempted operations completed successfully with zero failures** in every run. The best observed run achieved **2119.01 operations per second** with an average latency of **1.4000 milliseconds per operation**.
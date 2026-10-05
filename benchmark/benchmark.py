import threading
import queue
import requests
import time


BASE_URL = "http://127.0.0.1:8080"

# Benchmark configuration
NUM_THREADS = 3
TOTAL_OPS = 300

# Each task performs one POST and one GET
if TOTAL_OPS % 2 != 0:
    raise ValueError("TOTAL_OPS must be an even number")

NUM_TASKS = TOTAL_OPS // 2


# Queue containing key-value tasks
operations_queue = queue.Queue()

# Start synchronization
start_event = threading.Event()

# Main thread + all worker threads
ready_barrier = threading.Barrier(NUM_THREADS + 1)

# Each worker submits its final results here
results_queue = queue.Queue()


def kv_store_operation(session, op_type, key, value=None):
    """
    Perform one individual HTTP request.

    Connection reuse is enabled through requests.Session(),
    but every POST and GET remains a separate request.
    """

    try:
        if op_type == "set":
            response = session.post(
                f"{BASE_URL}/{key}",
                json={"value": value},
                timeout=5
            )

        elif op_type == "get":
            response = session.get(
                f"{BASE_URL}/{key}",
                timeout=5
            )

        else:
            raise ValueError("Invalid operation type")

        response.raise_for_status()
        return True

    except requests.RequestException as error:
        print(
            f"Error during {op_type} operation "
            f"for key '{key}': {error}"
        )
        return False


def worker_thread():
    """
    Each worker uses its own persistent HTTP session.
    """

    session = requests.Session()

    # Ignore proxy settings from the operating system.
    # This is useful for localhost benchmarking.
    session.trust_env = False

    local_latencies = []
    local_successful = 0
    local_failed = 0

    # Signal that this worker is ready.
    ready_barrier.wait()

    # Wait until benchmark timing begins.
    start_event.wait()

    while True:
        try:
            key, value = operations_queue.get_nowait()

        except queue.Empty:
            break

        # -------------------------------------------------
        # POST operation
        # -------------------------------------------------

        start_time = time.perf_counter()

        success = kv_store_operation(
            session,
            "set",
            key,
            value
        )

        latency = time.perf_counter() - start_time

        if success:
            local_successful += 1
            local_latencies.append(latency)
        else:
            local_failed += 1


        # -------------------------------------------------
        # GET operation
        # -------------------------------------------------

        start_time = time.perf_counter()

        success = kv_store_operation(
            session,
            "get",
            key
        )

        latency = time.perf_counter() - start_time

        if success:
            local_successful += 1
            local_latencies.append(latency)
        else:
            local_failed += 1


        operations_queue.task_done()

    session.close()

    # Submit this worker's results once at the end.
    results_queue.put(
        (
            local_successful,
            local_failed,
            local_latencies
        )
    )


# ---------------------------------------------------------
# Create workload
# ---------------------------------------------------------

for i in range(NUM_TASKS):
    key = f"key_{i}"
    value = f"value_{i}"

    operations_queue.put(
        (key, value)
    )


# ---------------------------------------------------------
# Create worker threads
# ---------------------------------------------------------

threads = [
    threading.Thread(target=worker_thread)
    for _ in range(NUM_THREADS)
]


# Start workers before benchmark timing.
for thread in threads:
    thread.start()


# Wait until all workers have initialized their sessions.
ready_barrier.wait()


# ---------------------------------------------------------
# Start benchmark
# ---------------------------------------------------------

benchmark_start = time.perf_counter()

start_event.set()


# Wait for all workers to finish.
for thread in threads:
    thread.join()


benchmark_end = time.perf_counter()

total_time = benchmark_end - benchmark_start


# ---------------------------------------------------------
# Collect results
# ---------------------------------------------------------

successful_ops = 0
failed_ops = 0
all_latencies = []


while not results_queue.empty():
    worker_successful, worker_failed, worker_latencies = (
        results_queue.get()
    )

    successful_ops += worker_successful
    failed_ops += worker_failed
    all_latencies.extend(worker_latencies)


# ---------------------------------------------------------
# Calculate statistics
# ---------------------------------------------------------

if all_latencies:
    average_latency = (
        sum(all_latencies)
        / len(all_latencies)
    )
else:
    average_latency = float("nan")


if total_time > 0:
    throughput = successful_ops / total_time
else:
    throughput = 0


average_latency_ms = average_latency * 1000


# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

print("\nFinal Results:")
print(f"Client threads: {NUM_THREADS}")
print(f"Total attempted operations: {TOTAL_OPS}")
print(f"Successful operations: {successful_ops}")
print(f"Failed operations: {failed_ops}")
print(f"Total time: {total_time:.6f} seconds")

print(
    f"Throughput: "
    f"{throughput:.2f} operations per second"
)

print(
    f"Average Latency: "
    f"{average_latency_ms:.4f} ms per operation"
)
import threading
import queue
import requests
import time

BASE_URL = "http://127.0.0.1:8080"

NUM_THREADS = 3
OPS_PER_THREAD = 100
PRINT_INTERVAL = 3

# Total number of HTTP operations
TOTAL_OPS = NUM_THREADS * OPS_PER_THREAD

# Each task performs one SET and one GET
NUM_TASKS = TOTAL_OPS // 2

operations_queue = queue.Queue()
latencies_queue = queue.Queue()

# Stores every latency for the final result
all_latencies = []
latency_lock = threading.Lock()

# Counters
successful_ops = 0
failed_ops = 0
counter_lock = threading.Lock()

# Used to start all worker threads together
start_event = threading.Event()


def kv_store_operation(op_type, key, value=None):
    try:
        if op_type == "set":
            response = requests.post(
                f"{BASE_URL}/{key}",
                json={"value": value}
            )

        elif op_type == "get":
            response = requests.get(
                f"{BASE_URL}/{key}"
            )

        else:
            raise ValueError("Invalid operation type")

        response.raise_for_status()
        return True

    except Exception as error:
        print(
            f"Error during {op_type} operation "
            f"for key '{key}': {error}"
        )
        return False


def record_operation(success, latency=None):
    global successful_ops, failed_ops

    with counter_lock:
        if success:
            successful_ops += 1
        else:
            failed_ops += 1

    if success and latency is not None:
        latencies_queue.put(latency)

        with latency_lock:
            all_latencies.append(latency)


def worker_thread():
    # Wait until benchmark begins
    start_event.wait()

    while True:
        try:
            key, value = operations_queue.get_nowait()
        except queue.Empty:
            break

        # PUT operation
        start_time = time.time()

        success = kv_store_operation(
            "set",
            key,
            value
        )

        latency = time.time() - start_time

        record_operation(
            success,
            latency if success else None
        )

        # GET operation
        start_time = time.time()

        success = kv_store_operation(
            "get",
            key
        )

        latency = time.time() - start_time

        record_operation(
            success,
            latency if success else None
        )

        operations_queue.task_done()


def monitor_performance():
    last_print = time.time()

    while True:
        time.sleep(PRINT_INTERVAL)

        current_time = time.time()
        elapsed_time = current_time - last_print

        interval_latencies = []

        while not latencies_queue.empty():
            try:
                interval_latencies.append(
                    latencies_queue.get_nowait()
                )
            except queue.Empty:
                break

        if interval_latencies:
            avg_latency = (
                sum(interval_latencies)
                / len(interval_latencies)
            )

            throughput = (
                len(interval_latencies)
                / elapsed_time
            )

            print(
                f"[Last {PRINT_INTERVAL} seconds] "
                f"Throughput: {throughput:.2f} ops/sec, "
                f"Avg Latency: {avg_latency:.5f} sec/op"
            )

        last_print = current_time


# Create SET/GET tasks
for i in range(NUM_TASKS):
    key = f"key_{i}"
    value = f"value_{i}"

    operations_queue.put(
        (key, value)
    )


# Create worker threads
threads = [
    threading.Thread(target=worker_thread)
    for _ in range(NUM_THREADS)
]


# Create monitoring thread
monitoring_thread = threading.Thread(
    target=monitor_performance,
    daemon=True
)

monitoring_thread.start()


# Start benchmark timer
start_time = time.time()

# Allow workers to begin
start_event.set()


# Start worker threads
for thread in threads:
    thread.start()


# Wait for workers to finish
for thread in threads:
    thread.join()


# Calculate total benchmark time
total_time = time.time() - start_time


# Calculate final average latency
with latency_lock:
    if all_latencies:
        average_latency = (
            sum(all_latencies)
            / len(all_latencies)
        )
    else:
        average_latency = float("nan")


# Calculate successful throughput
throughput = (
    successful_ops / total_time
    if total_time > 0
    else 0
)


# Display final results
print("\nFinal Results:")
print(f"Total attempted operations: {TOTAL_OPS}")
print(f"Successful operations: {successful_ops}")
print(f"Failed operations: {failed_ops}")
print(f"Total time: {total_time:.2f} seconds")
print(
    f"Throughput: "
    f"{throughput:.2f} operations per second"
)
print(
    f"Average Latency: "
    f"{average_latency:.5f} seconds per operation"
)
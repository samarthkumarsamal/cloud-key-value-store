from flask import Flask, request, jsonify
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path

import threading
import logging
import queue
import json
import time
import os
import atexit


app = Flask(__name__)


# ---------------------------------------------------------
# Disable Flask/Werkzeug access logging
# ---------------------------------------------------------

# Werkzeug normally prints one console line for every HTTP request.
# Disabling those console messages reduces benchmark overhead.
#
# GET, PUT, and DELETE operations are still recorded separately
# inside logs/operations.log.
logging.getLogger("werkzeug").setLevel(logging.ERROR)


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

# Automatically find the main project directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Persistent key-value storage file.
DATA_FILE = PROJECT_ROOT / "data" / "store.json"

# Operation log file.
LOG_FILE = PROJECT_ROOT / "logs" / "operations.log"

# Periodically save modified data every 5 seconds.
PERSIST_INTERVAL = 5


# Ensure required directories exist.
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# In-memory key-value store
# ---------------------------------------------------------

# Main dictionary used to store key-value pairs in memory.
store = {}

# Protect shared dictionary operations from concurrent access.
store_lock = threading.Lock()


# ---------------------------------------------------------
# Asynchronous logging
# ---------------------------------------------------------

# Request threads place log messages into this queue.
# A separate thread writes them to the log file.
log_queue = queue.Queue()


# Configure file logging.
file_handler = logging.FileHandler(
    LOG_FILE,
    encoding="utf-8"
)

file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(message)s"
    )
)


# Create a dedicated logger for key-value operations.
operation_logger = logging.getLogger(
    "kvstore.operations"
)

operation_logger.setLevel(logging.INFO)

# Prevent duplicate logging through Flask's root logger.
operation_logger.propagate = False

operation_logger.addHandler(
    QueueHandler(log_queue)
)


# Background listener that writes queued messages to disk.
log_listener = QueueListener(
    log_queue,
    file_handler
)

log_listener.start()


# ---------------------------------------------------------
# Persistence
# ---------------------------------------------------------

# Indicates whether PUT or DELETE modified the store.
store_dirty = threading.Event()


def create_store_snapshot():
    """
    Create a consistent copy of the current in-memory store.

    The lock is held only while copying the dictionary.
    Disk I/O occurs after the lock is released.
    """

    with store_lock:
        snapshot = dict(store)

    return snapshot


def save_store():
    """
    Save the current key-value store to disk.
    """

    snapshot = create_store_snapshot()

    # Write to a temporary file first.
    temp_file = str(DATA_FILE) + ".tmp"

    with open(
        temp_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            snapshot,
            file,
            indent=4
        )

    # Atomically replace the previous storage file.
    os.replace(
        temp_file,
        DATA_FILE
    )


def load_store():
    """
    Load previously persisted data when the server starts.
    """

    try:
        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            saved_data = json.load(file)

        if isinstance(saved_data, dict):

            with store_lock:
                store.update(saved_data)

    except FileNotFoundError:
        # Normal when the application is run for the first time.
        pass

    except json.JSONDecodeError:

        operation_logger.warning(
            "Persistence file contains invalid JSON"
        )


def persistence_worker():
    """
    Periodically save modified data in a background thread.

    PUT and DELETE requests do not need to wait for disk I/O.
    """

    while True:

        time.sleep(PERSIST_INTERVAL)

        if store_dirty.is_set():

            # Clear before saving so that any new modification
            # occurring during the save can trigger another cycle.
            store_dirty.clear()

            try:
                save_store()

            except Exception as error:

                # Try saving again during the next cycle.
                store_dirty.set()

                operation_logger.error(
                    f"Persistence error: {error}"
                )


# Restore saved data before serving requests.
load_store()


# Start background persistence.
persistence_thread = threading.Thread(
    target=persistence_worker,
    daemon=True
)

persistence_thread.start()


# ---------------------------------------------------------
# Home endpoint
# ---------------------------------------------------------

@app.route("/")
def home():

    return "Key-Value Store Server is Running"


# ---------------------------------------------------------
# PUT operation
# ---------------------------------------------------------

@app.route("/<key>", methods=["POST"])
def put_value(key):

    data = request.get_json(silent=True)

    # Validate incoming JSON.
    if not data or "value" not in data:

        operation_logger.warning(
            f"PUT failed key={key} - Value is required"
        )

        return jsonify({
            "error": "Value is required"
        }), 400


    value = data["value"]


    # Protect the dictionary while modifying it.
    with store_lock:
        store[key] = value


    # Mark the store as modified.
    # Persistence will happen in the background.
    store_dirty.set()


    # Log the operation asynchronously.
    operation_logger.info(
        f"PUT key={key} value={value}"
    )


    return jsonify({
        "message": "Value Stored Successfully",
        "key": key,
        "value": value
    }), 200


# ---------------------------------------------------------
# GET operation
# ---------------------------------------------------------

@app.route("/<key>", methods=["GET"])
def get_value(key):

    # Protect the dictionary while reading.
    #
    # Keeping GET synchronized makes behavior predictable while
    # PUT and DELETE may be modifying the same dictionary.
    with store_lock:

        if key not in store:

            operation_logger.warning(
                f"GET failed key={key} - Key Not Found"
            )

            return jsonify({
                "error": "Key Not Found"
            }), 404

        value = store[key]


    operation_logger.info(
        f"GET key={key}"
    )


    return jsonify({
        "key": key,
        "value": value
    }), 200


# ---------------------------------------------------------
# DELETE operation
# ---------------------------------------------------------

@app.route("/<key>", methods=["DELETE"])
def delete_value(key):

    # Check and delete while holding the same lock.
    # This prevents another request from modifying the key
    # between the existence check and deletion.
    with store_lock:

        if key not in store:

            operation_logger.warning(
                f"DEL failed key={key} - Key Not Found"
            )

            return jsonify({
                "error": "Key Not Found"
            }), 404

        deleted_value = store.pop(key)


    # Persist the change later in the background.
    store_dirty.set()


    operation_logger.info(
        f"DEL key={key}"
    )


    return jsonify({
        "message": "Key Deleted Successfully",
        "key": key,
        "value": deleted_value
    }), 200


# ---------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------

def shutdown_handler():
    """
    Save unsaved changes and flush queued logs when Python
    exits normally.
    """

    try:

        if store_dirty.is_set():
            save_store()

    except Exception:
        pass


    try:
        log_listener.stop()

    except Exception:
        pass


atexit.register(shutdown_handler)


# ---------------------------------------------------------
# Start Flask server
# ---------------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=8080,

        # Debug mode and automatic reloading add unnecessary
        # overhead during benchmarking.
        debug=False,

        # Allows Flask to process multiple requests concurrently.
        threaded=True
    )
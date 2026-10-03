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

# Disable Flask access logs to reduce benchmark console overhead.
# GET, PUT, and DELETE are still logged in operations.log.
logging.getLogger("werkzeug").setLevel(logging.ERROR)


# Project file locations
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "store.json"
LOG_FILE = PROJECT_ROOT / "logs" / "operations.log"

PERSIST_INTERVAL = 5

DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


# In-memory key-value store shared by all requests
store = {}

# Prevent concurrent requests from modifying shared data at the same time
store_lock = threading.Lock()


# Asynchronous logging prevents requests from waiting for log file writes
log_queue = queue.Queue()

file_handler = logging.FileHandler(
    LOG_FILE,
    encoding="utf-8"
)

file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(message)s")
)

operation_logger = logging.getLogger("kvstore.operations")
operation_logger.setLevel(logging.INFO)
operation_logger.propagate = False

operation_logger.addHandler(
    QueueHandler(log_queue)
)

log_listener = QueueListener(
    log_queue,
    file_handler
)

log_listener.start()


# Tracks whether PUT or DELETE changed the store
store_dirty = threading.Event()


def create_store_snapshot():
    # Copy the store while holding the lock, then release it
    # before performing slower disk operations.
    with store_lock:
        return dict(store)


def save_store():
    snapshot = create_store_snapshot()

    # Write to a temporary file first to reduce corruption risk
    temp_file = str(DATA_FILE) + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(snapshot, file, indent=4)

    os.replace(temp_file, DATA_FILE)


def load_store():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            saved_data = json.load(file)

        if isinstance(saved_data, dict):
            with store_lock:
                store.update(saved_data)

    except FileNotFoundError:
        # No saved data exists during the first run
        pass

    except json.JSONDecodeError:
        operation_logger.warning(
            "Persistence file contains invalid JSON"
        )


def persistence_worker():
    # Save changed data periodically instead of during every request
    while True:
        time.sleep(PERSIST_INTERVAL)

        if store_dirty.is_set():
            store_dirty.clear()

            try:
                save_store()

            except Exception as error:
                # Retry during the next persistence cycle
                store_dirty.set()

                operation_logger.error(
                    f"Persistence error: {error}"
                )


# Restore previously saved data
load_store()


# Start background persistence thread
persistence_thread = threading.Thread(
    target=persistence_worker,
    daemon=True
)

persistence_thread.start()


@app.route("/")
def home():
    return "Key-Value Store Server is Running"


@app.route("/<key>", methods=["POST"])
def put_value(key):
    data = request.get_json(silent=True)

    if not data or "value" not in data:
        operation_logger.warning(
            f"PUT failed key={key} - Value is required"
        )

        return jsonify({
            "error": "Value is required"
        }), 400

    value = data["value"]

    # PUT modifies shared data, so it is protected by the lock
    with store_lock:
        store[key] = value

    store_dirty.set()

    operation_logger.info(
        f"PUT key={key} value={value}"
    )

    return jsonify({
        "message": "Value Stored Successfully",
        "key": key,
        "value": value
    }), 200


@app.route("/<key>", methods=["GET"])
def get_value(key):
    # Synchronize reads with concurrent PUT and DELETE operations
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


@app.route("/<key>", methods=["DELETE"])
def delete_value(key):
    # Checking and deleting under the same lock avoids race conditions
    with store_lock:
        if key not in store:
            operation_logger.warning(
                f"DEL failed key={key} - Key Not Found"
            )

            return jsonify({
                "error": "Key Not Found"
            }), 404

        deleted_value = store.pop(key)

    store_dirty.set()

    operation_logger.info(
        f"DEL key={key}"
    )

    return jsonify({
        "message": "Key Deleted Successfully",
        "key": key,
        "value": deleted_value
    }), 200


def shutdown_handler():
    # Save pending changes and flush queued log messages before exit
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


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8080,
        debug=False,
        threaded=True
    )
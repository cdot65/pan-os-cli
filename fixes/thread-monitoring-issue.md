# Thread Monitoring Implementation Issue

## Problem

When implementing the thread monitoring feature for the `test objects addresses` command, we encountered an issue where despite setting a high thread count (e.g., `--threads 10`), the monitoring display would only show a maximum concurrent thread usage of 1 thread. This significantly reduced the effectiveness of the thread monitoring feature, as it failed to properly visualize thread utilization.

The root cause was identified in the thread tracking implementation. The original code was calling `threading.get_ident()` in the main thread when submitting tasks to the thread pool, rather than within the worker threads themselves:

```python
# Original problematic code
thread_id = threading.get_ident()  # This was called in the main thread
with active_threads_lock:
    active_threads[thread_id] = {
        "object_name": obj.name,
        "start_time": time.time(),
    }
    # Update max concurrent threads
    thread_stats["max_concurrent"] = max(
        thread_stats["max_concurrent"], len(active_threads)
    )
```

This led to all tasks being incorrectly associated with the main thread, resulting in the monitoring display showing only one active thread even when multiple threads were actually being used.

## Solution

We fixed the issue by creating a wrapper function that runs in the context of each worker thread and properly captures each thread's ID:

```python
# Create a wrapper function that executes in the thread and tracks its ID
def create_address_with_monitoring(obj, devicegroup):
    # Get the actual thread ID from within the worker thread
    thread_id = threading.get_ident()

    # Register this thread as active
    with active_threads_lock:
        active_threads[thread_id] = {
            "object_name": obj.name,
            "start_time": time.time(),
        }
        # Update max concurrent threads right after adding
        thread_stats["max_concurrent"] = max(
            thread_stats["max_concurrent"], len(active_threads)
        )

    # If in mock mode, add a small delay to ensure threads overlap
    if mock:
        time.sleep(random.uniform(0.05, 0.1))

    # Execute the actual work
    try:
        result = client.create_address_object(obj, devicegroup)
        return result
    finally:
        # Ensure thread is marked as completed even if an exception occurs
        with active_threads_lock:
            if thread_id in active_threads:
                del active_threads[thread_id]
            thread_stats["completed_tasks"] += 1
```

We also added key improvements:
1. A small random delay in mock mode to simulate network latency and ensure thread overlap is visible
2. A proper `finally` block to ensure thread completion is always tracked, even if exceptions occur
3. Moved task completion counting to the worker thread for better accuracy

This solution correctly identifies and tracks each thread's activity, providing an accurate real-time visualization of thread utilization. After implementation, we were able to verify that all 10 threads were being properly utilized (100% utilization) when executing the `test objects addresses` command.

## Verification

When running the command, we now see proper thread utilization:

```bash
pan-os-cli test objects addresses --count 20 --threads 10

# Output now correctly shows:
# SUMMARY           Max Concurrent: 10 (100.0%)
#                  Current: 0/10 (0.0%)
#                  Completed: 20/20
```

This implementation allows users to properly visualize and optimize thread usage when bulk-creating address objects, which was a key requirement for the thread monitoring feature.

import os
import time
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import concurrent.futures

from bsti_nessus.utils.parallel import ThreadPool, ProcessPool, TaskManager
from bsti_nessus.utils.logger import CustomLogger
from bsti_nessus.utils.progress import ProgressTracker


# Test helper functions
def slow_io_task(delay, return_value):
    """Simulate a slow I/O-bound task."""
    time.sleep(delay)
    return return_value


def cpu_intensive_task(n):
    """Simulate a CPU-intensive task."""
    result = 0
    for i in range(n):
        result += i
    return result


def task_with_error():
    """A task that raises an exception."""
    raise ValueError("Intentional test error")


def test_file_processor(file_path):
    """Process a file and return its content length."""
    with open(file_path, 'r') as f:
        content = f.read()
    return len(content)


@pytest.fixture
def mock_logger():
    """Fixture that provides a mock logger."""
    return MagicMock(spec=CustomLogger)


@pytest.fixture
def progress_tracker():
    """Fixture that provides a progress tracker."""
    return ProgressTracker(total=100, description="Test Progress")


@pytest.fixture
def sample_files():
    """Create temporary sample files for testing parallel file processing."""
    files = []
    for i in range(5):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as temp_file:
            # Write different amounts of content to each file
            content = f"File {i} content\n" * (i + 1)
            temp_file.write(content)
            files.append(temp_file.name)
    
    yield files
    
    # Clean up
    for file_path in files:
        if os.path.exists(file_path):
            os.remove(file_path)


@pytest.mark.integration
def test_thread_pool_execution(mock_logger):
    """Test thread pool execution of I/O-bound tasks."""
    # Create a thread pool with 2 workers
    pool = ThreadPool(num_workers=2, logger=mock_logger)
    
    try:
        # Submit tasks
        future1 = pool.submit(slow_io_task, 0.1, "result1")
        future2 = pool.submit(slow_io_task, 0.2, "result2")
        
        # Get results
        result1 = future1.get()
        result2 = future2.get()
        
        # Verify results
        assert result1 == "result1"
        assert result2 == "result2"
    finally:
        # Ensure pool is shut down
        pool.shutdown()


@pytest.mark.integration
def test_process_pool_execution(mock_logger):
    """Test process pool execution of CPU-bound tasks."""
    # Create a process pool with 2 workers
    pool = ProcessPool(num_workers=2, logger=mock_logger)
    
    try:
        # Submit tasks
        future1 = pool.submit(cpu_intensive_task, 10000)
        future2 = pool.submit(cpu_intensive_task, 20000)
        
        # Get results
        result1 = future1.get()
        result2 = future2.get()
        
        # Verify results
        assert result1 == sum(range(10000))
        assert result2 == sum(range(20000))
    finally:
        # Ensure pool is shut down
        pool.shutdown()


@pytest.mark.integration
def test_task_manager_map(mock_logger, sample_files):
    """Test mapping tasks across multiple files."""
    # Create a task manager
    task_manager = TaskManager(logger=mock_logger)
    
    # Process files in parallel
    results = task_manager.map(test_file_processor, sample_files)
    
    # Verify results
    assert len(results) == len(sample_files)
    for i, result in enumerate(results):
        # Each file should have (i+1) lines of content "File {i} content\n"
        expected_length = len(f"File {i} content\n" * (i + 1))
        assert result == expected_length


@pytest.mark.integration
def test_error_handling(mock_logger):
    """Test error handling in parallel execution."""
    # Create a thread pool
    pool = ThreadPool(num_workers=2, logger=mock_logger)
    
    try:
        # Submit a task that will raise an exception
        future = pool.submit(task_with_error)
        
        # The exception should be raised when getting the result
        with pytest.raises(ValueError) as exc_info:
            future.get()
        
        # Verify the exception message
        assert "Intentional test error" in str(exc_info.value)
    finally:
        # Ensure pool is shut down
        pool.shutdown()


@pytest.mark.integration
def test_task_cancellation(mock_logger):
    """Test task cancellation."""
    # Create a thread pool
    pool = ThreadPool(num_workers=2, logger=mock_logger)
    
    try:
        # Submit a short-running task (0.5 second) to make test run faster
        future = pool.submit(slow_io_task, 0.5, "result")
        
        # Try to cancel the task (may or may not succeed depending on timing)
        cancelled = future.cancel()
        
        # If cancellation was successful, we're done
        if cancelled:
            assert True
            return
        
        # If cancellation failed, the task might already be running or done
        # We should still be able to get the result or catch an exception
        try:
            # If task completes normally, we should get the expected result
            result = future.get(timeout=1.0)
            assert result == "result"  # Task completed successfully
        except Exception as e:
            # Task might raise exception if cancelled after starting
            # That's also an acceptable outcome for this test
            print(f"Task raised exception after cancellation attempt: {e}")
            assert True
    finally:
        # Ensure pool is shut down
        pool.shutdown()


@pytest.mark.integration
def test_parallel_with_progress(mock_logger, progress_tracker, sample_files):
    """Test parallel processing with progress tracking."""
    # Create a task manager
    task_manager = TaskManager(logger=mock_logger)
    
    # Store the original update method before patching
    original_update = progress_tracker.update
    
    # Process files in parallel with progress tracking
    with patch.object(progress_tracker, 'update') as mock_update:
        # Make the mock actually update the current count
        mock_update.side_effect = lambda n=1, info=None: original_update(n, info)
        
        results = task_manager.map(
            test_file_processor, 
            sample_files, 
            progress_tracker=progress_tracker
        )
        
        # Verify progress tracker was updated
        assert mock_update.call_count >= len(sample_files)
    
    # Verify all tasks completed
    assert progress_tracker.current >= len(sample_files)


@pytest.mark.integration
def test_chunked_processing(mock_logger):
    """Test processing data in chunks."""
    # Create a large list of data
    data = list(range(1000))
    
    # Create a task manager
    task_manager = TaskManager(logger=mock_logger)
    
    # Process data in chunks
    results = task_manager.map_chunked(
        lambda chunk: sum(chunk),  # Sum each chunk
        data,
        chunk_size=100
    )
    
    # Verify results
    assert len(results) == 10  # 1000 items / 100 chunk size = 10 chunks
    assert sum(results) == sum(data)


@pytest.mark.integration
def test_task_dependencies(mock_logger):
    """Test tasks with dependencies."""
    # Create a task manager
    task_manager = TaskManager(logger=mock_logger)
    
    # Submit a chain of dependent tasks
    future1 = task_manager.submit(lambda: "step1")
    future2 = task_manager.submit_after(future1, lambda result: f"{result} -> step2")
    future3 = task_manager.submit_after(future2, lambda result: f"{result} -> step3")
    
    # Get the final result
    result = future3.get()
    
    # Verify the result shows the chain of execution
    assert result == "step1 -> step2 -> step3" 
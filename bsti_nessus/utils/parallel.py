"""
Parallel processing utilities for BSTI Nessus to Plextrac converter.

This module provides thread and process pools for parallel execution of tasks,
with integration for progress tracking and error handling.
"""
import os
import math
import logging
import concurrent.futures
from typing import List, Callable, Any, Dict, Iterable, Optional, TypeVar, Union, Tuple, Generic

from bsti_nessus.utils.logger import CustomLogger
from bsti_nessus.utils.progress import ProgressTracker

# Type variables for generics
T = TypeVar('T')
R = TypeVar('R')


class Future(Generic[R]):
    """
    A class representing the result of an asynchronous computation.
    """
    
    def __init__(self, future: concurrent.futures.Future):
        """
        Initialize a Future wrapper around a concurrent.futures.Future.
        
        Args:
            future: The concurrent.futures.Future to wrap
        """
        self._future = future
        self._cancelled = False
    
    def cancel(self) -> bool:
        """
        Attempt to cancel the task.
        
        Returns:
            True if the task was successfully cancelled, False otherwise
        """
        result = self._future.cancel()
        if result:
            self._cancelled = True
        return result
    
    def cancelled(self) -> bool:
        """
        Return True if the task was cancelled.
        """
        return self._cancelled or self._future.cancelled()
    
    def running(self) -> bool:
        """
        Return True if the task is currently running.
        """
        return self._future.running()
    
    def done(self) -> bool:
        """
        Return True if the task is done executing or was cancelled.
        """
        return self._cancelled or self._future.done()
    
    def get(self, timeout: Optional[float] = None) -> R:
        """
        Return the result of the task.
        
        Args:
            timeout: The maximum number of seconds to wait for the result
            
        Returns:
            The result of the task
            
        Raises:
            Exception: If the task raised an exception
            concurrent.futures.TimeoutError: If the task did not complete within the timeout
            concurrent.futures.CancelledError: If the task was cancelled
        """
        if self._cancelled:
            raise concurrent.futures.CancelledError()
        return self._future.result(timeout)


def chunk_items(items: List[T], chunk_size: Optional[int] = None, num_chunks: Optional[int] = None) -> List[List[T]]:
    """
    Split a list of items into chunks.

    Args:
        items: The list of items to split
        chunk_size: The size of each chunk (takes precedence over num_chunks)
        num_chunks: The number of chunks to create

    Returns:
        A list of chunks (lists)
    """
    if not items:
        return []

    total_items = len(items)
    
    if chunk_size is None and num_chunks is None:
        # Default to CPU count if neither parameter is provided
        num_chunks = os.cpu_count() or 4
    
    if chunk_size is not None:
        # Calculate number of chunks based on chunk size
        num_chunks = math.ceil(total_items / chunk_size)
    else:
        # Calculate chunk size based on number of chunks
        chunk_size = math.ceil(total_items / num_chunks)
    
    # Create chunks
    return [items[i:i + chunk_size] for i in range(0, total_items, chunk_size)]


class ThreadPool:
    """
    Thread pool for parallel execution of I/O-bound tasks.
    
    This class provides a simple interface for executing tasks in parallel
    using a thread pool, with optional progress tracking.
    """
    
    def __init__(
        self, 
        num_workers: Optional[int] = None, 
        thread_name_prefix: str = "bsti-thread",
        logger: Optional[CustomLogger] = None
    ):
        """
        Initialize a thread pool.
        
        Args:
            num_workers: Maximum number of worker threads (defaults to CPU count * 5)
            thread_name_prefix: Prefix for thread names
            logger: Optional logger instance
        """
        if num_workers is None:
            # For I/O-bound tasks, we can use more threads than CPU cores
            cpu_count = os.cpu_count() or 4
            num_workers = cpu_count * 5
        
        self.num_workers = num_workers
        self.thread_name_prefix = thread_name_prefix
        self.logger = logger or logging.getLogger(__name__)
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=num_workers,
            thread_name_prefix=thread_name_prefix
        )
        self.logger.debug(f"Initialized ThreadPool with {num_workers} workers")
    
    def submit(self, func: Callable[..., R], *args, **kwargs) -> Future[R]:
        """
        Submit a task to the thread pool.
        
        Args:
            func: The function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            A Future representing the execution of the task
        """
        future = self.executor.submit(func, *args, **kwargs)
        return Future(future)
    
    def map(
        self, 
        func: Callable[[T], R], 
        items: List[T], 
        show_progress: bool = True,
        progress_tracker: Optional[ProgressTracker] = None,
        progress_description: str = "Processing",
        chunk_items_first: bool = False,
        chunk_size: Optional[int] = None
    ) -> List[R]:
        """
        Apply a function to each item in a list, in parallel.
        
        Args:
            func: The function to apply to each item
            items: The list of items to process
            show_progress: Whether to show a progress bar
            progress_tracker: Optional progress tracker instance
            progress_description: Description for the progress bar
            chunk_items_first: Whether to chunk items before processing
            chunk_size: Size of chunks (if chunking)
            
        Returns:
            A list of results from applying the function to each item
        """
        if not items:
            return []
        
        total_items = len(items)
        self.logger.debug(f"Threading {total_items} items with {self.num_workers} workers")
        
        # Create progress tracker if needed
        if show_progress and progress_tracker is None:
            progress_tracker = ProgressTracker(
                description=progress_description,
                total=total_items,
                unit="items"
            )
        
        # Prepare items
        if chunk_items_first and total_items > self.num_workers:
            chunked_items = chunk_items(items, chunk_size=chunk_size, num_chunks=self.num_workers)
            
            # Define a wrapper function to process chunks
            def process_chunk(chunk: List[T]) -> List[R]:
                results = []
                for item in chunk:
                    result = func(item)
                    results.append(result)
                    if progress_tracker:
                        progress_tracker.update(1)
                return results
            
            # Process chunks in parallel
            futures = [self.submit(process_chunk, chunk) for chunk in chunked_items]
            
            # Collect results
            results = []
            for future in futures:
                try:
                    chunk_results = future.get()
                    results.extend(chunk_results)
                except Exception as e:
                    self.logger.error(f"Error processing chunk: {str(e)}")
                    raise
            
            return results
        else:
            # Process individual items in parallel
            futures = {}
            for item in items:
                future = self.submit(func, item)
                futures[future] = item
            
            # Collect results
            results = []
            for future in futures:
                try:
                    result = future.get()
                    results.append(result)
                    if progress_tracker:
                        progress_tracker.update(1)
                except Exception as e:
                    item = futures[future]
                    self.logger.error(f"Error processing item {item}: {str(e)}")
                    raise
            
            return results
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the thread pool.
        
        Args:
            wait: Whether to wait for all tasks to complete
        """
        self.executor.shutdown(wait=wait)


class ProcessPool:
    """
    Process pool for parallel execution of CPU-bound tasks.
    
    This class provides a simple interface for executing tasks in parallel
    using a process pool, with optional progress tracking.
    """
    
    def __init__(
        self, 
        num_workers: Optional[int] = None,
        logger: Optional[CustomLogger] = None
    ):
        """
        Initialize a process pool.
        
        Args:
            num_workers: Maximum number of worker processes (defaults to CPU count)
            logger: Optional logger instance
        """
        self.num_workers = num_workers or os.cpu_count() or 4
        self.logger = logger or logging.getLogger(__name__)
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=self.num_workers)
        self.logger.debug(f"Initialized ProcessPool with {self.num_workers} workers")
    
    def submit(self, func: Callable[..., R], *args, **kwargs) -> Future[R]:
        """
        Submit a task to the process pool.
        
        Args:
            func: The function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            A Future representing the execution of the task
        """
        future = self.executor.submit(func, *args, **kwargs)
        return Future(future)
    
    def map(
        self, 
        func: Callable[[T], R], 
        items: List[T], 
        show_progress: bool = True,
        progress_tracker: Optional[ProgressTracker] = None,
        progress_description: str = "Processing",
        chunk_items_first: bool = True,
        chunk_size: Optional[int] = None
    ) -> List[R]:
        """
        Apply a function to each item in a list, in parallel.
        
        Args:
            func: The function to apply to each item
            items: The list of items to process
            show_progress: Whether to show a progress bar
            progress_tracker: Optional progress tracker instance
            progress_description: Description for the progress bar
            chunk_items_first: Whether to chunk items before processing
            chunk_size: Size of chunks (if chunking)
            
        Returns:
            A list of results from applying the function to each item
        """
        if not items:
            return []
        
        total_items = len(items)
        self.logger.debug(f"Processing {total_items} items with {self.num_workers} processes")
        
        # Create progress tracker if needed
        if show_progress and progress_tracker is None:
            progress_tracker = ProgressTracker(
                description=progress_description,
                total=total_items,
                unit="items"
            )
        
        # For processes, we almost always want to chunk to reduce overhead
        if chunk_items_first and total_items > self.num_workers:
            chunked_items = chunk_items(items, chunk_size=chunk_size, num_chunks=self.num_workers)
            
            # Process chunks in parallel
            futures = [self.submit(func, chunk) for chunk in chunked_items]
            
            # Collect results
            results = []
            for future in futures:
                try:
                    chunk_result = future.get()
                    results.append(chunk_result)
                    if progress_tracker:
                        progress_tracker.update(len(chunk_result))
                except Exception as e:
                    self.logger.error(f"Error processing chunk: {str(e)}")
                    raise
            
            return [item for sublist in results for item in sublist]  # Flatten results
        else:
            # Process individual items in parallel
            futures = {}
            for item in items:
                future = self.submit(func, item)
                futures[future] = item
            
            # Collect results
            results = []
            for future in futures:
                try:
                    result = future.get()
                    results.append(result)
                    if progress_tracker:
                        progress_tracker.update(1)
                except Exception as e:
                    item = futures[future]
                    self.logger.error(f"Error processing item {item}: {str(e)}")
                    raise
            
            return results
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the process pool.
        
        Args:
            wait: Whether to wait for all tasks to complete
        """
        self.executor.shutdown(wait=wait)


class TaskManager:
    """
    Manager for task execution, with support for thread and process pools.
    
    This class provides a unified interface for executing tasks in parallel,
    choosing the appropriate pool based on the task type.
    """
    
    def __init__(
        self, 
        num_threads: Optional[int] = None,
        num_processes: Optional[int] = None,
        logger: Optional[CustomLogger] = None
    ):
        """
        Initialize the task manager.
        
        Args:
            num_threads: Number of worker threads (defaults to CPU count * 5)
            num_processes: Number of worker processes (defaults to CPU count)
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.thread_pool = ThreadPool(num_workers=num_threads, logger=self.logger)
        self.process_pool = ProcessPool(num_workers=num_processes, logger=self.logger)
        self.logger.debug("Initialized TaskManager")
    
    def submit(self, func: Callable[..., R], *args, use_process: bool = False, **kwargs) -> Future[R]:
        """
        Submit a task for execution.
        
        Args:
            func: The function to execute
            *args: Positional arguments to pass to the function
            use_process: Whether to use a process pool instead of a thread pool
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            A Future representing the execution of the task
        """
        if use_process:
            return self.process_pool.submit(func, *args, **kwargs)
        else:
            return self.thread_pool.submit(func, *args, **kwargs)
    
    def submit_after(
        self, 
        dependency: Future[T], 
        func: Callable[[T], R], 
        use_process: bool = False
    ) -> Future[R]:
        """
        Submit a task to run after another task completes.
        
        Args:
            dependency: The Future representing the task to wait for
            func: The function to execute with the result of the dependency
            use_process: Whether to use a process pool
            
        Returns:
            A Future representing the execution of the task
        """
        def execute_after():
            # Wait for the dependency to complete
            result = dependency.get()
            # Execute the function with the result
            return func(result)
        
        return self.submit(execute_after, use_process=use_process)
    
    def map(
        self, 
        func: Callable[[T], R], 
        items: List[T], 
        use_processes: bool = False,
        progress_tracker: Optional[ProgressTracker] = None,
        progress_description: str = "Processing",
        chunk_items: bool = True,
        chunk_size: Optional[int] = None
    ) -> List[R]:
        """
        Apply a function to each item in a list, in parallel.
        
        Args:
            func: The function to apply to each item
            items: The list of items to process
            use_processes: Whether to use a process pool instead of a thread pool
            progress_tracker: Optional progress tracker instance
            progress_description: Description for the progress bar
            chunk_items: Whether to chunk items before processing
            chunk_size: Size of chunks (if chunking)
            
        Returns:
            A list of results from applying the function to each item
        """
        if use_processes:
            return self.process_pool.map(
                func, 
                items, 
                show_progress=bool(progress_tracker),
                progress_tracker=progress_tracker,
                progress_description=progress_description,
                chunk_items_first=chunk_items,
                chunk_size=chunk_size
            )
        else:
            return self.thread_pool.map(
                func, 
                items, 
                show_progress=bool(progress_tracker),
                progress_tracker=progress_tracker,
                progress_description=progress_description,
                chunk_items_first=chunk_items,
                chunk_size=chunk_size
            )
    
    def map_chunked(
        self, 
        func: Callable[[List[T]], R], 
        items: List[T], 
        use_processes: bool = False,
        chunk_size: Optional[int] = None,
        num_chunks: Optional[int] = None,
        progress_tracker: Optional[ProgressTracker] = None
    ) -> List[R]:
        """
        Apply a function to chunks of items, in parallel.
        
        Args:
            func: The function to apply to each chunk of items
            items: The list of items to process
            use_processes: Whether to use a process pool
            chunk_size: Size of each chunk
            num_chunks: Number of chunks to create
            progress_tracker: Optional progress tracker
            
        Returns:
            A list of results from applying the function to each chunk
        """
        if not items:
            return []
        
        # Create chunks
        chunked_items = chunk_items(items, chunk_size=chunk_size, num_chunks=num_chunks)
        
        # Map function to chunks
        return self.map(
            func, 
            chunked_items, 
            use_processes=use_processes,
            progress_tracker=progress_tracker,
            progress_description="Processing chunks",
            chunk_items=False  # Already chunked
        )
    
    def shutdown(self):
        """Shutdown all worker pools."""
        self.thread_pool.shutdown()
        self.process_pool.shutdown()


# Convenience functions
def parallel_map(
    func: Callable[[T], R], 
    items: List[T], 
    use_processes: bool = False,
    max_workers: Optional[int] = None,
    show_progress: bool = True,
    progress_description: str = "Processing items",
    chunk_items: bool = True,
    chunk_size: Optional[int] = None
) -> List[R]:
    """
    Apply a function to each item in a list using parallel processing.
    
    This is a convenience function that automatically chooses between
    thread and process pools based on the use_processes parameter.
    
    Args:
        func: The function to apply to each item
        items: The list of items to process
        use_processes: Whether to use processes (True) or threads (False)
        max_workers: Maximum number of workers
        show_progress: Whether to show a progress bar
        progress_description: Description for the progress bar
        chunk_items: Whether to chunk items before processing
        chunk_size: Size of chunks (if chunking)
        
    Returns:
        A list of results from applying the function to each item
    """
    if use_processes:
        pool = ProcessPool(max_workers=max_workers)
    else:
        pool = ThreadPool(max_workers=max_workers)
    
    return pool.map(
        func=func,
        items=items,
        show_progress=show_progress,
        progress_description=progress_description,
        chunk_items_first=chunk_items,
        chunk_size=chunk_size
    ) 
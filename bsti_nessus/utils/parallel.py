"""
Parallel processing utilities for BSTI Nessus to Plextrac converter.

This module provides thread and process pools for parallel execution of tasks,
with integration for progress tracking and error handling.
"""
import os
import math
import logging
import concurrent.futures
from typing import List, Callable, Any, Dict, Iterable, Optional, TypeVar, Union, Tuple

from bsti_nessus.utils.progress import progress_bar, ProgressTracker

# Setup logger
logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar('T')
R = TypeVar('R')


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
        max_workers: Optional[int] = None, 
        thread_name_prefix: str = "bsti-thread"
    ):
        """
        Initialize a thread pool.
        
        Args:
            max_workers: Maximum number of worker threads (defaults to CPU count * 5)
            thread_name_prefix: Prefix for thread names
        """
        if max_workers is None:
            # For I/O-bound tasks, we can use more threads than CPU cores
            cpu_count = os.cpu_count() or 4
            max_workers = cpu_count * 5
        
        self.max_workers = max_workers
        self.thread_name_prefix = thread_name_prefix
        logger.debug(f"Initialized ThreadPool with {max_workers} workers")
    
    def map(
        self, 
        func: Callable[[T], R], 
        items: List[T], 
        show_progress: bool = True,
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
            progress_description: Description for the progress bar
            chunk_items_first: Whether to chunk items before processing
            chunk_size: Size of chunks (if chunking)
            
        Returns:
            A list of results from applying the function to each item
        """
        if not items:
            return []
        
        total_items = len(items)
        logger.debug(f"Threading {total_items} items with {self.max_workers} workers")
        
        # Prepare items
        if chunk_items_first and total_items > self.max_workers:
            chunked_items = chunk_items(items, chunk_size=chunk_size, num_chunks=self.max_workers)
            
            # Define a wrapper function to process chunks
            def process_chunk(chunk: List[T]) -> List[R]:
                return [func(item) for item in chunk]
            
            # Process chunks in parallel
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix=self.thread_name_prefix
            ) as executor:
                if show_progress:
                    with progress_bar(
                        total=len(chunked_items), 
                        description=progress_description,
                        unit="chunks"
                    ) as pbar:
                        futures = []
                        for chunk in chunked_items:
                            futures.append(executor.submit(process_chunk, chunk))
                        
                        results = []
                        for future in concurrent.futures.as_completed(futures):
                            try:
                                chunk_results = future.result()
                                results.extend(chunk_results)
                                pbar.update(1)
                            except Exception as e:
                                logger.error(f"Error processing chunk: {e}")
                                raise
                else:
                    # Process without progress reporting
                    results = []
                    for chunk_result in executor.map(process_chunk, chunked_items):
                        results.extend(chunk_result)
            
            return results
        else:
            # Process individual items in parallel
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix=self.thread_name_prefix
            ) as executor:
                if show_progress:
                    with progress_bar(total=total_items, description=progress_description) as pbar:
                        futures = {}
                        for item in items:
                            future = executor.submit(func, item)
                            futures[future] = item
                        
                        results = []
                        for future in concurrent.futures.as_completed(futures):
                            try:
                                result = future.result()
                                results.append(result)
                                pbar.update(1)
                            except Exception as e:
                                item = futures[future]
                                logger.error(f"Error processing item {item}: {e}")
                                raise
                        
                        return results
                else:
                    # Process without progress reporting
                    return list(executor.map(func, items))


class ProcessPool:
    """
    Process pool for parallel execution of CPU-bound tasks.
    
    This class provides a simple interface for executing tasks in parallel
    using a process pool, with optional progress tracking.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize a process pool.
        
        Args:
            max_workers: Maximum number of worker processes (defaults to CPU count)
        """
        self.max_workers = max_workers or os.cpu_count() or 4
        logger.debug(f"Initialized ProcessPool with {self.max_workers} workers")
    
    def map(
        self, 
        func: Callable[[T], R], 
        items: List[T], 
        show_progress: bool = True,
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
            progress_description: Description for the progress bar
            chunk_items_first: Whether to chunk items before processing
            chunk_size: Size of chunks (if chunking)
            
        Returns:
            A list of results from applying the function to each item
        """
        if not items:
            return []
        
        total_items = len(items)
        logger.debug(f"Processing {total_items} items with {self.max_workers} processes")
        
        # For CPU-bound tasks, chunking can improve performance
        if chunk_items_first and total_items > self.max_workers:
            chunked_items = chunk_items(items, chunk_size=chunk_size, num_chunks=self.max_workers)
            
            # Define a wrapper function to process chunks
            def process_chunk(chunk: List[T]) -> List[R]:
                return [func(item) for item in chunk]
            
            # Process chunks in parallel
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                if show_progress:
                    with progress_bar(
                        total=len(chunked_items), 
                        description=progress_description,
                        unit="chunks"
                    ) as pbar:
                        futures = []
                        for chunk in chunked_items:
                            futures.append(executor.submit(process_chunk, chunk))
                        
                        results = []
                        for future in concurrent.futures.as_completed(futures):
                            try:
                                chunk_results = future.result()
                                results.extend(chunk_results)
                                pbar.update(1)
                            except Exception as e:
                                logger.error(f"Error processing chunk: {e}")
                                raise
                else:
                    # Process without progress reporting
                    results = []
                    for chunk_result in executor.map(process_chunk, chunked_items):
                        results.extend(chunk_result)
            
            return results
        else:
            # Process individual items in parallel
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                if show_progress:
                    with progress_bar(total=total_items, description=progress_description) as pbar:
                        futures = [executor.submit(func, item) for item in items]
                        
                        results = []
                        for future in concurrent.futures.as_completed(futures):
                            try:
                                result = future.result()
                                results.append(result)
                                pbar.update(1)
                            except Exception as e:
                                logger.error(f"Error processing item: {e}")
                                raise
                        
                        return results
                else:
                    # Process without progress reporting
                    return list(executor.map(func, items))


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
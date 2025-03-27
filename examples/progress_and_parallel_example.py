#!/usr/bin/env python3
"""
Example demonstrating the progress reporting and parallel processing features
of BSTI Nessus to Plextrac Converter.

This example simulates a typical workflow processing multiple files in parallel
with real-time progress tracking.
"""
import os
import sys
import time
import random
import logging
from typing import List, Dict

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bsti-example")

# Import BSTI modules
from bsti_nessus.utils.progress import ProgressTracker, NestedProgress, progress_bar
from bsti_nessus.utils.parallel import ThreadPool, ProcessPool, parallel_map


def simulate_work(duration: float = 0.5) -> None:
    """Simulate work by sleeping for a random duration."""
    time.sleep(duration * random.uniform(0.5, 1.5))


def process_file(filepath: str) -> Dict:
    """
    Process a single file with progress tracking.
    
    Args:
        filepath: Path to the file to process
        
    Returns:
        Dict containing results
    """
    # Simulate file processing
    filesize = random.randint(10, 100)  # in MB
    
    # Create a progress tracker for this file
    with progress_bar(total=filesize, description=f"Processing {os.path.basename(filepath)}") as progress:
        processed = 0
        while processed < filesize:
            # Simulate processing a chunk
            chunk_size = min(random.randint(1, 10), filesize - processed)
            simulate_work(0.1)  # Simulate work
            processed += chunk_size
            progress.update(chunk_size, info=f"Processed {chunk_size}MB chunk")
    
    return {
        "filepath": filepath,
        "filesize": filesize,
        "success": True
    }


def process_files_sequentially(filepaths: List[str]) -> List[Dict]:
    """
    Process files sequentially with progress tracking.
    
    Args:
        filepaths: List of file paths to process
        
    Returns:
        List of results for each file
    """
    print("\n[SEQUENTIAL PROCESSING]")
    results = []
    
    with progress_bar(total=len(filepaths), description="Overall progress", unit="files") as progress:
        for filepath in filepaths:
            result = process_file(filepath)
            results.append(result)
            progress.update(1, info=f"Completed {filepath}")
    
    return results


def process_files_parallel(filepaths: List[str], use_processes: bool = False) -> List[Dict]:
    """
    Process files in parallel with progress tracking.
    
    Args:
        filepaths: List of file paths to process
        use_processes: Whether to use processes (True) or threads (False)
        
    Returns:
        List of results for each file
    """
    pool_type = "PROCESS" if use_processes else "THREAD"
    print(f"\n[PARALLEL PROCESSING USING {pool_type} POOL]")
    
    if use_processes:
        pool = ProcessPool()
    else:
        pool = ThreadPool()
    
    return pool.map(
        func=process_file,
        items=filepaths,
        show_progress=True,
        progress_description=f"Processing files using {pool_type.lower()} pool"
    )


def process_files_with_nested_progress(filepaths: List[str]) -> List[Dict]:
    """
    Process files with nested progress tracking.
    
    Args:
        filepaths: List of file paths to process
        
    Returns:
        List of results for each file
    """
    print("\n[NESTED PROGRESS TRACKING]")
    
    # Define stages
    stages = [
        {"description": "Scanning files", "total": len(filepaths), "weight": 1},
        {"description": "Processing files", "total": len(filepaths), "weight": 4},
        {"description": "Finalizing results", "total": 1, "weight": 1}
    ]
    
    # Create nested progress tracker
    nested = NestedProgress(stages)
    results = []
    
    # Stage 1: Scanning
    scan_progress = nested.start_stage(0)
    for filepath in filepaths:
        # Simulate scanning
        simulate_work(0.1)
        scan_progress.update(1, info=f"Scanned {filepath}")
        nested.update_overall()
    
    # Stage 2: Processing
    process_progress = nested.start_stage(1)
    for filepath in filepaths:
        result = process_file(filepath)
        results.append(result)
        process_progress.update(1, info=f"Processed {filepath}")
        nested.update_overall()
    
    # Stage 3: Finalizing
    finalize_progress = nested.start_stage(2)
    simulate_work(1.0)
    finalize_progress.update(1, info="Results finalized")
    nested.update_overall()
    
    # Close all progress bars
    nested.close()
    
    return results


def main():
    """Run the example."""
    # Create sample file paths
    num_files = 5
    filepaths = [f"sample_file_{i}.csv" for i in range(1, num_files + 1)]
    
    print("=" * 80)
    print("BSTI Nessus to Plextrac Converter - Progress & Parallel Processing Example")
    print("=" * 80)
    
    # 1. Sequential processing
    sequential_start = time.time()
    sequential_results = process_files_sequentially(filepaths)
    sequential_time = time.time() - sequential_start
    print(f"Sequential processing completed in {sequential_time:.2f} seconds")
    
    # 2. Parallel processing with threads
    thread_start = time.time()
    thread_results = process_files_parallel(filepaths, use_processes=False)
    thread_time = time.time() - thread_start
    print(f"Thread pool processing completed in {thread_time:.2f} seconds")
    
    # 3. Parallel processing with processes
    process_start = time.time()
    process_results = process_files_parallel(filepaths, use_processes=True)
    process_time = time.time() - process_start
    print(f"Process pool processing completed in {process_time:.2f} seconds")
    
    # 4. Nested progress tracking
    nested_start = time.time()
    nested_results = process_files_with_nested_progress(filepaths)
    nested_time = time.time() - nested_start
    print(f"Nested progress processing completed in {nested_time:.2f} seconds")
    
    # Summary
    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("-" * 80)
    print(f"Sequential processing:      {sequential_time:.2f} seconds")
    print(f"Thread pool processing:     {thread_time:.2f} seconds ({sequential_time/thread_time:.1f}x faster)")
    print(f"Process pool processing:    {process_time:.2f} seconds ({sequential_time/process_time:.1f}x faster)")
    print(f"Nested progress processing: {nested_time:.2f} seconds")
    print("=" * 80)


if __name__ == "__main__":
    main() 
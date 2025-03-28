Parallel Processing
=================

.. automodule:: bsti_nessus.utils.parallel
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The parallel module provides tools for executing tasks in parallel using thread and process pools. It includes:

- A ``ThreadPool`` class for I/O-bound tasks
- A ``ProcessPool`` class for CPU-bound tasks
- A ``TaskManager`` class that provides a unified interface for both types of parallelism
- Utilities for chunking large datasets for efficient parallel processing

Examples
--------

Thread Pool for I/O-bound tasks:

.. code-block:: python

   from bsti_nessus.utils.parallel import ThreadPool

   # Create a thread pool with custom number of workers
   pool = ThreadPool(num_workers=10)

   try:
       # Submit individual tasks
       future1 = pool.submit(download_file, "http://example.com/file1.zip")
       future2 = pool.submit(download_file, "http://example.com/file2.zip")
       
       # Get results (blocks until tasks complete)
       result1 = future1.get()
       result2 = future2.get()
       
       # Process a list of items in parallel with progress tracking
       urls = ["http://example.com/file3.zip", "http://example.com/file4.zip"]
       results = pool.map(download_file, urls, show_progress=True)
   finally:
       # Always shut down the pool when done
       pool.shutdown()

Process Pool for CPU-bound tasks:

.. code-block:: python

   from bsti_nessus.utils.parallel import ProcessPool

   # Create a process pool with default number of workers (CPU count)
   pool = ProcessPool()

   try:
       # Process CPU-intensive tasks in parallel
       data_chunks = [large_array1, large_array2, large_array3]
       results = pool.map(process_data_chunk, data_chunks)
   finally:
       # Always shut down the pool when done
       pool.shutdown()

Using the TaskManager for unified interface:

.. code-block:: python

   from bsti_nessus.utils.parallel import TaskManager
   from bsti_nessus.utils.progress import ProgressTracker

   # Create a task manager
   task_manager = TaskManager()

   # Create a progress tracker
   progress = ProgressTracker(total=len(files), description="Processing files")

   # Process I/O-bound tasks (using threads by default)
   results = task_manager.map(
       process_file,
       files,
       progress_tracker=progress
   )

   # Process CPU-bound tasks using processes
   chunked_results = task_manager.map_chunked(
       process_data_chunk,
       large_dataset,
       use_processes=True,
       chunk_size=1000
   ) 
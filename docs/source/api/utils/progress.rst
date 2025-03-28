Progress Reporting
================

.. automodule:: bsti_nessus.utils.progress
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The progress module provides tools for tracking and reporting progress of long-running operations. It includes:

- A ``ProgressTracker`` class for tracking progress with ETA calculation
- A ``NestedProgress`` class for managing multi-stage operations
- Context managers and helper functions for common progress tracking patterns

Examples
--------

Basic progress tracking:

.. code-block:: python

   from bsti_nessus.utils.progress import ProgressTracker

   # Create a progress tracker
   tracker = ProgressTracker(total=100, description="Processing files")

   # Update progress as items are processed
   for i in range(100):
       # Process item
       process_item(i)
       
       # Update progress
       tracker.update(1)
       
       # Get ETA (optional)
       eta = tracker.get_eta_string()
       print(f"ETA: {eta}")

   # Close tracker when done
   tracker.close()

Using the context manager:

.. code-block:: python

   from bsti_nessus.utils.progress import progress_bar

   # Use the context manager for automatic cleanup
   with progress_bar(total=100, description="Processing files") as progress:
       for i in range(100):
           # Process item
           process_item(i)
           
           # Update progress
           progress.update(1)

Parallel processing with progress tracking:

.. code-block:: python

   from bsti_nessus.utils.progress import progress_map

   # Process items in parallel with progress tracking
   results = progress_map(
       process_item,             # Function to apply to each item
       items,                    # List of items to process
       description="Processing"  # Description for progress bar
   ) 
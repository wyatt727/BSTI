"""
Progress reporting utilities for BSTI Nessus to Plextrac converter.

This module provides classes and functions for tracking progress of long-running
operations, including ETA calculations and nested progress tracking.
"""
import time
import logging
import datetime
from typing import Callable, List, Dict, Any, Optional, TypeVar, Union, Tuple, Iterator
from contextlib import contextmanager

# Try to import tqdm, fallback to a simple progress indicator if not available
try:
    from tqdm.auto import tqdm as auto_tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    
    # Simple fallback for tqdm when not available
    class SimpleTqdm:
        """Simple fallback for tqdm when not available"""
        def __init__(self, total=None, desc=None, **kwargs):
            self.total = total
            self.desc = desc
            self.n = 0
            self.last_print = 0
            print(f"{desc or 'Progress'}: 0/{total or '?'} (0%)")
        
        def update(self, n=1):
            self.n += n
            # Only print every 100ms to avoid flooding console
            if time.time() - self.last_print > 0.1:
                if self.total:
                    percentage = int(100 * self.n / self.total)
                    print(f"\r{self.desc or 'Progress'}: {self.n}/{self.total} ({percentage}%)", end="")
                else:
                    print(f"\r{self.desc or 'Progress'}: {self.n}", end="")
                self.last_print = time.time()
        
        def close(self):
            if self.total:
                print(f"\r{self.desc or 'Progress'}: {self.n}/{self.total} (100%)")
            else:
                print(f"\r{self.desc or 'Progress'}: {self.n} (completed)")
    
    def auto_tqdm(*args, **kwargs):
        return SimpleTqdm(*args, **kwargs)


# Type variables for generics
T = TypeVar('T')
R = TypeVar('R')

# Setup logger
logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Tracks progress of an operation with ETA calculation.
    
    This class provides a simple interface for tracking progress of
    a long-running operation, with ETA calculation and logging support.
    """
    
    def __init__(
        self,
        total: int,
        description: str = "Processing",
        logger: Optional[logging.Logger] = None,
        unit: str = "it",
        position: Optional[int] = None,
        leave: bool = True,
        silent: bool = False
    ):
        """
        Initialize a progress tracker.
        
        Args:
            total: Total number of items to process
            description: Description of the operation
            logger: Logger instance to use for logging progress
            unit: Unit label for progress bar
            position: Position of the progress bar (for nested progress)
            leave: Whether to leave the progress bar after completion
            silent: If True, don't display the progress bar, but still track progress
        """
        self.total = total
        self.description = description
        self.logger = logger or logging.getLogger(__name__)
        self.unit = unit
        self.position = position
        self.leave = leave
        self.silent = silent
        
        self.current = 0
        self.start_time = None
        self.end_time = None
        
        # Create progress bar if not silent
        if not silent:
            self.progress_bar = auto_tqdm(
                total=total,
                desc=description,
                unit=unit,
                position=position,
                leave=leave
            )
        else:
            self.progress_bar = None
        
        self.logger.debug(f"Initialized progress tracker: {description} (total: {total})")
    
    def update(self, n: int = 1, info: Optional[str] = None) -> None:
        """
        Update progress by n items.
        
        Args:
            n: Number of items processed
            info: Additional information to log
        """
        # Set start time on first update
        if self.start_time is None:
            self.start_time = time.time()
        
        # Update current count
        self.current += n
        
        # Update progress bar
        if self.progress_bar is not None:
            self.progress_bar.update(n)
        
        # Log the update
        if info:
            self.logger.debug(f"{self.description}: {self.current}/{self.total} - {info}")
    
    def get_eta(self) -> Optional[float]:
        """
        Calculate estimated time to completion in seconds.
        
        Returns:
            Estimated time remaining in seconds, or None if no progress yet
        """
        if self.start_time is None or self.current == 0:
            return None
        
        elapsed = time.time() - self.start_time
        if self.current >= self.total:
            return 0
        
        items_per_second = self.current / elapsed
        remaining_items = self.total - self.current
        
        return remaining_items / items_per_second if items_per_second > 0 else float('inf')
    
    def get_eta_string(self) -> str:
        """
        Get a human-readable ETA string.
        
        Returns:
            A string representation of the ETA, or 'unknown' if not available
        """
        eta = self.get_eta()
        if eta is None:
            return "unknown"
        
        if eta > 172800:  # 2 days
            return f"{eta // 86400:.1f} days"
        elif eta > 7200:  # 2 hours
            return f"{eta // 3600:.1f} hours"
        elif eta > 120:  # 2 minutes
            return f"{eta // 60:.1f} min"
        else:
            return f"{eta:.1f} s"
    
    def close(self, success: bool = True) -> None:
        """
        Close the progress tracker.
        
        Args:
            success: Whether the operation completed successfully
        """
        self.end_time = time.time()
        
        # Complete the progress bar
        if self.progress_bar is not None:
            if success and self.current < self.total:
                self.progress_bar.update(self.total - self.current)
            self.progress_bar.close()
        
        # Log completion
        if self.start_time is not None:
            elapsed = self.end_time - self.start_time
            if success:
                self.logger.info(
                    f"{self.description} completed: {self.current}/{self.total} items "
                    f"in {elapsed:.2f} seconds ({self.current / elapsed:.2f} items/s)"
                )
            else:
                self.logger.warning(
                    f"{self.description} failed after processing "
                    f"{self.current}/{self.total} items in {elapsed:.2f} seconds"
                )
    
    def __enter__(self) -> 'ProgressTracker':
        """Enter context manager, starting the timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager, closing the progress tracker."""
        if exc_type is not None:
            self.logger.error(f"{self.description} failed: {exc_val}")
            self.close(success=False)
        else:
            self.close(success=True)


class NestedProgress:
    """
    Manages nested progress tracking for multi-stage operations.
    
    This class coordinates multiple progress trackers for different stages
    of a complex operation, updating an overall progress bar based on
    the weighted progress of individual stages.
    """
    
    def __init__(self, stages: List[Dict[str, Any]]):
        """
        Initialize nested progress tracking.
        
        Args:
            stages: List of stage configurations, each with:
                   - description: Description of the stage
                   - total: Total number of items in the stage
                   - weight: Relative weight of the stage (optional, default 1)
        """
        self.stages = stages.copy()
        self._normalize_weights()
        
        # Calculate total weighted steps
        self.total_weighted_steps = 100  # Use percentage
        
        # Create overall progress bar
        self.overall_progress = ProgressTracker(
            total=self.total_weighted_steps,
            description="Overall progress",
            unit="%"
        )
        
        # Initialize trackers list and current stage
        self.trackers = []
        self.current_stage = -1
    
    def _normalize_weights(self) -> None:
        """Normalize stage weights to sum to 1."""
        # Set default weights if not provided
        for stage in self.stages:
            if "weight" not in stage:
                stage["weight"] = 1
        
        # Calculate total weight
        total_weight = sum(stage["weight"] for stage in self.stages)
        
        # Normalize weights
        for stage in self.stages:
            stage["weight"] = stage["weight"] / total_weight
    
    def start_stage(self, stage_index: int) -> ProgressTracker:
        """
        Start a new stage of progress tracking.
        
        Args:
            stage_index: Index of the stage to start
            
        Returns:
            The progress tracker for the new stage
        """
        if stage_index >= len(self.stages):
            raise ValueError(f"Stage index {stage_index} out of range")
        
        # Close previous stage if applicable
        if self.current_stage != -1 and self.current_stage < len(self.trackers):
            self.trackers[self.current_stage].close()
        
        # Update current stage
        self.current_stage = stage_index
        stage = self.stages[stage_index]
        
        # Create progress tracker for this stage
        tracker = ProgressTracker(
            total=stage["total"],
            description=stage["description"],
            position=1,  # Position below overall progress
            leave=False  # Don't leave the progress bar after completion
        )
        
        # Add to trackers list
        if stage_index < len(self.trackers):
            self.trackers[stage_index] = tracker
        else:
            self.trackers.append(tracker)
        
        return tracker
    
    def update_overall(self) -> None:
        """Update the overall progress based on stage progress."""
        total_progress = 0
        
        # Calculate weighted progress from all stages
        for i, tracker in enumerate(self.trackers):
            if i < len(self.stages):
                weight = self.stages[i]["weight"]
                if tracker.total > 0:
                    stage_progress = (tracker.current / tracker.total) * 100
                    weighted_progress = stage_progress * weight
                    total_progress += weighted_progress
        
        # Update overall progress (delta from current)
        delta = int(total_progress) - self.overall_progress.current
        if delta > 0:
            self.overall_progress.update(delta)
    
    def close(self) -> None:
        """Close all progress trackers."""
        # Close stage trackers
        for tracker in self.trackers:
            tracker.close()
        
        # Close overall tracker
        self.overall_progress.close()


@contextmanager
def progress_bar(
    total: int,
    description: str = "Processing",
    **kwargs
) -> Iterator[ProgressTracker]:
    """
    Context manager for progress tracking.
    
    Args:
        total: Total number of items
        description: Description of the operation
        **kwargs: Additional arguments to pass to ProgressTracker
        
    Yields:
        A ProgressTracker instance
    """
    tracker = ProgressTracker(total=total, description=description, **kwargs)
    try:
        yield tracker
    finally:
        tracker.close()


def progress_map(
    func: Callable[[T], R],
    items: List[T],
    description: str = "Processing items",
    **kwargs
) -> List[R]:
    """
    Apply a function to each item in a list with progress tracking.
    
    Args:
        func: Function to apply
        items: List of items to process
        description: Description for the progress bar
        **kwargs: Additional arguments to pass to ProgressTracker
        
    Returns:
        List of results
    """
    results = []
    
    with progress_bar(total=len(items), description=description, **kwargs) as pbar:
        for item in items:
            result = func(item)
            results.append(result)
            pbar.update(1)
    
    return results 
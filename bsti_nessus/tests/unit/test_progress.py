import time
import pytest
from unittest.mock import MagicMock, patch

from bsti_nessus.utils.progress import ProgressTracker, NestedProgress, progress_map, progress_bar


@pytest.fixture
def mock_logger():
    """Fixture to provide a mock logger."""
    return MagicMock()


def test_progress_tracker_init():
    """Test initializing a ProgressTracker."""
    tracker = ProgressTracker(total=100, description="Test progress")
    
    assert tracker.total == 100
    assert tracker.description == "Test progress"
    assert tracker.current == 0
    assert tracker.start_time is None
    assert tracker.end_time is None


def test_progress_tracker_update():
    """Test updating a ProgressTracker."""
    tracker = ProgressTracker(total=100, description="Test progress", silent=True)
    
    # Update by 1
    tracker.update(1)
    assert tracker.current == 1
    assert tracker.start_time is not None
    
    # Update by multiple
    tracker.update(10)
    assert tracker.current == 11
    
    # Update with info
    tracker.update(1, info="Processing item 12")
    assert tracker.current == 12


def test_progress_tracker_eta():
    """Test ETA calculation in ProgressTracker."""
    tracker = ProgressTracker(total=100, description="Test progress", silent=True)
    
    # No ETA before any updates
    assert tracker.get_eta() is None
    assert tracker.get_eta_string() == "unknown"
    
    # Update and test ETA
    with patch.object(tracker, 'start_time', time.time() - 10):  # 10 seconds elapsed
        tracker.current = 20  # 20% complete in 10 seconds
        
        # ETA should be about 40 seconds (80 items at 2 items/sec)
        eta = tracker.get_eta()
        assert 35 < eta < 45
        
        # Test ETA string format
        assert "s" in tracker.get_eta_string()  # Should be in seconds


def test_progress_tracker_context_manager():
    """Test using ProgressTracker as a context manager."""
    with ProgressTracker(total=10, description="Test context", silent=True) as tracker:
        assert tracker.start_time is not None
        tracker.update(5)
    
    # After context exits
    assert tracker.end_time is not None
    assert tracker.current == 5


def test_nested_progress():
    """Test nested progress tracking."""
    stages = [
        {"description": "Stage 1", "total": 50, "weight": 1},
        {"description": "Stage 2", "total": 100, "weight": 2}
    ]
    
    progress = NestedProgress(stages)
    assert len(progress.stages) == 2
    
    # Start stage 1
    tracker1 = progress.start_stage(0)
    assert progress.current_stage == 0
    
    # Update stage 1
    tracker1.update(25)  # 50% of stage 1
    progress.update_overall()
    assert progress.overall_progress.current > 0
    
    # Start stage 2
    tracker2 = progress.start_stage(1)
    assert progress.current_stage == 1
    
    # Update stage 2
    tracker2.update(50)  # 50% of stage 2
    progress.update_overall()
    
    # Close everything
    progress.close()


def test_progress_map():
    """Test progress_map function."""
    items = [1, 2, 3, 4, 5]
    result = progress_map(lambda x: x * 2, items, description="Doubling", silent=True)
    
    assert result == [2, 4, 6, 8, 10]


def test_progress_bar_context_manager():
    """Test progress_bar context manager."""
    with progress_bar(total=10, description="Test progress bar", silent=True) as tracker:
        assert tracker.total == 10
        tracker.update(5)
        assert tracker.current == 5 
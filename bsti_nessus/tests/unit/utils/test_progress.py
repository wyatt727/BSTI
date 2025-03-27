"""
Unit tests for the progress reporting module
"""
import time
import sys
from unittest.mock import patch, MagicMock
import pytest

from bsti_nessus.utils.progress import (
    ProgressTracker, 
    NestedProgress, 
    progress_bar, 
    progress_map
)


@pytest.fixture
def mock_tqdm():
    """Mock for tqdm progress bar"""
    with patch('bsti_nessus.utils.progress.auto_tqdm') as mock:
        pbar = MagicMock()
        mock.return_value = pbar
        yield pbar


@pytest.fixture
def mock_logger():
    """Mock for logger"""
    mock = MagicMock()
    return mock


class TestProgressTracker:
    """Test the progress tracker"""
    
    def test_init(self, mock_tqdm):
        """Test progress tracker initialization"""
        with patch('bsti_nessus.utils.progress.auto_tqdm') as mock_auto_tqdm:
            mock_bar = MagicMock()
            mock_auto_tqdm.return_value = mock_bar
            
            tracker = ProgressTracker(
                total=100, 
                description="Test Progress",
                unit="files",
                position=1
            )
            
            assert tracker.total == 100
            assert tracker.description == "Test Progress"
            assert tracker.unit == "files"
            assert tracker.position == 1
            assert tracker.current == 0
            assert tracker.start_time is None
            
            # Check that tqdm was called with the right parameters
            mock_auto_tqdm.assert_called_once()
            args, kwargs = mock_auto_tqdm.call_args
            assert kwargs["total"] == 100
            assert kwargs["desc"] == "Test Progress"
            assert kwargs["unit"] == "files"
            assert kwargs["position"] == 1
    
    def test_update(self, mock_tqdm):
        """Test progress bar update"""
        tracker = ProgressTracker(total=100, description="Test Progress")
        
        # Update progress
        tracker.update(5)
        
        assert tracker.current == 5
        assert tracker.start_time is not None
        mock_tqdm.update.assert_called_once_with(5)
        
        # Update with info
        mock_logger = MagicMock()
        tracker.logger = mock_logger
        tracker.update(10, info="Processing batch 1")
        
        assert tracker.current == 15
        mock_tqdm.update.assert_called_with(10)
        mock_logger.debug.assert_called_once()
    
    def test_get_eta(self, mock_tqdm):
        """Test ETA calculation"""
        tracker = ProgressTracker(total=100)
        
        # No progress yet
        assert tracker.get_eta() is None
        
        # Set up some progress
        tracker.start_time = time.time() - 10  # 10 seconds elapsed
        tracker.current = 20  # 20% complete
        
        # ETA should be around 40 seconds (10 seconds for 20%, so 40 more for remaining 80%)
        eta = tracker.get_eta()
        assert 35 <= eta <= 45
        
        # Test the string format
        eta_string = tracker.get_eta_string()
        assert "s" in eta_string  # Should contain seconds
    
    def test_close(self, mock_tqdm):
        """Test progress bar closing"""
        tracker = ProgressTracker(total=100, description="Test Progress")
        mock_logger = MagicMock()
        tracker.logger = mock_logger
        
        # Start tracking
        tracker.start_time = time.time() - 5
        tracker.current = 50
        
        # Close successfully
        tracker.close(success=True)
        
        assert tracker.end_time is not None
        mock_tqdm.update.assert_called_once_with(50)  # Remaining progress
        mock_tqdm.close.assert_called_once()
        mock_logger.info.assert_called_once()
        
        # Reset and test unsuccessful close
        mock_tqdm.reset_mock()
        mock_logger.reset_mock()
        tracker = ProgressTracker(total=100)
        tracker.logger = mock_logger
        tracker.start_time = time.time() - 5
        tracker.current = 50
        
        tracker.close(success=False)
        
        mock_tqdm.close.assert_called_once()
        mock_logger.warning.assert_called_once()
    
    def test_context_manager(self, mock_tqdm):
        """Test progress tracker as context manager"""
        mock_logger = MagicMock()
        
        # Normal execution
        with ProgressTracker(total=100, logger=mock_logger) as tracker:
            assert tracker.start_time is not None
            tracker.update(50)
        
        mock_tqdm.close.assert_called_once()
        mock_logger.info.assert_called_once()
        
        # With exception
        mock_tqdm.reset_mock()
        mock_logger.reset_mock()
        
        try:
            with ProgressTracker(total=100, logger=mock_logger) as tracker:
                tracker.update(50)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        mock_tqdm.close.assert_called_once()
        mock_logger.error.assert_called_once()


class TestNestedProgress:
    """Test nested progress tracking"""
    
    @patch('bsti_nessus.utils.progress.ProgressTracker')
    def test_init(self, mock_tracker_class):
        """Test nested progress initialization"""
        stages = [
            {"description": "Stage 1", "total": 100, "weight": 2},
            {"description": "Stage 2", "total": 200, "weight": 3},
            {"description": "Stage 3", "total": 150, "weight": 1}
        ]
        
        mock_overall = MagicMock()
        mock_tracker_class.return_value = mock_overall
        
        nested = NestedProgress(stages)
        
        # Check that weights were normalized
        assert nested.stages[0]["weight"] == 2/6
        assert nested.stages[1]["weight"] == 3/6
        assert nested.stages[2]["weight"] == 1/6
        
        # Check that overall progress was created
        assert nested.overall_progress == mock_overall
        mock_tracker_class.assert_called_once()
        
        # Check trackers list
        assert nested.trackers == []
        assert nested.current_stage == -1
    
    @patch('bsti_nessus.utils.progress.ProgressTracker')
    def test_start_stage(self, mock_tracker_class):
        """Test starting a stage"""
        stages = [
            {"description": "Stage 1", "total": 100},
            {"description": "Stage 2", "total": 200}
        ]
        
        # Mock tracker instances
        mock_overall = MagicMock()
        mock_stage1 = MagicMock()
        mock_stage2 = MagicMock()
        mock_tracker_class.side_effect = [mock_overall, mock_stage1, mock_stage2]
        
        nested = NestedProgress(stages)
        
        # Start first stage
        tracker1 = nested.start_stage(0)
        
        assert tracker1 == mock_stage1
        assert nested.current_stage == 0
        assert nested.trackers == [mock_stage1]
        
        # Start second stage
        tracker2 = nested.start_stage(1)
        
        assert tracker2 == mock_stage2
        assert nested.current_stage == 1
        assert nested.trackers == [mock_stage1, mock_stage2]
        mock_stage1.close.assert_called_once()
        
        # Test invalid stage
        with pytest.raises(ValueError):
            nested.start_stage(2)
    
    @patch('bsti_nessus.utils.progress.ProgressTracker')
    def test_update_overall(self, mock_tracker_class):
        """Test updating overall progress"""
        stages = [
            {"description": "Stage 1", "total": 100, "weight": 1},
            {"description": "Stage 2", "total": 200, "weight": 1}
        ]
        
        # Mock tracker instances
        mock_overall = MagicMock()
        mock_stage1 = MagicMock()
        mock_stage2 = MagicMock()
        mock_tracker_class.side_effect = [mock_overall, mock_stage1, mock_stage2]
        
        # Configure mock values
        mock_overall.current = 0
        mock_stage1.total = 100
        mock_stage1.current = 100  # Completed
        mock_stage2.total = 200
        mock_stage2.current = 100  # 50% complete
        
        nested = NestedProgress(stages)
        nested.trackers = [mock_stage1, mock_stage2]
        
        # Set current stage to 1 (second stage)
        nested.current_stage = 1
        
        # Update overall progress
        nested.update_overall()
        
        # First stage is complete (50%), second stage is 50% complete (25%)
        # Total should be 75%
        mock_overall.update.assert_called_once_with(75)
    
    @patch('bsti_nessus.utils.progress.ProgressTracker')
    def test_close(self, mock_tracker_class):
        """Test closing all progress trackers"""
        # Mock tracker instances
        mock_overall = MagicMock()
        mock_stage1 = MagicMock()
        mock_stage2 = MagicMock()
        mock_tracker_class.side_effect = [mock_overall, mock_stage1, mock_stage2]
        
        # Create nested progress
        nested = NestedProgress([
            {"description": "Stage 1", "total": 100},
            {"description": "Stage 2", "total": 200}
        ])
        nested.trackers = [mock_stage1, mock_stage2]
        
        # Close all trackers
        nested.close()
        
        mock_stage1.close.assert_called_once()
        mock_stage2.close.assert_called_once()
        mock_overall.close.assert_called_once()


def test_progress_bar_context_manager():
    """Test progress_bar context manager"""
    with patch('bsti_nessus.utils.progress.ProgressTracker') as mock_tracker_class:
        mock_tracker = MagicMock()
        mock_tracker_class.return_value = mock_tracker
        
        with progress_bar(total=100, description="Test") as bar:
            assert bar == mock_tracker
            bar.update(50)
        
        mock_tracker.update.assert_called_once_with(50)
        mock_tracker.close.assert_called_once()


def test_progress_map():
    """Test progress_map function"""
    with patch('bsti_nessus.utils.progress.progress_bar') as mock_progress_bar:
        mock_tracker = MagicMock()
        mock_progress_bar.return_value.__enter__.return_value = mock_tracker
        
        # Define a simple function to map
        def square(x):
            return x * x
        
        # Apply function with progress tracking
        result = progress_map(square, [1, 2, 3, 4], description="Squaring")
        
        assert result == [1, 4, 9, 16]
        assert mock_tracker.update.call_count == 4 
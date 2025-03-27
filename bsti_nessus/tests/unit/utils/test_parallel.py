"""
Unit tests for the parallel processing module
"""
import time
import os
from unittest.mock import patch, MagicMock
import pytest

from bsti_nessus.utils.parallel import (
    chunk_items,
    ThreadPool,
    ProcessPool,
    parallel_map
)


def test_chunk_items_with_chunk_size():
    """Test chunking items with a specific chunk size"""
    items = list(range(10))
    chunked = chunk_items(items, chunk_size=3)
    
    assert len(chunked) == 4
    assert chunked == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_chunk_items_with_num_chunks():
    """Test chunking items with a specific number of chunks"""
    items = list(range(10))
    chunked = chunk_items(items, num_chunks=3)
    
    assert len(chunked) == 3
    assert chunked == [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]


def test_chunk_items_empty():
    """Test chunking an empty list"""
    assert chunk_items([]) == []


def test_chunk_items_defaults():
    """Test chunking with default parameters"""
    items = list(range(10))
    
    with patch('os.cpu_count', return_value=2):
        chunked = chunk_items(items)
    
    assert len(chunked) == 2
    assert chunked == [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]


def test_chunk_items_single_chunk():
    """Test chunking with a chunk size larger than the list"""
    items = list(range(5))
    chunked = chunk_items(items, chunk_size=10)
    
    assert len(chunked) == 1
    assert chunked == [items]


class TestThreadPool:
    """Test the ThreadPool class"""
    
    def test_init_default_workers(self):
        """Test initializing ThreadPool with default worker count"""
        with patch('os.cpu_count', return_value=4):
            pool = ThreadPool()
            assert pool.max_workers == 20  # 4 * 5
    
    def test_init_custom_workers(self):
        """Test initializing ThreadPool with custom worker count"""
        pool = ThreadPool(max_workers=10)
        assert pool.max_workers == 10
    
    @patch('concurrent.futures.ThreadPoolExecutor')
    @patch('bsti_nessus.utils.parallel.progress_bar')
    def test_map_with_progress(self, mock_progress_bar, mock_executor_class):
        """Test mapping with progress tracking"""
        # Mock the progress bar context manager
        mock_bar = MagicMock()
        mock_progress_bar.return_value.__enter__.return_value = mock_bar
        
        # Mock the executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock futures for as_completed
        future1 = MagicMock()
        future1.result.return_value = 1
        future2 = MagicMock()
        future2.result.return_value = 4
        
        with patch('concurrent.futures.as_completed', return_value=[future1, future2]):
            # Test map function
            pool = ThreadPool(max_workers=2)
            result = pool.map(lambda x: x*x, [1, 2], show_progress=True)
            
            assert result == [1, 4]
            mock_bar.update.call_count == 2
    
    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_map_no_progress(self, mock_executor_class):
        """Test mapping without progress tracking"""
        # Mock the executor
        mock_executor = MagicMock()
        mock_executor.map.return_value = [1, 4]
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Test map function
        pool = ThreadPool(max_workers=2)
        result = pool.map(lambda x: x*x, [1, 2], show_progress=False)
        
        assert result == [1, 4]
    
    @patch('concurrent.futures.ThreadPoolExecutor')
    @patch('bsti_nessus.utils.parallel.progress_bar')
    @patch('bsti_nessus.utils.parallel.chunk_items')
    def test_map_with_chunking(self, mock_chunk_items, mock_progress_bar, mock_executor_class):
        """Test mapping with chunking"""
        # Mock chunking
        mock_chunk_items.return_value = [[1, 2], [3, 4]]
        
        # Mock the progress bar
        mock_bar = MagicMock()
        mock_progress_bar.return_value.__enter__.return_value = mock_bar
        
        # Mock the executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock futures for as_completed
        future1 = MagicMock()
        future1.result.return_value = [1, 4]
        future2 = MagicMock()
        future2.result.return_value = [9, 16]
        
        with patch('concurrent.futures.as_completed', return_value=[future1, future2]):
            # Test map function with chunking
            pool = ThreadPool(max_workers=2)
            result = pool.map(
                lambda x: x*x, 
                [1, 2, 3, 4], 
                show_progress=True,
                chunk_items_first=True
            )
            
            assert result == [1, 4, 9, 16]
            mock_bar.update.call_count == 2
    
    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_map_empty_list(self, mock_executor_class):
        """Test mapping an empty list"""
        pool = ThreadPool()
        result = pool.map(lambda x: x*x, [])
        
        assert result == []
        mock_executor_class.assert_not_called()


class TestProcessPool:
    """Test the ProcessPool class"""
    
    def test_init_default_workers(self):
        """Test initializing ProcessPool with default worker count"""
        with patch('os.cpu_count', return_value=4):
            pool = ProcessPool()
            assert pool.max_workers == 4
    
    def test_init_custom_workers(self):
        """Test initializing ProcessPool with custom worker count"""
        pool = ProcessPool(max_workers=10)
        assert pool.max_workers == 10
    
    @patch('concurrent.futures.ProcessPoolExecutor')
    @patch('bsti_nessus.utils.parallel.progress_bar')
    def test_map_with_progress(self, mock_progress_bar, mock_executor_class):
        """Test mapping with progress tracking"""
        # Mock the progress bar context manager
        mock_bar = MagicMock()
        mock_progress_bar.return_value.__enter__.return_value = mock_bar
        
        # Mock the executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock futures for as_completed
        future1 = MagicMock()
        future1.result.return_value = 1
        future2 = MagicMock()
        future2.result.return_value = 4
        
        with patch('concurrent.futures.as_completed', return_value=[future1, future2]):
            # Test map function
            pool = ProcessPool(max_workers=2)
            result = pool.map(lambda x: x*x, [1, 2], show_progress=True)
            
            assert result == [1, 4]
            mock_bar.update.call_count == 2
    
    @patch('concurrent.futures.ProcessPoolExecutor')
    def test_map_no_progress(self, mock_executor_class):
        """Test mapping without progress tracking"""
        # Mock the executor
        mock_executor = MagicMock()
        mock_executor.map.return_value = [1, 4]
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Test map function
        pool = ProcessPool(max_workers=2)
        result = pool.map(lambda x: x*x, [1, 2], show_progress=False)
        
        assert result == [1, 4]
    
    @patch('concurrent.futures.ProcessPoolExecutor')
    @patch('bsti_nessus.utils.parallel.progress_bar')
    @patch('bsti_nessus.utils.parallel.chunk_items')
    def test_map_with_chunking(self, mock_chunk_items, mock_progress_bar, mock_executor_class):
        """Test mapping with chunking"""
        # Mock chunking
        mock_chunk_items.return_value = [[1, 2], [3, 4]]
        
        # Mock the progress bar
        mock_bar = MagicMock()
        mock_progress_bar.return_value.__enter__.return_value = mock_bar
        
        # Mock the executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock futures for as_completed
        future1 = MagicMock()
        future1.result.return_value = [1, 4]
        future2 = MagicMock()
        future2.result.return_value = [9, 16]
        
        with patch('concurrent.futures.as_completed', return_value=[future1, future2]):
            # Test map function with chunking
            pool = ProcessPool(max_workers=2)
            result = pool.map(
                lambda x: x*x, 
                [1, 2, 3, 4], 
                show_progress=True,
                chunk_items_first=True
            )
            
            assert result == [1, 4, 9, 16]
            mock_bar.update.call_count == 2


def test_parallel_map_threads():
    """Test parallel_map with threads"""
    with patch('bsti_nessus.utils.parallel.ThreadPool') as mock_thread_pool_class:
        mock_pool = MagicMock()
        mock_thread_pool_class.return_value = mock_pool
        
        # Configure the mock
        mock_pool.map.return_value = [1, 4, 9]
        
        # Call the function
        result = parallel_map(lambda x: x*x, [1, 2, 3], use_processes=False)
        
        # Check the result
        assert result == [1, 4, 9]
        
        # Verify ThreadPool was used
        mock_thread_pool_class.assert_called_once()
        mock_pool.map.assert_called_once()


def test_parallel_map_processes():
    """Test parallel_map with processes"""
    with patch('bsti_nessus.utils.parallel.ProcessPool') as mock_process_pool_class:
        mock_pool = MagicMock()
        mock_process_pool_class.return_value = mock_pool
        
        # Configure the mock
        mock_pool.map.return_value = [1, 4, 9]
        
        # Call the function
        result = parallel_map(lambda x: x*x, [1, 2, 3], use_processes=True)
        
        # Check the result
        assert result == [1, 4, 9]
        
        # Verify ProcessPool was used
        mock_process_pool_class.assert_called_once()
        mock_pool.map.assert_called_once()


@pytest.mark.integration
def test_real_parallel_execution():
    """Integration test for actual parallel execution"""
    # Only run if explicitly requested
    if not os.environ.get('RUN_SLOW_TESTS'):
        pytest.skip("Skipping slow integration test")
    
    def slow_square(x):
        time.sleep(0.1)  # Simulate work
        return x * x
    
    # Test with ThreadPool
    start_time = time.time()
    thread_result = parallel_map(slow_square, list(range(10)), use_processes=False)
    thread_time = time.time() - start_time
    
    # Check results
    assert thread_result == [x*x for x in range(10)]
    
    # Should be much faster than sequential (which would take ~1 second)
    assert thread_time < 0.5
    
    # Test with ProcessPool
    start_time = time.time()
    process_result = parallel_map(slow_square, list(range(10)), use_processes=True)
    process_time = time.time() - start_time
    
    # Check results
    assert process_result == [x*x for x in range(10)]
    
    # Should be much faster than sequential
    assert process_time < 0.5 
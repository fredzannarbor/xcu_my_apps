"""
Performance tests for the ideation system.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

from src.codexes.modules.ideation import (
    BookIdea, IdeaSet, Tournament, ContinuousIdeaGenerator
)
from src.codexes.modules.ideation.monitoring import MetricsCollector


class TestIdeationPerformance:
    """Performance tests for ideation components."""
    
    def test_book_idea_creation_performance(self):
        """Test BookIdea creation performance."""
        start_time = time.time()
        
        ideas = []
        for i in range(1000):
            idea = BookIdea(
                title=f"Book {i}",
                logline=f"Logline for book {i}",
                genre="Fiction",
                target_audience="Adults"
            )
            ideas.append(idea)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        assert len(ideas) == 1000
        assert creation_time < 1.0  # Should create 1000 ideas in under 1 second
        
        print(f"Created 1000 BookIdea objects in {creation_time:.3f} seconds")

    def test_idea_set_operations_performance(self):
        """Test IdeaSet operations performance."""
        idea_set = IdeaSet()
        
        # Test addition performance
        start_time = time.time()
        for i in range(1000):
            idea = BookIdea(title=f"Book {i}", logline=f"Logline {i}")
            idea_set.add_idea(idea)
        
        addition_time = time.time() - start_time
        assert len(idea_set) == 1000
        assert addition_time < 2.0
        
        # Test filtering performance
        start_time = time.time()
        filtered = idea_set.filter_ideas(lambda x: "5" in x.title)
        filtering_time = time.time() - start_time
        
        assert len(filtered) > 0
        assert filtering_time < 0.5
        
        print(f"Added 1000 ideas in {addition_time:.3f}s, filtered in {filtering_time:.3f}s")

    @patch('src.codexes.core.llm_caller.LLMCaller')
    def test_tournament_performance(self, mock_llm_caller):
        """Test tournament execution performance."""
        mock_llm_caller.call_llm.return_value = {'content': 'A'}
        
        # Test with different tournament sizes
        sizes = [4, 8, 16, 32]
        
        for size in sizes:
            ideas = [
                BookIdea(title=f"Book {i}", logline=f"Logline {i}")
                for i in range(size)
            ]
            
            start_time = time.time()
            tournament = Tournament(ideas, mock_llm_caller)
            tournament.create_brackets()
            execution_time = time.time() - start_time
            
            assert tournament.get_winner() is not None
            assert execution_time < size * 0.1  # Should be roughly linear
            
            print(f"Tournament with {size} participants completed in {execution_time:.3f}s")

    @patch('src.codexes.core.llm_caller.LLMCaller')
    def test_continuous_generation_performance(self, mock_llm_caller):
        """Test continuous generation performance."""
        mock_llm_caller.call_llm.return_value = {
            'content': '{"title": "Generated Book", "logline": "Generated logline"}'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ContinuousIdeaGenerator(
                llm_caller=mock_llm_caller,
                ideas_per_batch=10,
                base_dir=temp_dir
            )
            
            start_time = time.time()
            results = generator.generate_single_batch()
            generation_time = time.time() - start_time
            
            assert results is not None
            assert generation_time < 5.0  # Should generate batch in under 5 seconds
            
            print(f"Generated batch of 10 ideas in {generation_time:.3f}s")

    def test_metrics_collection_performance(self):
        """Test metrics collection performance."""
        collector = MetricsCollector(collection_interval=1)
        
        start_time = time.time()
        
        # Collect metrics multiple times
        for _ in range(100):
            metrics = collector._collect_current_metrics()
            assert metrics is not None
        
        collection_time = time.time() - start_time
        
        assert collection_time < 10.0  # Should collect 100 metrics in under 10 seconds
        print(f"Collected 100 metrics in {collection_time:.3f}s")

    def test_concurrent_tournament_performance(self):
        """Test concurrent tournament execution."""
        with patch('src.codexes.core.llm_caller.LLMCaller') as mock_llm_caller:
            mock_llm_caller.call_llm.return_value = {'content': 'A'}
            
            def run_tournament(tournament_id):
                ideas = [
                    BookIdea(title=f"Book {tournament_id}-{i}", logline=f"Logline {i}")
                    for i in range(8)
                ]
                
                tournament = Tournament(ideas, mock_llm_caller)
                tournament.create_brackets()
                return tournament.get_winner()
            
            # Run multiple tournaments concurrently
            threads = []
            results = {}
            
            start_time = time.time()
            
            for i in range(5):
                thread = threading.Thread(
                    target=lambda tid=i: results.update({tid: run_tournament(tid)})
                )
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            concurrent_time = time.time() - start_time
            
            assert len(results) == 5
            assert all(winner is not None for winner in results.values())
            assert concurrent_time < 10.0  # Should complete 5 concurrent tournaments in under 10s
            
            print(f"Completed 5 concurrent tournaments in {concurrent_time:.3f}s")

    def test_memory_usage_performance(self):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        large_idea_set = IdeaSet()
        for i in range(10000):
            idea = BookIdea(
                title=f"Book {i}",
                logline=f"This is a longer logline for book {i} to test memory usage",
                description=f"Extended description for book {i} " * 10,
                genre="Fiction",
                target_audience="Adults"
            )
            large_idea_set.add_idea(idea)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        assert len(large_idea_set) == 10000
        assert memory_increase < 500  # Should use less than 500MB for 10k ideas
        
        print(f"Memory usage for 10k ideas: {memory_increase:.1f}MB")

    def test_file_io_performance(self):
        """Test file I/O performance for persistence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create large idea set
            idea_set = IdeaSet()
            for i in range(1000):
                idea = BookIdea(title=f"Book {i}", logline=f"Logline {i}")
                idea_set.add_idea(idea)
            
            file_path = Path(temp_dir) / "performance_test.json"
            
            # Test save performance
            start_time = time.time()
            idea_set.save_to_json(str(file_path))
            save_time = time.time() - start_time
            
            # Test load performance
            new_idea_set = IdeaSet()
            start_time = time.time()
            new_idea_set.load_from_json(str(file_path))
            load_time = time.time() - start_time
            
            assert len(new_idea_set) == 1000
            assert save_time < 2.0  # Should save 1000 ideas in under 2 seconds
            assert load_time < 2.0  # Should load 1000 ideas in under 2 seconds
            
            print(f"Save: {save_time:.3f}s, Load: {load_time:.3f}s for 1000 ideas")


class TestScalabilityLimits:
    """Test system behavior at scale limits."""
    
    @patch('src.codexes.core.llm_caller.LLMCaller')
    def test_large_tournament_scalability(self, mock_llm_caller):
        """Test tournament scalability with large participant counts."""
        mock_llm_caller.call_llm.return_value = {'content': 'A'}
        
        # Test progressively larger tournaments
        max_size = 128  # Start with reasonable size
        
        ideas = [
            BookIdea(title=f"Book {i}", logline=f"Logline {i}")
            for i in range(max_size)
        ]
        
        start_time = time.time()
        tournament = Tournament(ideas, mock_llm_caller)
        tournament.create_brackets()
        execution_time = time.time() - start_time
        
        assert tournament.get_winner() is not None
        assert len(tournament.rounds) > 0
        
        # Calculate expected matches for single elimination
        expected_matches = max_size - 1
        actual_matches = sum(len(round_data['matches']) for round_data in tournament.rounds)
        
        assert actual_matches >= expected_matches
        print(f"Tournament with {max_size} participants: {execution_time:.3f}s, {actual_matches} matches")

    def test_continuous_generation_endurance(self):
        """Test continuous generation system endurance."""
        with patch('src.codexes.core.llm_caller.LLMCaller') as mock_llm_caller:
            mock_llm_caller.call_llm.return_value = {
                'content': '{"title": "Generated Book", "logline": "Generated logline"}'
            }
            
            with tempfile.TemporaryDirectory() as temp_dir:
                generator = ContinuousIdeaGenerator(
                    llm_caller=mock_llm_caller,
                    ideas_per_batch=5,
                    base_dir=temp_dir
                )
                
                # Simulate multiple generation cycles
                successful_generations = 0
                start_time = time.time()
                
                for i in range(10):  # 10 cycles
                    results = generator.generate_single_batch()
                    if results:
                        successful_generations += 1
                
                total_time = time.time() - start_time
                
                assert successful_generations >= 8  # At least 80% success rate
                assert total_time < 30.0  # Should complete in under 30 seconds
                
                print(f"Endurance test: {successful_generations}/10 successful in {total_time:.3f}s")

    def test_concurrent_load_handling(self):
        """Test system behavior under concurrent load."""
        with patch('src.codexes.core.llm_caller.LLMCaller') as mock_llm_caller:
            mock_llm_caller.call_llm.return_value = {'content': 'A'}
            
            def concurrent_operation(operation_id):
                """Simulate concurrent ideation operations."""
                ideas = [
                    BookIdea(title=f"Book {operation_id}-{i}", logline=f"Logline {i}")
                    for i in range(4)
                ]
                
                tournament = Tournament(ideas, mock_llm_caller)
                tournament.create_brackets()
                return tournament.get_winner() is not None
            
            # Run many concurrent operations
            threads = []
            results = []
            
            start_time = time.time()
            
            for i in range(20):  # 20 concurrent operations
                thread = threading.Thread(
                    target=lambda oid=i: results.append(concurrent_operation(oid))
                )
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            concurrent_time = time.time() - start_time
            success_rate = sum(results) / len(results)
            
            assert success_rate >= 0.9  # At least 90% success rate
            assert concurrent_time < 20.0  # Should complete in reasonable time
            
            print(f"Concurrent load test: {success_rate:.1%} success rate in {concurrent_time:.3f}s")


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Benchmark tests for performance regression detection."""
    
    def test_idea_creation_benchmark(self):
        """Benchmark for BookIdea creation."""
        iterations = 10000
        
        start_time = time.perf_counter()
        for i in range(iterations):
            BookIdea(title=f"Book {i}", logline=f"Logline {i}")
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        ideas_per_second = iterations / total_time
        
        # Benchmark: Should create at least 10,000 ideas per second
        assert ideas_per_second > 10000
        print(f"BookIdea creation benchmark: {ideas_per_second:.0f} ideas/second")

    @patch('src.codexes.core.llm_caller.LLMCaller')
    def test_tournament_benchmark(self, mock_llm_caller):
        """Benchmark for tournament execution."""
        mock_llm_caller.call_llm.return_value = {'content': 'A'}
        
        tournament_sizes = [8, 16, 32]
        
        for size in tournament_sizes:
            ideas = [
                BookIdea(title=f"Book {i}", logline=f"Logline {i}")
                for i in range(size)
            ]
            
            start_time = time.perf_counter()
            tournament = Tournament(ideas, mock_llm_caller)
            tournament.create_brackets()
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            matches_per_second = (size - 1) / execution_time
            
            print(f"Tournament benchmark ({size} participants): {matches_per_second:.1f} matches/second")

    def test_serialization_benchmark(self):
        """Benchmark for idea serialization performance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            idea_set = IdeaSet()
            
            # Create test dataset
            for i in range(5000):
                idea = BookIdea(
                    title=f"Book {i}",
                    logline=f"Logline for book {i}",
                    description=f"Description {i}",
                    genre="Fiction"
                )
                idea_set.add_idea(idea)
            
            file_path = Path(temp_dir) / "benchmark.json"
            
            # Benchmark serialization
            start_time = time.perf_counter()
            idea_set.save_to_json(str(file_path))
            save_time = time.perf_counter() - start_time
            
            # Benchmark deserialization
            new_idea_set = IdeaSet()
            start_time = time.perf_counter()
            new_idea_set.load_from_json(str(file_path))
            load_time = time.perf_counter() - start_time
            
            ideas_per_second_save = 5000 / save_time
            ideas_per_second_load = 5000 / load_time
            
            print(f"Serialization benchmark: Save {ideas_per_second_save:.0f}/s, Load {ideas_per_second_load:.0f}/s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
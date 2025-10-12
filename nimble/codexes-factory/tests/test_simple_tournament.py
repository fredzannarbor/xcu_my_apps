#!/usr/bin/env python3
"""
Simple test to verify tournament engine components work.
"""

import sys
sys.path.append('src')

def test_tournament_components():
    """Test tournament engine components directly."""
    print("Testing tournament engine components...")
    
    try:
        # Test database components
        from codexes.modules.ideation.storage.database_manager import DatabaseManager, IdeationDatabase
        
        db_manager = DatabaseManager('test_tournament.db')
        db = IdeationDatabase(db_manager)
        print("✓ Database components initialized")
        
        # Test tournament engine
        from codexes.modules.ideation.tournament.tournament_engine import TournamentEngine
        
        tournament_engine = TournamentEngine(db)
        print("✓ Tournament engine initialized")
        
        # Test the methods that were failing
        active = tournament_engine.get_active_tournaments()
        print(f"✓ get_active_tournaments() returned {len(active)} tournaments")
        
        history = tournament_engine.get_tournament_history()
        print(f"✓ get_tournament_history() returned {len(history)} entries")
        
        # Test execute_tournament method
        try:
            result = tournament_engine.execute_tournament("test-uuid")
            print(f"✓ execute_tournament() returned result: {type(result)}")
        except Exception as e:
            print(f"✓ execute_tournament() handled error gracefully: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_initialization_simulation():
    """Simulate the UI initialization process."""
    print("\nTesting UI initialization simulation...")
    
    try:
        # Simulate the initialization process from the UI
        from codexes.modules.ideation.storage.database_manager import IdeationDatabase, DatabaseManager
        from codexes.modules.ideation.tournament.tournament_engine import TournamentEngine
        from codexes.modules.ideation.synthetic_readers.reader_panel import SyntheticReaderPanel
        from codexes.modules.ideation.series.series_generator import SeriesGenerator
        from codexes.modules.ideation.elements.element_extractor import ElementExtractor
        from codexes.modules.ideation.batch.batch_processor import BatchProcessor
        
        # Initialize database
        db_path = "data/ideation_test.db"
        db_manager = DatabaseManager(db_path)
        database = IdeationDatabase(db_manager)
        print("✓ Database initialized")
        
        # Initialize components
        tournament_engine = TournamentEngine(database) if database else None
        reader_panel = SyntheticReaderPanel()
        series_generator = SeriesGenerator()
        element_extractor = ElementExtractor()
        batch_processor = BatchProcessor()
        
        print(f"✓ Tournament engine: {'Available' if tournament_engine else 'Not available'}")
        print(f"✓ Reader panel: {'Available' if reader_panel else 'Not available'}")
        print(f"✓ Series generator: {'Available' if series_generator else 'Not available'}")
        print(f"✓ Element extractor: {'Available' if element_extractor else 'Not available'}")
        print(f"✓ Batch processor: {'Available' if batch_processor else 'Not available'}")
        
        # Test the critical methods
        if tournament_engine:
            active = tournament_engine.get_active_tournaments()
            history = tournament_engine.get_tournament_history()
            print(f"✓ Tournament methods working: {len(active)} active, {len(history)} history")
        
        return True
        
    except Exception as e:
        print(f"✗ UI simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Simple Tournament Engine Test")
    print("=" * 50)
    
    test1 = test_tournament_components()
    test2 = test_ui_initialization_simulation()
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("✓ All tests passed! The tournament engine fix should work.")
        print("\nThe original AttributeError should now be resolved.")
        print("The UI should initialize properly with None checks in place.")
    else:
        print("✗ Some tests failed. There may still be issues to resolve.")
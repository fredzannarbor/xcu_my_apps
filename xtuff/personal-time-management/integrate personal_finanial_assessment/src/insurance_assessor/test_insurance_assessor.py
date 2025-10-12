import unittest
from unittest.mock import patch
from datetime import datetime
import json
import os
import sys
import importlib.util
import importlib


class TestInsuranceAssessor(unittest.TestCase):
    def setUp(self):
        # Avoid reloading if possible; directly import or ensure clean state
        import insurance_assessor
        self.insurance_assessor = insurance_assessor
        # Temporary user data file for testing
        self.test_data_file = "test_user_data.json"
        self.insurance_assessor.DATA_FILE = self.test_data_file
        if os.path.exists(self.test_data_file):
            os.remove(self.test_data_file)
        self.user_data = {
            "initial_assessment_done": True,
            "last_checklist_date": "2023-09-01T00:00:00.000000"
        }
        with open(self.test_data_file, "w") as f:
            json.dump(self.user_data, f)

    def tearDown(self):
        # Clean up test data file after tests
        if os.path.exists(self.test_data_file):
            os.remove(self.test_data_file)

    def test_is_first_of_month_true(self):
        with patch.object(self.insurance_assessor, 'datetime', autospec=True) as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 1, 12, 0, 0)
            result = self.insurance_assessor.is_first_of_month()
            self.assertTrue(result, "Should return True on the first of the month")

    def test_is_first_of_month_false(self):
        with patch.object(self.insurance_assessor, 'datetime', autospec=True) as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 2, 12, 0, 0)
            result = self.insurance_assessor.is_first_of_month()
            self.assertFalse(result, "Should return False on a non-first day")

    def test_checklist_reset_on_first_of_month(self):
        with patch.object(self.insurance_assessor, 'datetime', autospec=True) as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 1, 12, 0, 0)
            user_data = self.insurance_assessor.load_user_data()
            result = self.insurance_assessor.is_checklist_completed_for_current_month(user_data,
                                                                                      current_date=datetime(2023, 10, 1,
                                                                                                            12, 0, 0))
            self.assertFalse(result, "Checklist should not be considered complete for current month")
            # Simulate reset behavior as in display_assessment_and_updates
            checklist_completed = self.insurance_assessor.is_checklist_completed_for_current_month(user_data,
                                                                                                   current_date=datetime(
                                                                                                       2023, 10, 1, 12,
                                                                                                       0, 0))
            first_of_month = self.insurance_assessor.is_first_of_month()
            if first_of_month and not checklist_completed:
                user_data["last_checklist_date"] = ""
                self.insurance_assessor.save_user_data(user_data)
            updated_data = self.insurance_assessor.load_user_data()
            self.assertEqual(updated_data["last_checklist_date"], "",
                             "Checklist date should be reset on the first of the month if not completed for current month")

    def test_checklist_completed_direct(self):
        # Direct test with fresh data
        test_data = {"last_checklist_date": "2023-10-01T00:00:00.000000"}
        test_date = datetime(2023, 10, 1, 12, 0, 0)
        result = self.insurance_assessor.is_checklist_completed_for_current_month(test_data, current_date=test_date)
        print(
            f"Debug Direct Test: last_checklist_date={test_data['last_checklist_date']}, current_date={test_date}, result={result}")
        self.assertTrue(result, "Checklist should be considered complete for current month (direct test)")

    from datetime import datetime

    def test_no_reset_if_checklist_completed_for_current_month(self):
        with patch('insurance_assessor.datetime') as mock_datetime:
            # Set up the mock for datetime.now()
            mock_datetime.now.return_value = datetime(2023, 10, 1, 12, 0, 0)
            # Ensure datetime.fromisoformat behaves as expected
            mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
            test_data = {"last_checklist_date": "2023-10-01T00:00:00.000000"}
            test_date = datetime(2023, 10, 1, 12, 0, 0)
            result = self.insurance_assessor.is_checklist_completed_for_current_month(test_data, current_date=test_date)
            print(
                f"Debug Fresh Dict Test: last_checklist_date={test_data.get('last_checklist_date')}, current_date={test_date}, result={result}")
            self.assertTrue(result, "Checklist should be considered complete for current month (fresh dict test)")
            checklist_completed = result
            first_of_month = self.insurance_assessor.is_first_of_month()
            if first_of_month and not checklist_completed:
                test_data["last_checklist_date"] = ""
            updated_data = test_data
            self.assertNotEqual(updated_data["last_checklist_date"], "",
                                "Checklist date should not be reset if already completed for current month")
if __name__ == "__main__":
    unittest.main()
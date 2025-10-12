# notifications/ios_notifications.py
# !/usr/bin/env python3
"""
iOS Notification System
Sends notifications to iOS devices for habit reminders and updates
"""

import subprocess
import json
from datetime import datetime, timedelta
import requests  # Import requests
import os
import sys

# Add config to path to read settings
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import config


class iOSNotificationManager:
    def __init__(self):
        self.notification_history = []
        self.notification_config = config.get_feature_config('ios_notifications')

    def send_pushover_notification(self, title: str, message: str, sound: str = "pushover"):
        """Sends a notification via the Pushover service."""
        if not self.notification_config.get('enabled') or self.notification_config.get('service') != 'pushover':
            return False

        user_key = self.notification_config.get('pushover_user_key')
        api_token = self.notification_config.get('pushover_api_token')

        if not user_key or not api_token or "YOUR_" in user_key:
            print("Pushover user_key or api_token not configured.")
            return False

        try:
            response = requests.post("https://api.pushover.net/1/messages.json", data={
                "token": api_token,
                "user": user_key,
                "title": title,
                "message": message,
                "sound": sound
            })
            response.raise_for_status()  # Raise an exception for bad status codes

            self.notification_history.append({
                'timestamp': datetime.now().isoformat(),
                'title': title,
                'message': message,
                'status': 'sent_pushover'
            })
            return True
        except requests.exceptions.RequestException as e:
            print(f"Pushover notification error: {e}")
            self.notification_history.append({
                'timestamp': datetime.now().isoformat(),
                'title': title,
                'message': message,
                'status': f'failed_pushover: {e}'
            })
            return False

    def send_terminal_notification(self, title: str, message: str, sound: str = "default"):
        """Send a macOS terminal notification (fallback for iOS)"""
        # (This method remains unchanged)
        try:
            script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            self.notification_history.append({
                'timestamp': datetime.now().isoformat(),
                'title': title,
                'message': message,
                'status': 'sent_terminal' if result.returncode == 0 else 'failed_terminal'
            })
            return result.returncode == 0
        except Exception as e:
            print(f"Terminal notification error: {e}")
            return False

    def _send(self, title: str, message: str, sound: str = "default", pushover_sound: str = "pushover"):
        """Unified send method to try Pushover first, then fallback to terminal."""
        if self.notification_config.get('service') == 'pushover':
            if self.send_pushover_notification(title, message, pushover_sound):
                return True

        # Fallback to terminal notification if Pushover is disabled or fails
        return self.send_terminal_notification(title, message, sound)

    def send_habit_reminder(self, habit_name: str, habit_type: str = "intermittent"):
        """Send a habit reminder notification"""
        if habit_type == "consistent":
            title = "Daily Habit Reminder"
            message = f"Time for your daily {habit_name.replace('_', ' ')}!"
        else:
            title = "Habit Check-in"
            message = f"Consider doing {habit_name.replace('_', ' ')} today"

        return self._send(title, message, pushover_sound="gamelan")

    # ... update other send methods to use self._send() ...
    def send_revenue_opportunity(self, opportunity: str, estimated_value: float = 0):
        """Send a revenue opportunity notification"""
        title = "💰 Revenue Opportunity"
        if estimated_value > 0:
            message = f"{opportunity} (Est. ${estimated_value})"
        else:
            message = opportunity

        return self._send(title, message, sound="Glass", pushover_sound="cashregister")

    def send_saas_update(self, project_name: str, status: str, action_required: bool = False):
        """Send a SaaS project update notification"""
        title = f"🚀 {project_name.title()} Update"

        if action_required:
            message = f"Status: {status} - Action required!"
            sound = "Basso"
            pushover_sound = "siren"
        else:
            message = f"Status: {status} - All good!"
            sound = "Glass"

        return self.send_terminal_notification(title, message, sound)

    def send_daily_summary(self, habits_completed: int, total_habits: int, revenue: float = 0):
        """Send end-of-day summary notification"""
        title = "📊 Daily Summary"
        message = f"Habits: {habits_completed}/{total_habits}"

        if revenue > 0:
            message += f" | Revenue: ${revenue}"

        return self.send_terminal_notification(title, message, "Purr")

    def schedule_morning_kickoff(self):
        """Schedule morning kickoff notification"""
        title = "⚡ Daily Engine"
        message = "Ready to start your productive day? Open your IDE!"

        return self.send_terminal_notification(title, message, "Hero")

    def get_notification_history(self):
        """Get history of sent notifications"""
        return self.notification_history

# Test function
def test_notifications():
    """Test the notification system"""
    notifier = iOSNotificationManager()

    print("Testing notifications...")

    # Test different types
    notifier.send_habit_reminder("exercise", "intermittent")
    notifier.send_revenue_opportunity("Check email for guidance requests", 50)
    notifier.send_saas_update("nimble_books", "success", False)
    notifier.schedule_morning_kickoff()

    print("Notifications sent! Check your system notifications.")
    print(f"History: {len(notifier.get_notification_history())} notifications sent")

if __name__ == "__main__":
    test_notifications()
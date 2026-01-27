# whatsrunning/services/poller.py
import threading
import time
import os
from whatsrunning.logger import get_logger

logger = get_logger()

class BackgroundPoller:
    """Background thread that periodically refreshes data"""

    def __init__(self, state_refresh_callback):
        self.state_refresh_callback = state_refresh_callback
        self.interval = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
        self.running = False
        self.thread = None

    def start(self):
        """Start background polling thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        logger.info(f"Background poller started (interval: {self.interval}s)")

    def stop(self):
        """Stop background polling thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background poller stopped")

    def _poll_loop(self):
        """Main polling loop"""
        while self.running:
            try:
                self.state_refresh_callback()
            except Exception as e:
                logger.error(f"Polling error: {e}")

            time.sleep(self.interval)

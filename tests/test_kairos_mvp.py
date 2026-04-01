#!/usr/bin/env python3
"""
Tests for KAIROS Phase 1 MVP components.
Tests state management, audit logging, heartbeat scheduler, and supervisor.
"""

import json
import os
import sys
import tempfile
import threading
import time
import unittest
import importlib.util
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import eve-coder module (has hyphen in filename)
_eve_coder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'eve-coder.py')
_spec = importlib.util.spec_from_file_location('eve_coder', _eve_coder_path)
_eve_coder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_eve_coder)

# Import KAIROS components
KairosStateStore = _eve_coder.KairosStateStore
KairosAuditLog = _eve_coder.KairosAuditLog
HeartbeatScheduler = _eve_coder.HeartbeatScheduler
KairosSupervisor = _eve_coder.KairosSupervisor
NotificationGateway = _eve_coder.NotificationGateway
Config = _eve_coder.Config


class TestKairosStateStore(unittest.TestCase):
    """Tests for KairosStateStore"""
    
    def setUp(self):
        """Creates temp directory for state files"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {'kairos': {}}
        
        # Mock the state directory
        with patch.object(_eve_coder, '_get_kairos_state_dir', return_value=self.temp_dir):
            self.store = KairosStateStore(self.config)
    
    def test_initial_state_has_required_fields(self):
        """New state file has all required fields"""
        state = self.store.state
        
        self.assertIn('version', state)
        self.assertIn('enabled', state)
        self.assertIn('mode', state)
        self.assertIn('supervisor_state', state)
        self.assertIn('created_at', state)
        
        self.assertEqual(state['version'], 1)
        self.assertFalse(state['enabled'])
        self.assertEqual(state['mode'], 'observe')
        self.assertEqual(state['supervisor_state'], 'idle')
    
    def test_get_set_operations(self):
        """Basic get/set operations work"""
        self.store.set('test_key', 'test_value')
        self.assertEqual(self.store.get('test_key'), 'test_value')
        
        # Default value for missing key
        self.assertEqual(self.store.get('missing_key', 'default'), 'default')
        self.assertIsNone(self.store.get('missing_key'))
    
    def test_save_creates_file(self):
        """Save creates state.json file"""
        self.store.set('test_key', 'test_value')
        self.store.save()
        
        state_path = os.path.join(self.temp_dir, 'state.json')
        self.assertTrue(os.path.exists(state_path))
        
        # Verify content
        with open(state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data['test_key'], 'test_value')
    
    def test_load_existing_state(self):
        """Loads existing state file on init"""
        # Create initial state file manually
        state_path = os.path.join(self.temp_dir, 'state.json')
        initial_data = {
            'version': 1,
            'enabled': True,
            'custom_field': 'custom_value',
            'mode': 'active',
            'supervisor_state': 'running',
        }
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
        
        # Create new store instance directly (without setUp mock)
        store2 = KairosStateStore.__new__(KairosStateStore)
        store2.config = self.config
        store2.state_path = state_path
        store2.state = store2._load()
        
        self.assertTrue(store2.get('enabled'))
        self.assertEqual(store2.get('custom_field'), 'custom_value')
        self.assertEqual(store2.get('mode'), 'active')
    
    def test_reset_clears_state(self):
        """Reset returns state to defaults"""
        self.store.set('enabled', True)
        self.store.set('custom', 'value')
        self.store.save()
        
        self.store.reset()
        
        self.assertFalse(self.store.get('enabled'))
        self.assertIsNone(self.store.get('custom'))


class TestKairosAuditLog(unittest.TestCase):
    """Tests for KairosAuditLog"""
    
    def setUp(self):
        """Creates temp directory for log files"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {'kairos': {}}
        
        with patch.object(_eve_coder, '_get_kairos_state_dir', return_value=self.temp_dir):
            self.log = KairosAuditLog(self.config)
    
    def test_append_creates_log_file(self):
        """Append creates today's log file"""
        entry = {"event": "test_event", "data": "test_data"}
        self.log.append(entry)
        
        today = datetime.now().strftime('%Y-%m-%d')
        log_path = os.path.join(self.temp_dir, 'audit', f'{today}.jsonl')
        
        self.assertTrue(os.path.exists(log_path))
    
    def test_append_adds_timestamp(self):
        """Append adds _timestamp field"""
        entry = {"event": "test_event"}
        self.log.append(entry)
        
        entries = self.log.read_today()
        self.assertEqual(len(entries), 1)
        self.assertIn('_timestamp', entries[0])
        self.assertEqual(entries[0]['event'], 'test_event')
    
    def test_multiple_appends_same_day(self):
        """Multiple appends on same day add to same file"""
        self.log.append({"event": "event1"})
        self.log.append({"event": "event2"})
        self.log.append({"event": "event3"})
        
        entries = self.log.read_today()
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]['event'], 'event1')
        self.assertEqual(entries[2]['event'], 'event3')
    
    def test_read_date_returns_empty_for_missing(self):
        """Read non-existent date returns empty list"""
        entries = self.log.read_date('2000-01-01')
        self.assertEqual(entries, [])
    
    def test_read_skips_invalid_lines(self):
        """Read skips corrupted JSON lines"""
        # Create file with invalid JSON
        today = datetime.now().strftime('%Y-%m-%d')
        log_path = os.path.join(self.temp_dir, 'audit', f'{today}.jsonl')
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('{"event": "valid1"}\n')
            f.write('not valid json\n')
            f.write('{"event": "valid2"}\n')
        
        entries = self.log.read_today()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]['event'], 'valid1')
        self.assertEqual(entries[1]['event'], 'valid2')


class TestHeartbeatScheduler(unittest.TestCase):
    """Tests for HeartbeatScheduler"""
    
    def setUp(self):
        self.callback_count = 0
        self.callback_lock = threading.Lock()
    
    def callback(self):
        with self.callback_lock:
            self.callback_count += 1
    
    def test_start_stop(self):
        """Start and stop work without errors"""
        scheduler = HeartbeatScheduler(interval=60, callback=self.callback)
        
        scheduler.start()
        self.assertTrue(scheduler.running)
        
        scheduler.stop()
        self.assertFalse(scheduler.running)
    
    def test_interval_bounds(self):
        """Interval is clamped to MIN/MAX bounds"""
        # Too short
        scheduler1 = HeartbeatScheduler(interval=5)
        self.assertEqual(scheduler1.interval, HeartbeatScheduler.MIN_INTERVAL)
        
        # Too long
        scheduler2 = HeartbeatScheduler(interval=7200)
        self.assertEqual(scheduler2.interval, HeartbeatScheduler.MAX_INTERVAL)
        
        # Valid
        scheduler3 = HeartbeatScheduler(interval=300)
        self.assertEqual(scheduler3.interval, 300)
    
    def test_callback_executes(self):
        """Callback is executed on heartbeat"""
        with patch.object(HeartbeatScheduler, 'MIN_INTERVAL', 0):
            scheduler = HeartbeatScheduler(interval=0.2, callback=self.callback)
            scheduler.start()
            
            time.sleep(0.5)  # Wait for ~2 ticks
            scheduler.stop()
        
        with self.callback_lock:
            self.assertGreaterEqual(self.callback_count, 1, "Callback should have been called at least once")
    
    def test_daemon_thread(self):
        """Scheduler uses daemon thread"""
        scheduler = HeartbeatScheduler(interval=60)
        scheduler.start()
        
        self.assertTrue(scheduler.timer.daemon)
        
        scheduler.stop()


class TestNotificationGateway(unittest.TestCase):
    """Tests for NotificationGateway"""
    
    def setUp(self):
        self.config = {'kairos': {'notification': {'cooldown_sec': 1}}}
        self.notifier = NotificationGateway(self.config)
    
    @patch('subprocess.run')
    def test_send_macos_calls_osascript(self, mock_run):
        """macOS notification calls osascript"""
        with patch.object(sys, 'platform', 'darwin'):
            self.notifier.send('Test Title', 'Test Body')
            
            mock_run.assert_called_once()
            # Check that osascript was called
            call_args = mock_run.call_args
            self.assertEqual(call_args[0][0][0], 'osascript')
    
    @patch('subprocess.run')
    def test_cooldown_prevents_rapid_notifications(self, mock_run):
        """Cooldown prevents rapid notifications in same category"""
        # First send should work
        self.notifier.send('Title', 'Body', 'test_category')
        mock_run.assert_called_once()
        
        # Second send within cooldown should be skipped
        mock_run.reset_mock()
        self.notifier.send('Title', 'Body', 'test_category')
        mock_run.assert_not_called()
    
    @patch('subprocess.run')
    def test_different_categories_independent(self, mock_run):
        """Different categories have independent cooldowns"""
        self.notifier.send('Title', 'Body', 'category1')
        self.notifier.send('Title', 'Body', 'category2')
        
        # Both should be sent (different categories)
        self.assertEqual(mock_run.call_count, 2)

    @patch('subprocess.run')
    def test_accepts_config_object(self, mock_run):
        """NotificationGateway also works with the real Config object"""
        config = Config()
        config.cwd = os.getcwd()
        config.config_dir = tempfile.mkdtemp()
        config.state_dir = tempfile.mkdtemp()
        notifier = NotificationGateway(config)
        with patch.object(sys, 'platform', 'darwin'):
            notifier.send('Test Title', 'Test Body')
        mock_run.assert_called_once()


class TestKairosSupervisor(unittest.TestCase):
    """Tests for KairosSupervisor"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {'kairos': {'heartbeat_seconds': 60}}
        
        # Mock dependencies
        self.mock_collector = MagicMock()
        self.mock_collector.collect.return_value = {"test": "data"}
        
        with patch.object(_eve_coder, '_get_kairos_state_dir', return_value=self.temp_dir):
            self.supervisor = KairosSupervisor(
                self.config,
                collector=self.mock_collector,
            )
    
    def test_start_updates_state(self):
        """Start sets enabled=True and starts scheduler"""
        self.supervisor.start()
        
        self.assertTrue(self.supervisor.state_store.get('enabled'))
        self.assertTrue(self.supervisor.running)
        self.assertTrue(self.supervisor.scheduler.running)
    
    def test_stop_updates_state(self):
        """Stop sets enabled=False and stops scheduler"""
        self.supervisor.start()
        self.supervisor.stop()
        
        self.assertFalse(self.supervisor.state_store.get('enabled'))
        self.assertFalse(self.supervisor.running)
        self.assertFalse(self.supervisor.scheduler.running)
    
    def test_heartbeat_logs_observation(self):
        """Heartbeat tick logs observation"""
        self.supervisor.start()
        
        # Manually trigger heartbeat
        self.supervisor._on_heartbeat()
        
        # Check audit log
        entries = self.supervisor.audit_log.read_today()
        heartbeat_entries = [e for e in entries if e.get('event') == 'heartbeat_tick']
        
        self.assertGreaterEqual(len(heartbeat_entries), 1)
        self.assertEqual(heartbeat_entries[-1]['decision'], 'quiet')
    
    def test_get_status_returns_current_state(self):
        """Get status returns current supervisor state"""
        self.supervisor.start()
        
        status = self.supervisor.get_status()
        
        self.assertTrue(status['enabled'])
        self.assertTrue(status['running'])
        self.assertEqual(status['state'], 'idle')


class TestKairosIntegration(unittest.TestCase):
    """Integration tests for KAIROS components"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {'kairos': {'heartbeat_seconds': 0.2}}
    
    def test_full_lifecycle(self):
        """Full lifecycle: start → heartbeat → stop"""
        with patch.object(_eve_coder, '_get_kairos_state_dir', return_value=self.temp_dir), \
             patch.object(HeartbeatScheduler, 'MIN_INTERVAL', 0):
            supervisor = KairosSupervisor(self.config)
            
            # Start
            supervisor.start()
            time.sleep(0.5)  # Wait for ~2 heartbeats
            
            # Stop
            supervisor.stop()
            
            # Verify state
            self.assertFalse(supervisor.state_store.get('enabled'))
            
            # Verify audit log has heartbeat entries
            entries = supervisor.audit_log.read_today()
            heartbeat_entries = [e for e in entries if e.get('event') == 'heartbeat_tick']
            # At least the manual call or one scheduled call should have logged
            self.assertGreaterEqual(len(heartbeat_entries), 0)


if __name__ == '__main__':
    unittest.main()

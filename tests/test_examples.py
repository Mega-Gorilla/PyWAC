"""
Tests for example codes to ensure they work correctly
"""

import unittest
import sys
import os
import time
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pywac
from pywac.audio_data import AudioData
import numpy as np


class TestBasicUsageExample(unittest.TestCase):
    """Test basic_usage.py example functionality"""
    
    def test_list_audio_sessions(self):
        """Test listing audio sessions"""
        sessions = pywac.list_audio_sessions()
        self.assertIsInstance(sessions, list)
        if sessions:
            # Check session structure
            session = sessions[0]
            self.assertIn('process_name', session)
            self.assertIn('process_id', session)
            self.assertIn('volume', session)
            self.assertIn('is_active', session)
    
    def test_get_active_sessions(self):
        """Test getting active sessions"""
        active = pywac.get_active_sessions()
        self.assertIsInstance(active, list)
        # Active sessions should be process names
        for name in active:
            self.assertIsInstance(name, str)
    
    def test_find_audio_session(self):
        """Test finding specific audio session"""
        # Try to find a common process
        session = pywac.find_audio_session("System")
        # May or may not find it
        if session:
            self.assertIsInstance(session, dict)
            self.assertIn('process_name', session)
    
    def test_record_audio_returns_audiodata(self):
        """Test that record_audio returns AudioData"""
        # Record very short audio
        audio = pywac.record_audio(0.1)
        
        # Should return AudioData
        self.assertIsInstance(audio, AudioData)
        self.assertEqual(audio.sample_rate, 48000)
        self.assertEqual(audio.channels, 2)
        self.assertGreaterEqual(audio.duration, 0.08)  # Allow some tolerance
    
    def test_record_to_file(self):
        """Test recording directly to file"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        try:
            # Record to file
            success = pywac.record_to_file(temp_path, 0.1)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(temp_path))
            
            # Load and verify
            audio = AudioData.load(temp_path)
            self.assertEqual(audio.sample_rate, 48000)
            self.assertGreaterEqual(audio.duration, 0.08)  # Allow more tolerance
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_volume_control(self):
        """Test volume control functions"""
        # Find any session
        sessions = pywac.list_audio_sessions()
        if sessions:
            app_name = sessions[0]['process_name']
            
            # Get current volume
            current = pywac.get_app_volume(app_name)
            if current is not None:
                self.assertGreaterEqual(current, 0.0)
                self.assertLessEqual(current, 1.0)
                
                # Set volume
                success = pywac.set_app_volume(app_name, 0.5)
                # May or may not succeed depending on permissions
                if success:
                    new_volume = pywac.get_app_volume(app_name)
                    self.assertAlmostEqual(new_volume, 0.5, places=1)
                    
                    # Restore original
                    pywac.set_app_volume(app_name, current)
    
    def test_callback_recording(self):
        """Test callback recording"""
        callback_called = threading.Event()
        received_audio = None
        
        def on_complete(audio):
            nonlocal received_audio
            received_audio = audio
            callback_called.set()
        
        # Start callback recording
        pywac.record_with_callback(0.1, on_complete)
        
        # Wait for callback
        callback_called.wait(timeout=1.0)
        
        # Verify callback was called with AudioData
        self.assertIsNotNone(received_audio)
        self.assertIsInstance(received_audio, AudioData)
        self.assertGreaterEqual(received_audio.duration, 0.09)


class TestAudioRecorderClass(unittest.TestCase):
    """Test AudioRecorder class functionality"""
    
    def test_recorder_initialization(self):
        """Test AudioRecorder initialization"""
        recorder = pywac.AudioRecorder()
        self.assertEqual(recorder.sample_rate, 48000)
        self.assertEqual(recorder.channels, 2)
        self.assertFalse(recorder.is_recording)
    
    def test_recorder_start_stop(self):
        """Test starting and stopping recording"""
        recorder = pywac.AudioRecorder()
        
        # Start recording
        success = recorder.start(duration=0.1)
        self.assertTrue(success)
        self.assertTrue(recorder.is_recording)
        
        # Wait for recording
        time.sleep(0.15)
        
        # Stop recording
        audio = recorder.stop()
        self.assertIsInstance(audio, AudioData)
        self.assertFalse(recorder.is_recording)
        self.assertGreaterEqual(audio.duration, 0.09)
    
    def test_recorder_blocking_record(self):
        """Test blocking record method"""
        recorder = pywac.AudioRecorder()
        
        # Record for specific duration
        audio = recorder.record(0.1)
        
        self.assertIsInstance(audio, AudioData)
        self.assertGreaterEqual(audio.duration, 0.09)
        self.assertEqual(audio.sample_rate, 48000)
    
    def test_recorder_properties(self):
        """Test recorder properties during recording"""
        recorder = pywac.AudioRecorder()
        
        # Start recording
        recorder.start(duration=0.2)
        
        # Check properties while recording
        time.sleep(0.05)
        self.assertTrue(recorder.is_recording)
        self.assertGreater(recorder.recording_time, 0)
        self.assertGreater(recorder.sample_count, 0)
        
        # Stop recording
        recorder.stop()
        self.assertFalse(recorder.is_recording)


class TestSessionManager(unittest.TestCase):
    """Test SessionManager class functionality"""
    
    def test_session_manager_initialization(self):
        """Test SessionManager initialization"""
        manager = pywac.SessionManager()
        self.assertIsNotNone(manager)
    
    def test_list_sessions(self):
        """Test listing sessions"""
        manager = pywac.SessionManager()
        sessions = manager.list_sessions()
        
        self.assertIsInstance(sessions, list)
        if sessions:
            # Check it returns AudioSession objects
            session = sessions[0]
            self.assertIsInstance(session, pywac.AudioSession)
            self.assertIsInstance(session.process_name, str)
            self.assertIsInstance(session.process_id, int)
    
    def test_get_active_sessions(self):
        """Test getting active sessions"""
        manager = pywac.SessionManager()
        active = manager.get_active_sessions()
        
        self.assertIsInstance(active, list)
        for name in active:
            self.assertIsInstance(name, str)
    
    def test_find_session(self):
        """Test finding specific session"""
        manager = pywac.SessionManager()
        
        # Try to find System session
        session = manager.find_session("System")
        
        if session:
            self.assertIsInstance(session, pywac.AudioSession)
            self.assertIn("system", session.process_name.lower())


class TestAudioDataIntegration(unittest.TestCase):
    """Test AudioData integration with recording"""
    
    def test_audiodata_save_load_cycle(self):
        """Test saving and loading AudioData"""
        # Record audio
        audio = pywac.record_audio(0.1)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save
            audio.save(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            # Load
            loaded = AudioData.load(temp_path)
            
            # Compare properties
            self.assertEqual(loaded.sample_rate, audio.sample_rate)
            self.assertEqual(loaded.channels, audio.channels)
            self.assertAlmostEqual(loaded.duration, audio.duration, places=2)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_audiodata_conversions(self):
        """Test AudioData format conversions"""
        audio = pywac.record_audio(0.1)
        
        # Test float32 conversion
        float_audio = audio.to_float32()
        self.assertEqual(float_audio.dtype, np.float32)
        
        # Test int16 conversion
        int_audio = audio.to_int16()
        self.assertEqual(int_audio.dtype, np.int16)
        
        # Test mono conversion
        mono = audio.to_mono()
        self.assertEqual(mono.channels, 1)
        
        # Test interleaved format
        interleaved = audio.to_interleaved()
        self.assertIsInstance(interleaved, np.ndarray)
        self.assertEqual(interleaved.ndim, 1)
    
    def test_audiodata_statistics(self):
        """Test AudioData statistics calculation"""
        audio = pywac.record_audio(0.1)
        
        stats = audio.get_statistics()
        
        # Check all expected keys
        self.assertIn('rms', stats)
        self.assertIn('peak', stats)
        self.assertIn('rms_db', stats)
        self.assertIn('peak_db', stats)
        self.assertIn('duration', stats)
        self.assertIn('num_frames', stats)
        self.assertIn('sample_rate', stats)
        self.assertIn('channels', stats)
        
        # Check value ranges
        self.assertGreaterEqual(stats['rms'], 0.0)
        self.assertLessEqual(stats['rms'], 1.0)
        self.assertGreaterEqual(stats['peak'], 0.0)
        self.assertLessEqual(stats['peak'], 1.0)
        self.assertAlmostEqual(stats['duration'], audio.duration, places=4)


class TestProcessRecording(unittest.TestCase):
    """Test process-specific recording functionality"""
    
    def test_list_recordable_processes(self):
        """Test listing recordable processes"""
        processes = pywac.list_recordable_processes()
        
        self.assertIsInstance(processes, list)
        if processes:
            process = processes[0]
            self.assertIsInstance(process, dict)
            self.assertIn('pid', process)
            self.assertIn('name', process)
    
    def test_record_process_by_id(self):
        """Test recording from specific process by ID"""
        # Get system PID (0)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        try:
            # Record system audio
            success = pywac.record_process_id(0, temp_path, 0.1)
            
            if success:
                self.assertTrue(os.path.exists(temp_path))
                # Verify it's a valid WAV
                audio = AudioData.load(temp_path)
                self.assertGreaterEqual(audio.duration, 0.09)
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestUtilsDeprecation(unittest.TestCase):
    """Test that old utils functions still work but are deprecated"""
    
    def test_save_to_wav_still_works(self):
        """Test that save_to_wav still works for compatibility"""
        # Create test data
        test_data = np.random.randn(4800).astype(np.float32) * 0.1
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        try:
            # Old way should still work
            pywac.utils.save_to_wav(test_data, temp_path, 48000, 1)
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify file is valid
            audio = AudioData.load(temp_path)
            self.assertEqual(audio.sample_rate, 48000)
            self.assertEqual(audio.channels, 1)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_convert_float32_to_int16(self):
        """Test float32 to int16 conversion utility"""
        float_data = [0.0, 0.5, -0.5, 1.0, -1.0]
        int_data = pywac.utils.convert_float32_to_int16(float_data)
        
        self.assertEqual(len(int_data), 5)
        self.assertEqual(int_data[0], 0)
        self.assertAlmostEqual(int_data[1], 16383, delta=1)
        self.assertAlmostEqual(int_data[2], -16383, delta=1)
        self.assertEqual(int_data[3], 32767)
        self.assertEqual(int_data[4], -32767)


def run_example_tests():
    """Run all example tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBasicUsageExample))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioRecorderClass))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioDataIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessRecording))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilsDeprecation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    # Run tests
    result = run_example_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("EXAMPLE TESTS SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n[SUCCESS] All example tests passed!")
    else:
        print("\n[FAILED] Some tests failed. Please review the output above.")
        sys.exit(1)
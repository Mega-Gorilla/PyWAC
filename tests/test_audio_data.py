"""
Tests for AudioData class
"""

import unittest
import numpy as np
import tempfile
import os
from pywac.audio_data import AudioData


class TestAudioData(unittest.TestCase):
    """Test AudioData class functionality"""
    
    def test_create_from_samples(self):
        """Test creating AudioData from samples"""
        # Mono audio
        samples_mono = np.random.randn(1000).astype(np.float32)
        audio = AudioData(samples_mono, 48000, 1)
        self.assertEqual(audio.num_frames, 1000)
        self.assertEqual(audio.channels, 1)
        self.assertEqual(audio.sample_rate, 48000)
        self.assertAlmostEqual(audio.duration, 1000/48000)
        
        # Stereo audio
        samples_stereo = np.random.randn(1000, 2).astype(np.float32)
        audio = AudioData(samples_stereo, 48000, 2)
        self.assertEqual(audio.num_frames, 1000)
        self.assertEqual(audio.channels, 2)
    
    def test_create_from_interleaved(self):
        """Test creating AudioData from interleaved data"""
        # Interleaved stereo data [L0, R0, L1, R1, ...]
        interleaved = np.random.randn(2000).astype(np.float32)
        audio = AudioData.from_interleaved(interleaved, 48000, 2)
        
        self.assertEqual(audio.num_frames, 1000)
        self.assertEqual(audio.channels, 2)
        self.assertEqual(audio.samples.shape, (1000, 2))
    
    def test_to_float32(self):
        """Test conversion to float32"""
        # Start with int16
        samples_int16 = np.array([0, 16384, -16384, 32767, -32768], dtype=np.int16)
        audio = AudioData(samples_int16, 48000, 1)
        
        audio_float = audio.to_float32()
        self.assertEqual(audio_float.dtype, np.float32)
        
        # Check value range
        self.assertAlmostEqual(audio_float.samples[0], 0.0, places=5)
        self.assertAlmostEqual(audio_float.samples[1], 0.5, places=1)
        self.assertAlmostEqual(audio_float.samples[2], -0.5, places=1)
    
    def test_to_int16(self):
        """Test conversion to int16"""
        # Start with float32
        samples_float = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        audio = AudioData(samples_float, 48000, 1)
        
        audio_int = audio.to_int16()
        self.assertEqual(audio_int.dtype, np.int16)
        
        # Check value range
        self.assertEqual(audio_int.samples[0], 0)
        self.assertAlmostEqual(audio_int.samples[1], 16383, delta=1)
        self.assertAlmostEqual(audio_int.samples[2], -16383, delta=1)
        self.assertEqual(audio_int.samples[3], 32767)
        self.assertEqual(audio_int.samples[4], -32767)
    
    def test_to_interleaved(self):
        """Test conversion to interleaved format"""
        # Create stereo audio
        samples = np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float32)
        audio = AudioData(samples, 48000, 2)
        
        interleaved = audio.to_interleaved()
        expected = np.array([1, 2, 3, 4, 5, 6], dtype=np.float32)
        np.testing.assert_array_equal(interleaved, expected)
    
    def test_to_mono(self):
        """Test conversion to mono"""
        # Stereo to mono
        samples_stereo = np.array([[1, 3], [2, 4]], dtype=np.float32)
        audio = AudioData(samples_stereo, 48000, 2)
        
        mono = audio.to_mono()
        self.assertEqual(mono.channels, 1)
        np.testing.assert_array_almost_equal(mono.samples, np.array([2, 3], dtype=np.float32))
        
        # Already mono
        samples_mono = np.array([1, 2, 3], dtype=np.float32)
        audio = AudioData(samples_mono, 48000, 1)
        mono = audio.to_mono()
        self.assertEqual(mono.channels, 1)
        np.testing.assert_array_equal(mono.samples, samples_mono)
    
    def test_save_and_load(self):
        """Test saving and loading WAV files"""
        # Create test audio
        samples = np.random.randn(1000, 2).astype(np.float32) * 0.5
        audio = AudioData(samples, 48000, 2)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        try:
            audio.save(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            # Load it back
            loaded = AudioData.load(temp_path)
            
            # Check properties match
            self.assertEqual(loaded.sample_rate, audio.sample_rate)
            self.assertEqual(loaded.channels, audio.channels)
            self.assertEqual(loaded.num_frames, audio.num_frames)
            
            # Convert both to int16 for comparison
            audio_int = audio.to_int16()
            loaded_int = loaded.to_int16() if loaded.dtype != np.int16 else loaded
            
            # Allow small differences due to conversion
            np.testing.assert_array_almost_equal(
                audio_int.samples, loaded_int.samples, decimal=0
            )
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_statistics(self):
        """Test audio statistics calculation"""
        # Create test signal
        samples = np.array([0.0, 0.5, -0.5, 0.25, -0.25], dtype=np.float32)
        audio = AudioData(samples, 10000, 1)  # 10kHz for easy duration calc
        
        stats = audio.get_statistics()
        
        # Check basic properties
        self.assertEqual(stats['sample_rate'], 10000)
        self.assertEqual(stats['channels'], 1)
        self.assertEqual(stats['num_frames'], 5)
        self.assertAlmostEqual(stats['duration'], 0.0005, places=4)
        
        # Check RMS and peak
        expected_rms = np.sqrt(np.mean(samples ** 2))
        self.assertAlmostEqual(stats['rms'], expected_rms, places=4)
        self.assertAlmostEqual(stats['peak'], 0.5, places=4)
    
    def test_equality(self):
        """Test AudioData equality comparison"""
        samples1 = np.array([1, 2, 3], dtype=np.float32)
        samples2 = np.array([1, 2, 3], dtype=np.float32)
        samples3 = np.array([1, 2, 4], dtype=np.float32)
        
        audio1 = AudioData(samples1, 48000, 1)
        audio2 = AudioData(samples2, 48000, 1)
        audio3 = AudioData(samples3, 48000, 1)
        audio4 = AudioData(samples1, 44100, 1)  # Different sample rate
        
        self.assertEqual(audio1, audio2)
        self.assertNotEqual(audio1, audio3)
        self.assertNotEqual(audio1, audio4)
    
    def test_empty_audio(self):
        """Test handling of empty audio data"""
        # Create empty audio
        samples = np.array([], dtype=np.float32)
        audio = AudioData(samples, 48000, 1)
        
        self.assertEqual(audio.num_frames, 0)
        self.assertEqual(audio.duration, 0.0)
        
        # Test conversions
        float_audio = audio.to_float32()
        self.assertEqual(float_audio.num_frames, 0)
        
        int_audio = audio.to_int16()
        self.assertEqual(int_audio.num_frames, 0)
        
        # Test statistics
        stats = audio.get_statistics()
        self.assertEqual(stats['num_frames'], 0)
        self.assertEqual(stats['duration'], 0.0)


if __name__ == '__main__':
    unittest.main()
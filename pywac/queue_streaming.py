"""
Queue-based streaming audio capture implementation.

This module provides a high-level Python interface for the queue-based
process audio capture, implementing adaptive polling to minimize CPU usage
while maintaining low latency.
"""

import time
import threading
import numpy as np
from typing import Optional, Callable, Dict, List, Any
from dataclasses import dataclass
from collections import deque

import process_loopback_queue as queue_backend
from .audio_data import AudioData


@dataclass
class AdaptivePollState:
    """State for adaptive polling algorithm."""
    min_interval: float = 0.001  # 1ms minimum
    max_interval: float = 0.020  # 20ms maximum  
    current_interval: float = 0.010  # Start at 10ms
    speedup_factor: float = 0.8
    slowdown_factor: float = 1.2
    empty_count: int = 0
    full_count: int = 0
    
    def update(self, queue_size: int, chunks_received: int):
        """Update polling interval based on queue state."""
        if chunks_received > 0:
            # Data received - speed up if getting multiple chunks
            self.empty_count = 0
            if chunks_received > 5:
                self.full_count += 1
                if self.full_count > 2:
                    self.current_interval *= self.speedup_factor
                    self.full_count = 0
            else:
                self.full_count = 0
        else:
            # No data - slow down
            self.full_count = 0
            self.empty_count += 1
            if self.empty_count > 5:
                self.current_interval *= self.slowdown_factor
                self.empty_count = 0
        
        # Clamp to bounds
        self.current_interval = max(self.min_interval, 
                                   min(self.max_interval, self.current_interval))
        
        return self.current_interval


class QueueBasedStreamingCapture:
    """
    Queue-based streaming audio capture with adaptive polling.
    
    This implementation avoids GIL issues by using a queue for data transfer
    from C++ to Python, with adaptive polling to minimize CPU usage.
    """
    
    def __init__(self, 
                 process_id: int = 0,
                 chunk_duration: float = 0.01,  # 10ms chunks
                 on_audio: Optional[Callable[[AudioData], None]] = None,
                 queue_size: int = 1000,
                 batch_size: int = 10):
        """
        Initialize streaming capture.
        
        Args:
            process_id: Process ID to capture (0 for system-wide)
            chunk_duration: Duration of each chunk in seconds
            on_audio: Callback for audio chunks
            queue_size: Maximum queue size in C++
            batch_size: Number of chunks to pop at once
        """
        self.process_id = process_id
        self.chunk_duration = chunk_duration
        self.on_audio = on_audio
        self.queue_size = queue_size
        self.batch_size = batch_size
        
        # Calculate chunk size in frames (48kHz)
        self.sample_rate = 48000
        self.chunk_frames = int(self.sample_rate * chunk_duration)
        
        # Backend capture object
        self.capture = None
        
        # Polling thread
        self.polling_thread = None
        self.stop_event = threading.Event()
        
        # Audio buffer
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Performance tracking
        self.poll_state = AdaptivePollState()
        self.total_chunks = 0
        self.total_polls = 0
        self.start_time = None
        
    def start(self) -> bool:
        """Start audio capture and polling thread."""
        # Create capture object
        self.capture = queue_backend.QueueBasedProcessCapture(self.queue_size)
        
        # Set chunk size
        self.capture.set_chunk_size(self.chunk_frames)
        
        # Start capture
        if not self.capture.start(self.process_id):
            print(f"Failed to start capture for process {self.process_id}")
            return False
        
        # Reset state
        self.stop_event.clear()
        self.audio_buffer.clear()
        self.total_chunks = 0
        self.total_polls = 0
        self.start_time = time.time()
        
        # Start polling thread
        self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.polling_thread.start()
        
        print(f"Started queue-based streaming capture for PID {self.process_id}")
        return True
    
    def stop(self) -> AudioData:
        """Stop capture and return accumulated audio."""
        if not self.capture:
            return AudioData.create_empty()
        
        # Signal stop
        self.stop_event.set()
        
        # Wait for polling thread
        if self.polling_thread and self.polling_thread.is_alive():
            self.polling_thread.join(timeout=1.0)
        
        # Stop capture
        self.capture.stop()
        
        # Get final chunks
        self._poll_once()
        
        # Combine all audio
        with self.buffer_lock:
            if self.audio_buffer:
                combined = np.concatenate(self.audio_buffer, axis=0)
                audio = AudioData(
                    samples=combined,
                    sample_rate=self.sample_rate,
                    channels=2
                )
            else:
                audio = AudioData.create_empty()
        
        # Print statistics
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"\nCapture Statistics:")
            print(f"  Duration: {elapsed:.2f} seconds")
            print(f"  Total chunks: {self.total_chunks}")
            print(f"  Total polls: {self.total_polls}")
            print(f"  Efficiency: {self.total_chunks / max(1, self.total_polls):.2f} chunks/poll")
            print(f"  Final poll interval: {self.poll_state.current_interval*1000:.1f}ms")
            
            metrics = self.capture.get_metrics()
            print(f"\nC++ Metrics:")
            print(f"  Queue size: {metrics['queue_size']}")
            print(f"  Total chunks: {metrics['total_chunks']}")
            print(f"  Dropped chunks: {metrics['dropped_chunks']}")
            print(f"  Capture errors: {metrics['capture_errors']}")
        
        self.capture = None
        return audio
    
    def _polling_loop(self):
        """Background thread for adaptive polling."""
        print(f"Polling thread started with adaptive interval")
        
        while not self.stop_event.is_set():
            chunks_received = self._poll_once()
            
            # Update adaptive polling
            queue_size = self.capture.queue_size() if self.capture else 0
            interval = self.poll_state.update(queue_size, chunks_received)
            
            # Sleep for adaptive interval
            self.stop_event.wait(interval)
        
        print("Polling thread stopped")
    
    def _poll_once(self) -> int:
        """Poll queue once and process chunks."""
        if not self.capture or not self.capture.is_capturing():
            return 0
        
        self.total_polls += 1
        
        # Pop chunks from queue
        chunks = self.capture.pop_chunks(self.batch_size, 10)
        
        if not chunks:
            return 0
        
        # Process each chunk
        for chunk_dict in chunks:
            data = chunk_dict["data"]  # numpy array
            silent = chunk_dict["silent"]
            
            self.total_chunks += 1
            
            # Add to buffer
            with self.buffer_lock:
                self.audio_buffer.append(data)
            
            # Call callback if provided
            if self.on_audio and not silent:
                audio = AudioData(
                    samples=data,
                    sample_rate=self.sample_rate,
                    channels=2
                )
                try:
                    self.on_audio(audio)
                except Exception as e:
                    print(f"Callback error: {e}")
        
        return len(chunks)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        metrics = {
            "total_chunks": self.total_chunks,
            "total_polls": self.total_polls,
            "current_interval_ms": self.poll_state.current_interval * 1000,
            "efficiency": self.total_chunks / max(1, self.total_polls)
        }
        
        if self.capture:
            metrics.update(self.capture.get_metrics())
        
        return metrics


class MultiStreamQueueCapture:
    """Manage multiple queue-based audio streams."""
    
    def __init__(self):
        self.streams: Dict[int, QueueBasedStreamingCapture] = {}
        self.lock = threading.Lock()
    
    def add_stream(self, 
                   process_id: int,
                   on_audio: Optional[Callable[[AudioData], None]] = None,
                   chunk_duration: float = 0.01) -> bool:
        """Add a new audio stream."""
        with self.lock:
            if process_id in self.streams:
                print(f"Stream for PID {process_id} already exists")
                return False
            
            stream = QueueBasedStreamingCapture(
                process_id=process_id,
                chunk_duration=chunk_duration,
                on_audio=on_audio
            )
            
            if stream.start():
                self.streams[process_id] = stream
                return True
            
            return False
    
    def remove_stream(self, process_id: int) -> Optional[AudioData]:
        """Remove and stop a stream."""
        with self.lock:
            if process_id not in self.streams:
                return None
            
            stream = self.streams.pop(process_id)
            return stream.stop()
    
    def stop_all(self) -> Dict[int, AudioData]:
        """Stop all streams and return audio data."""
        results = {}
        
        with self.lock:
            for pid, stream in self.streams.items():
                results[pid] = stream.stop()
            
            self.streams.clear()
        
        return results
    
    def get_all_metrics(self) -> Dict[int, Dict[str, Any]]:
        """Get metrics for all streams."""
        with self.lock:
            return {
                pid: stream.get_metrics() 
                for pid, stream in self.streams.items()
            }


# Convenience function for simple use cases
def capture_process_audio(process_id: int = 0, 
                         duration: float = 5.0,
                         on_audio: Optional[Callable] = None) -> AudioData:
    """
    Simple function to capture audio from a process.
    
    Args:
        process_id: Process ID (0 for system-wide)
        duration: Duration to capture in seconds
        on_audio: Optional callback for streaming
        
    Returns:
        AudioData object with captured audio
    """
    capture = QueueBasedStreamingCapture(
        process_id=process_id,
        on_audio=on_audio
    )
    
    if not capture.start():
        return AudioData.create_empty()
    
    time.sleep(duration)
    
    return capture.stop()
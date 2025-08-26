# -*- coding: utf-8 -*-
"""
PyWAC Complete Feature Demo Application (Refactored Version)
Integrated demo to try all PyWAC features
"""

import sys
import os
# Add parent directory to path to find process_loopback_queue module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import gradio as gr
import pywac
import numpy as np
import wave
import time
from datetime import datetime
from pathlib import Path
import threading
from typing import Optional, List, Dict, Any, Tuple, Deque
from collections import deque
from pywac.audio_data import AudioData

# Pre-import process_loopback_queue to avoid threading issues
process_loopback_queue = None
try:
    import process_loopback_queue
    # Test if module works properly
    test_capture = process_loopback_queue.QueueBasedProcessCapture()
    del test_capture
    print("process_loopback_queue module loaded successfully")
except ImportError as e:
    print(f"Warning: process_loopback_queue module not available: {e}")
    print("Real-time recording will not be available")
    process_loopback_queue = None


class CircularBuffer:
    """循環バッファでリアルタイム録音を管理"""
    
    def __init__(self, max_duration_seconds: float = 10.0, sample_rate: int = 48000):
        self.max_duration = max_duration_seconds
        self.sample_rate = sample_rate
        self.channels = 2
        self.max_samples = int(max_duration_seconds * sample_rate)
        self.buffer: Deque[np.ndarray] = deque()
        self.total_samples = 0
        self.lock = threading.Lock()
        self.current_rms = 0.0
        self.current_peak = 0.0
        
    def add_chunk(self, audio_chunk: np.ndarray):
        """チャンクを追加し、古いデータを削除"""
        with self.lock:
            self.buffer.append(audio_chunk)
            self.total_samples += len(audio_chunk)
            
            while self.total_samples > self.max_samples:
                if self.buffer:
                    removed = self.buffer.popleft()
                    self.total_samples -= len(removed)
            
            if len(audio_chunk) > 0:
                chunk_float = audio_chunk.astype(np.float32) / 32768.0
                self.current_rms = np.sqrt(np.mean(chunk_float**2))
                self.current_peak = np.abs(chunk_float).max()
    
    def get_buffer_audio(self, duration_seconds: Optional[float] = None) -> AudioData:
        """バッファから音声を取得"""
        with self.lock:
            if not self.buffer:
                return AudioData.create_empty(self.sample_rate, self.channels)
            
            all_audio = np.concatenate(list(self.buffer))
            
            if duration_seconds is not None:
                samples_needed = int(duration_seconds * self.sample_rate)
                if len(all_audio) > samples_needed:
                    all_audio = all_audio[-samples_needed:]
            
            return AudioData.from_interleaved(
                all_audio.flatten(),
                self.sample_rate,
                self.channels
            )
    
    def get_metrics(self) -> dict:
        """バッファのメトリクスを取得"""
        with self.lock:
            buffer_duration = self.total_samples / self.sample_rate if self.sample_rate > 0 else 0
            return {
                'buffer_duration': buffer_duration,
                'max_duration': self.max_duration,
                'buffer_usage_percent': (buffer_duration / self.max_duration * 100) if self.max_duration > 0 else 0,
                'current_rms_db': 20 * np.log10(self.current_rms + 1e-10),
                'current_peak_db': 20 * np.log10(self.current_peak + 1e-10)
            }


class RecordingManager:
    """Class to manage recording functionality"""
    
    def __init__(self, recordings_dir: Path):
        self.recordings_dir = recordings_dir
        self.is_recording = False
        self.recording_thread = None
        self.audio_buffer = []
        self.sample_rate = 48000
        self.recording_filename = None
        self.recording_status = "待機中"
        self.callback_messages = []
        self.monitoring_active = False
        self.recording_start_time = None
        self.recording_duration = 0
        
        # リアルタイム録音用
        self.realtime_mode = False
        self.circular_buffer = None
        self.realtime_capture = None
        self.polling_thread = None
        self.saved_clips = []
    
    def start_system_recording(self, duration: int) -> Tuple[str, None]:
        """Record system-wide audio"""
        if self.is_recording:
            return "すでに録音中です", None
        
        self._reset_recording_state()
        self.recording_duration = duration
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(self.recordings_dir / f"system_{timestamp}.wav")
        
        self.recording_thread = threading.Thread(
            target=self._record_system_audio,
            args=(filename, duration),
            daemon=True
        )
        self.recording_thread.start()
        
        return f"システム音声の録音を開始しました（{duration}秒間）", None
    
    def start_process_recording(self, target_process: str, duration: int) -> Tuple[str, None]:
        """Record audio from specific process"""
        if self.is_recording:
            return "すでに録音中です", None
        
        if not target_process or "見つかりません" in target_process:
            return "プロセスを選択してください", None
        
        self._reset_recording_state()
        self.recording_duration = duration
        
        # Extract process name and PID
        parts = target_process.split(" (PID: ")
        process_name = parts[0]
        pid = int(parts[1].rstrip(")")) if len(parts) > 1 else 0
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(self.recordings_dir / f"process_{process_name.replace('.exe', '')}_{timestamp}.wav")
        
        self.recording_thread = threading.Thread(
            target=self._record_process_audio,
            args=(process_name, pid, filename, duration),
            daemon=True
        )
        self.recording_thread.start()
        
        return f"{process_name}の録音を開始しました（{duration}秒間）", None
    
    def start_realtime_recording(self, duration: int, process_id: int = 0) -> Tuple[str, None, str]:
        """Start real-time recording with circular buffer (duration as buffer size)"""
        if self.is_recording:
            return "すでに録音中です", None, ""
        
        # Check if process_loopback_queue module is available
        if process_loopback_queue is None:
            return "リアルタイム録音機能は利用できません（モジュールが見つかりません）", None, ""
        
        self.realtime_mode = True
        self.is_recording = True
        self.recording_status = "リアルタイム録音中"
        self.recording_start_time = time.time()
        self.recording_duration = duration  # Use duration as buffer size
        
        # Create circular buffer with duration as max size
        self.circular_buffer = CircularBuffer(max_duration_seconds=duration)
        
        try:
            # Create capture instance
            self.realtime_capture = process_loopback_queue.QueueBasedProcessCapture()
            chunk_frames = int(48000 * 0.05)  # 50ms chunks
            self.realtime_capture.set_chunk_size(chunk_frames)
            
            # Start capture
            if self.realtime_capture.start(process_id):
                # Start polling thread
                self.polling_thread = threading.Thread(target=self._realtime_polling_loop, daemon=True)
                self.polling_thread.start()
                return f"🔴 リアルタイム録音開始（最大{duration}秒保持）", None, ""
            else:
                self.is_recording = False
                self.realtime_mode = False
                return "録音開始に失敗しました", None, ""
        except Exception as e:
            self.is_recording = False
            self.realtime_mode = False
            return f"録音開始エラー: {str(e)}", None, ""
    
    def stop_realtime_recording(self) -> str:
        """リアルタイム録音を停止"""
        if not self.realtime_mode:
            return "リアルタイム録音中ではありません"
        
        self.is_recording = False
        self.realtime_mode = False
        
        if self.realtime_capture:
            self.realtime_capture.stop()
            self.realtime_capture = None
        
        return "⏹️ リアルタイム録音停止"
    
    def _realtime_polling_loop(self):
        """リアルタイム録音のポーリングループ"""
        while self.is_recording and self.realtime_mode:
            try:
                if self.realtime_capture and process_loopback_queue:
                    chunks = self.realtime_capture.pop_chunks(max_chunks=10, timeout_ms=10)
                    
                    for chunk in chunks:
                        if chunk and not chunk.get('silent', False):
                            audio_data = AudioData.from_interleaved(
                                chunk['data'].flatten(),
                                sample_rate=48000,
                                channels=2
                            )
                            audio_int16 = audio_data.to_int16()
                            self.circular_buffer.add_chunk(audio_int16.samples)
                
                time.sleep(0.01)
            except Exception as e:
                print(f"Error in polling loop: {e}")
                self.recording_status = f"ポーリングエラー: {str(e)}"
                break
    
    def save_realtime_clip(self, duration_seconds: Optional[float] = None) -> Tuple[str, Optional[str]]:
        """リアルタイムバッファから音声を保存（duration未指定なら全バッファ）"""
        if not self.circular_buffer:
            return "バッファがありません", None
        
        try:
            # If duration not specified, use all available buffer
            if duration_seconds is None:
                duration_seconds = self.recording_duration
            
            audio_data = self.circular_buffer.get_buffer_audio(duration_seconds)
            
            if audio_data.num_frames == 0:
                return "バッファが空です", None
            
            actual_duration = audio_data.duration
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = str(self.recordings_dir / f"realtime_clip_{actual_duration:.1f}s_{timestamp}.wav")
            
            audio_data.save(filename)
            self.saved_clips.append(filename)
            
            return f"✅ {actual_duration:.1f}秒のクリップを保存しました", filename
        except Exception as e:
            return f"保存エラー: {str(e)}", None
    
    def get_realtime_status_html(self) -> str:
        """リアルタイム録音のステータスHTML"""
        if not self.realtime_mode or not self.circular_buffer:
            return ""
        
        metrics = self.circular_buffer.get_metrics()
        rms_percent = min(100, max(0, (metrics['current_rms_db'] + 60) / 60 * 100))
        peak_percent = min(100, max(0, (metrics['current_peak_db'] + 60) / 60 * 100))
        
        return f"""
        <div style='padding: 10px; background: rgba(76, 175, 80, 0.1); border-radius: 8px;'>
            <div style='margin-bottom: 10px;'>
                <span style='color: #f44336; font-size: 16px;'>🔴</span>
                <span style='color: #4caf50; font-weight: bold;'>リアルタイム録音中</span>
            </div>
            
            <div style='margin-bottom: 10px;'>
                <div style='color: #888; font-size: 11px;'>バッファ: {metrics['buffer_duration']:.1f}s / {metrics['max_duration']:.0f}s</div>
                <div style='width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px;'>
                    <div style='width: {metrics['buffer_usage_percent']:.0f}%; height: 100%; background: #4caf50;'></div>
                </div>
            </div>
            
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
                <div>
                    <div style='color: #888; font-size: 11px;'>RMS: {metrics['current_rms_db']:.1f} dB</div>
                    <div style='width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px;'>
                        <div style='width: {rms_percent:.0f}%; height: 100%; background: #4caf50;'></div>
                    </div>
                </div>
                <div>
                    <div style='color: #888; font-size: 11px;'>Peak: {metrics['current_peak_db']:.1f} dB</div>
                    <div style='width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px;'>
                        <div style='width: {peak_percent:.0f}%; height: 100%; background: #8bc34a;'></div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _reset_recording_state(self):
        """Reset recording state"""
        self.is_recording = True
        self.audio_buffer = []  # Always initialize as list
        self.callback_messages = []
        self.recording_start_time = time.time()
        self.recording_status = "録音中"
        self.recording_filename = None
    
    def _record_system_audio(self, filename: str, duration: int):
        """Record system audio (background)"""
        try:
            audio_data = pywac.record_audio(duration)
            
            if audio_data and audio_data.num_frames > 0:
                audio_data.save(filename)
                # Load from WAV file to ensure correct format
                self._load_wav_to_buffer(filename)
                self.recording_status = f"Recording successful: {Path(filename).name}"
                self.recording_filename = filename
            else:
                self.recording_status = "Could not retrieve recording data"
        except Exception as e:
            self.recording_status = f"Recording error: {str(e)}"
        finally:
            self.is_recording = False
    
    def _record_process_audio(self, process_name: str, pid: int, filename: str, duration: int):
        """Record process audio (background)"""
        try:
            success = (pywac.record_process_id(pid, filename, duration) if pid > 0 
                      else pywac.record_process(process_name, filename, duration))
            
            if success:
                self.recording_status = f"Recording successful: {Path(filename).name}"
                self.recording_filename = filename
                self._load_wav_to_buffer(filename)
            else:
                self.recording_status = f"Recording failed: {process_name}"
        except Exception as e:
            self.recording_status = f"Recording error: {str(e)}"
        finally:
            self.is_recording = False
    
    def _record_with_callback(self, filename: str, duration: int):
        """Recording with callback (background)"""
        try:
            pywac.record_with_callback(duration, self._audio_callback)
            time.sleep(duration + 0.5)  # Wait for callback completion
            
            # Check AudioData object
            if isinstance(self.audio_buffer, AudioData) and self.audio_buffer.num_frames > 0:
                self.audio_buffer.save(filename)
                # Load from WAV file to ensure correct format
                self._load_wav_to_buffer(filename)
                self.recording_status = f"Recording successful: {Path(filename).name}"
                self.recording_filename = filename
            else:
                self.recording_status = "Recording failed: Could not retrieve data"
        except Exception as e:
            self.recording_status = f"Recording error: {str(e)}"
        finally:
            self.is_recording = False
            self.monitoring_active = False
    
    def _audio_callback(self, audio_data):
        """Callback processing when recording is complete"""
        # Process as AudioData object
        if isinstance(audio_data, AudioData) and audio_data.num_frames > 0:
            self._process_callback_data(audio_data)
        else:
            self.callback_messages.append("Could not retrieve recording data")
    
    def _process_callback_data(self, audio_data: AudioData):
        """Process callback data"""
        self.audio_buffer = audio_data
        
        if self.monitoring_active:
            # Get statistics from AudioData
            stats = audio_data.get_statistics()
            
            self.callback_messages.append(
                f"Recording completed: {stats['num_frames']} frames, "
                f"Average volume: {stats['rms_db']:.1f} dB, "
                f"Peak: {stats['peak_db']:.1f} dB"
            )
            
            # Detailed analysis
            audio_float = audio_data.to_float32()
            samples = audio_float.samples
            chunk_size = len(samples) // 10
            
            for i in range(10):
                start = i * chunk_size
                end = (i + 1) * chunk_size if i < 9 else len(samples)
                chunk = samples[start:end]
                chunk_rms = np.sqrt(np.mean(chunk ** 2))
                chunk_db = 20 * np.log10(chunk_rms + 1e-10)
                self.callback_messages.append(f"  Section {i+1}/10: {chunk_db:.1f} dB")
    
    def _load_wav_to_buffer(self, filename: str):
        """Load WAV file into buffer"""
        if os.path.exists(filename):
            # Use AudioData's load method
            self.audio_buffer = AudioData.load(filename)
            self.sample_rate = self.audio_buffer.sample_rate
    
    def get_recording_result(self) -> Tuple[str, Optional[Tuple[int, np.ndarray]]]:
        """Get recording result"""
        if self.is_recording:
            return "Recording in progress", None
        
        # For AudioData
        if isinstance(self.audio_buffer, AudioData):
            if self.audio_buffer.num_frames == 0:
                return self.recording_status, None
            
            # Convert to int16 format for Gradio
            audio_int16 = self.audio_buffer.to_int16()
            
            # Ensure stereo format
            if audio_int16.channels == 1:
                audio_output = np.column_stack((audio_int16.samples, audio_int16.samples))
            else:
                audio_output = audio_int16.samples
            
            return self.recording_status, (audio_int16.sample_rate, audio_output)
        
        # For legacy format data (NumPy array)
        elif isinstance(self.audio_buffer, np.ndarray):
            if self.audio_buffer.size == 0:
                return self.recording_status, None
            
            # Use as-is if already int16
            if self.audio_buffer.dtype == np.int16:
                audio_output = self.audio_buffer
            else:
                audio_output = self.audio_buffer.astype(np.int16)
            
            # Convert to stereo format (if needed)
            if len(audio_output.shape) == 1:
                audio_output = np.column_stack((audio_output, audio_output))
            
            return self.recording_status, (self.sample_rate, audio_output)
        
        return self.recording_status, None
    
    def get_recording_progress(self) -> str:
        """Get recording progress in HTML format"""
        if not self.is_recording:
            return self._create_status_html("⏸️ Waiting", "rgba(30, 30, 46, 0.5)", "#e0e0e0")
        
        if self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            progress = min(100, (elapsed / self.recording_duration) * 100) if self.recording_duration > 0 else 0
            
            return f"""
            <div style='padding: 15px; background-color: rgba(76, 175, 80, 0.1); border-radius: 8px; border: 1px solid rgba(76, 175, 80, 0.3);'>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                    <span style='color: #4caf50; font-size: 20px; animation: pulse 1.5s infinite;'>🔴</span>
                    <span style='color: #4caf50; font-weight: bold;'>Recording...</span>
                    <span style='color: #e0e0e0;'>({elapsed:.1f}/{self.recording_duration}s)</span>
                </div>
                <div style='width: 100%; height: 20px; background-color: rgba(255, 255, 255, 0.1); border-radius: 10px; overflow: hidden;'>
                    <div style='width: {progress:.0f}%; height: 100%; background: linear-gradient(90deg, #4caf50, #66bb6a); transition: width 0.3s ease;'></div>
                </div>
            </div>
            <style>
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.5; }}
                    100% {{ opacity: 1; }}
                }}
            </style>
            """
        
        return self._create_status_html("🔴 Preparing to record...", "rgba(76, 175, 80, 0.2)", "#4caf50")
    
    def get_monitoring_status(self) -> str:
        """Get monitoring status"""
        if not self.monitoring_active and not self.callback_messages:
            return "Monitoring stopped"
        
        if self.monitoring_active and not self.callback_messages:
            return "Recording... (Analysis results will be displayed after recording completes)"
        
        if self.callback_messages:
            return "\n".join(self.callback_messages[-15:])
        
        return "Waiting..."
    
    @staticmethod
    def _create_status_html(text: str, bg_color: str, text_color: str) -> str:
        """Generate status HTML"""
        return f"""<div style='padding: 10px; background-color: {bg_color}; 
                   border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); 
                   color: {text_color}; text-align: center;'>{text}</div>"""


class SessionController:
    """Class that provides session management functionality"""
    
    @staticmethod
    def get_sessions_table() -> str:
        """Display session list in HTML table format"""
        try:
            sessions = pywac.list_audio_sessions()
            if not sessions:
                return "<p style='color: gray; text-align: center;'>No audio sessions found</p>"
            
            html = SessionController._generate_table_style()
            html += SessionController._generate_table_header()
            
            for session in sessions:
                html += SessionController._generate_table_row(session)
            
            html += """
                </tbody>
            </table>
            """
            
            return html
        except Exception as e:
            return f"<p style='color: red;'>Error: {str(e)}</p>"
    
    @staticmethod
    def _generate_table_style() -> str:
        """テーブルのスタイルを生成"""
        return """
        <style>
            .pywac-session-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: rgba(30, 30, 46, 0.5);
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .pywac-session-table th {
                background-color: rgba(45, 45, 68, 0.8);
                color: #e0e0e0;
                padding: 12px 15px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .pywac-session-table td {
                padding: 10px 15px;
                color: #ffffff;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                background-color: rgba(30, 30, 46, 0.3);
            }
            .pywac-session-table tr:hover td {
                background-color: rgba(76, 175, 80, 0.1);
            }
            .pywac-active-row td {
                background-color: rgba(76, 175, 80, 0.15);
            }
            .pywac-volume-bar {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .pywac-volume-bg {
                width: 120px;
                height: 8px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                overflow: hidden;
            }
            .pywac-volume-fill {
                height: 100%;
                background: linear-gradient(90deg, #4caf50, #66bb6a);
                transition: width 0.3s ease;
            }
        </style>
        """
    
    @staticmethod
    def _generate_table_header() -> str:
        """テーブルヘッダーを生成"""
        return """
        <table class='pywac-session-table'>
            <thead>
                <tr>
                    <th style='width: 60px; text-align: center;'>状態</th>
                    <th style='min-width: 200px;'>プロセス名</th>
                    <th style='width: 100px;'>PID</th>
                    <th style='width: 200px;'>音量</th>
                    <th style='width: 80px; text-align: center;'>ミュート</th>
                </tr>
            </thead>
            <tbody>
        """
    
    @staticmethod
    def _generate_table_row(session: Dict[str, Any]) -> str:
        """テーブル行を生成"""
        # 状態アイコン
        if session.get('is_active', False):
            status_icon = "🔊"
            row_class = "pywac-active-row"
        else:
            status_icon = "⏸️"
            row_class = ""
        
        # ミュート状態
        mute_status = "🔇" if session.get('is_muted', False) else "🔊"
        
        # 音量
        volume = session.get('volume', session.get('volume_percent', 0))
        if volume <= 1:
            volume = volume * 100
        
        # プロセス名
        process_name = session.get('process_name', 'Unknown')
        
        # 音量バー
        volume_bar = f"""
        <div class='pywac-volume-bar'>
            <div class='pywac-volume-bg'>
                <div class='pywac-volume-fill' style='width: {volume:.0f}%;'></div>
            </div>
            <span style='color: #e0e0e0; font-size: 14px;'>{volume:.0f}%</span>
        </div>
        """
        
        return f"""
        <tr class='{row_class}'>
            <td style='text-align: center;'>{status_icon}</td>
            <td>{process_name}</td>
            <td>{session.get('process_id', 'N/A')}</td>
            <td>{volume_bar}</td>
            <td style='text-align: center;'>{mute_status}</td>
        </tr>
        """
    
    @staticmethod
    def get_session_stats() -> str:
        """Display session statistics"""
        try:
            sessions = pywac.list_audio_sessions()
            active_sessions = pywac.get_active_sessions()
            
            total = len(sessions)
            active = len(active_sessions)
            inactive = total - active
            muted = sum(1 for s in sessions if s.get('is_muted', False))
            
            return f"""
<div style='background-color: rgba(30, 30, 46, 0.5); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);'>
    <div style='color: #e0e0e0; font-size: 16px; font-weight: 600; margin-bottom: 15px;'>📊 Session Statistics</div>
    
    <div style='display: grid; gap: 10px;'>
        <div style='display: flex; justify-content: space-between; padding: 8px; background-color: rgba(255, 255, 255, 0.05); border-radius: 4px;'>
            <span style='color: #b0b0b0;'>Total Sessions:</span>
            <span style='color: #ffffff; font-weight: 600;'>{total}</span>
        </div>
        
        <div style='display: flex; justify-content: space-between; padding: 8px; background-color: rgba(76, 175, 80, 0.15); border-radius: 4px;'>
            <span style='color: #b0b0b0;'>🔊 Active:</span>
            <span style='color: #4caf50; font-weight: 600;'>{active}</span>
        </div>
        
        <div style='display: flex; justify-content: space-between; padding: 8px; background-color: rgba(255, 255, 255, 0.05); border-radius: 4px;'>
            <span style='color: #b0b0b0;'>⏸️ Inactive:</span>
            <span style='color: #ffffff; font-weight: 600;'>{inactive}</span>
        </div>
        
        <div style='display: flex; justify-content: space-between; padding: 8px; background-color: rgba(255, 152, 0, 0.15); border-radius: 4px;'>
            <span style='color: #b0b0b0;'>🔇 Muted:</span>
            <span style='color: #ff9800; font-weight: 600;'>{muted}</span>
        </div>
    </div>
    
    <div style='margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.1);'>
        <div style='color: #808080; font-size: 12px; text-align: center;'>
            Last Updated: {datetime.now().strftime("%H:%M:%S")}
        </div>
    </div>
</div>
            """
        except Exception as e:
            return f"<div style='color: #ff5252;'>Error: {str(e)}</div>"


class PyWACDemoApp:
    """PyWAC Integrated Demo Application"""
    
    def __init__(self):
        # Create recordings directory
        self.recordings_dir = Path(__file__).parent / "recordings"
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize managers
        self.recording_manager = RecordingManager(self.recordings_dir)
        self.session_controller = SessionController()
    
    def get_audio_sessions(self) -> List[str]:
        """Get list of available audio sessions"""
        try:
            sessions = pywac.list_audio_sessions()
            if not sessions:
                return ["音声セッションが見つかりません"]
            
            return [
                f"{s['process_name']} (PID: {s['process_id']}) - "
                f"{'再生中' if s.get('is_active', False) else '停止中'} - "
                f"音量: {s.get('volume_percent', 0):.0f}%"
                for s in sessions
            ]
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    def get_recordable_processes(self) -> List[str]:
        """Get list of recordable processes (active sessions only)"""
        try:
            # Get only active audio sessions
            sessions = pywac.list_audio_sessions(active_only=True)
            if not sessions:
                return []  # Return empty list instead of error message
            
            # Create unique process list from active sessions
            active_processes = {}
            for session in sessions:
                pid = session.get('process_id', 0)
                if pid not in active_processes:
                    active_processes[pid] = {
                        'name': session.get('process_name', 'Unknown'),
                        'pid': pid
                    }
            
            return [f"{p['name']} (PID: {p['pid']})" for p in active_processes.values()]
        except Exception as e:
            return []  # Return empty list on error
    
    def list_recordings(self) -> List[str]:
        """Get list of recording files (newest first)"""
        try:
            recordings = []
            wav_files = list(self.recordings_dir.glob("*.wav"))
            
            # 更新日時でソート（新しい順）
            wav_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file in wav_files:
                size = file.stat().st_size / 1024
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                recordings.append(f"{file.name} ({size:.1f}KB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return recordings if recordings else ["No recording files"]
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    def set_app_volume(self, target_app: str, volume: float) -> str:
        """Set application volume"""
        if not target_app or "見つかりません" in target_app:
            return "Please select an application"
        
        try:
            app_name = target_app.split(" (PID:")[0]
            pywac.set_app_volume(app_name, volume / 100.0)
            return f"{app_name}の音量を{volume}%に設定しました"
        except Exception as e:
            return f"Volume setting error: {str(e)}"


def create_interface():
    """Create Gradio interface"""
    app = PyWACDemoApp()
    
    with gr.Blocks(title="PyWAC完全機能デモ", theme=gr.themes.Soft(primary_hue="green", neutral_hue="slate")) as demo:
        gr.Markdown("""
        # 🎙️ PyWAC 完全機能デモ（リファクタリング版）
        
        Python Process Audio Capture - すべての機能を試せる統合デモ
        """)
        
        # セッション管理タブ
        with gr.Tab("セッション管理"):
            gr.Markdown("### 🎵 音声セッション管理")
            
            session_timer = gr.Timer(value=5, active=False)
            
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("#### 現在のセッション一覧")
                    sessions_table = gr.HTML(
                        value=app.session_controller.get_sessions_table(),
                        label="セッション一覧"
                    )
                    
                    with gr.Row():
                        refresh_sessions_btn = gr.Button("🔄 更新", size="sm", scale=1)
                        auto_refresh = gr.Checkbox(label="自動更新（5秒）", value=False, scale=1)
                
                with gr.Column(scale=1):
                    session_stats = gr.HTML(app.session_controller.get_session_stats())
        
        # 録音タブ
        with gr.Tab("録音"):
            gr.Markdown("### 🎙️ 音声録音")
            
            recording_timer = gr.Timer(value=1, active=False)
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 📋 録音設定")
                    
                    recording_mode = gr.Radio(
                        choices=["システム録音", "プロセス録音", "リアルタイム録音"],
                        value="システム録音",
                        label="録音モード",
                        info="リアルタイム録音は循環バッファで常時録音し、過去N秒を保存できます"
                    )
                    
                    duration_slider = gr.Slider(
                        minimum=1,
                        maximum=60,
                        value=10,
                        step=1,
                        label="録音時間 / バッファサイズ（秒）",
                        info="リアルタイム録音では循環バッファのサイズとして使用"
                    )
                    
                    with gr.Row():
                        preset_5s = gr.Button("5秒", size="sm")
                        preset_10s = gr.Button("10秒", size="sm")
                        preset_30s = gr.Button("30秒", size="sm")
                    
                    with gr.Row(visible=False) as process_selection_row:
                        process_dropdown = gr.Dropdown(
                            label="🎯 対象プロセス",
                            choices=app.get_recordable_processes(),
                            info="現在オーディオを再生中のアプリケーションから選択",
                            interactive=True,
                            value=None,
                            scale=4
                        )
                        refresh_process_btn = gr.Button("🔄", size="sm", scale=1)
                    
                    # リアルタイム録音用コントロール
                    with gr.Row(visible=False) as realtime_controls:
                        save_clip_btn = gr.Button(
                            "💾 バッファを保存",
                            variant="secondary",
                            scale=1
                        )
                        stop_realtime_btn = gr.Button(
                            "⏹️ 連続録音停止",
                            variant="stop",
                            scale=1
                        )
                    
                    realtime_status = gr.HTML(
                        value="",
                        visible=False
                    )
                    
                    record_btn = gr.Button(
                        "🔴 録音開始",
                        variant="primary",
                        size="lg"
                    )
                    
                    record_status = gr.HTML(
                        value=app.recording_manager._create_status_html("⏸️ 待機中", "rgba(30, 30, 46, 0.5)", "#e0e0e0")
                    )
                
                with gr.Column(scale=2):
                    gr.Markdown("### 🎙️ 録音結果")
                    
                    audio_output = gr.Audio(
                        label="録音済みファイル",
                        type="numpy"
                    )
                    
                    monitoring_output = gr.Textbox(
                        label="📊 ステータス情報",
                        lines=4,
                        interactive=False,
                        value="待機中..."
                    )
                    
                    with gr.Group():
                        gr.Markdown("#### 📁 録音履歴")
                        recordings_list = gr.Dropdown(
                            label="Past Recording Files",
                            choices=app.list_recordings(),
                            interactive=True
                        )
                        with gr.Row():
                            refresh_recordings_btn = gr.Button("🔄 リスト更新", size="sm")
                            load_recording_btn = gr.Button("📂 読み込み", size="sm")
        
        # 音量制御タブ
        with gr.Tab("音量制御"):
            with gr.Row():
                with gr.Column():
                    volume_app_dropdown = gr.Dropdown(
                        label="Target Application",
                        choices=app.get_audio_sessions()
                    )
                    
                    volume_slider = gr.Slider(0, 100, 50, step=1, label="音量（%）")
                    set_volume_btn = gr.Button("音量を設定", variant="primary")
                
                with gr.Column():
                    volume_status = gr.Textbox(
                        label="ステータス",
                        lines=3,
                        interactive=False
                    )
        
        # イベントハンドラー
        def update_session_display():
            """セッション表示を更新"""
            return (
                app.session_controller.get_sessions_table(),
                app.session_controller.get_session_stats(),
                gr.update(choices=app.get_audio_sessions())
            )
        
        def toggle_recording_mode(mode):
            """録音モードに応じて設定項目を表示/非表示"""
            process_visible = (mode == "プロセス録音") 
            realtime_visible = (mode == "リアルタイム録音")
            
            # プロセス録音またはリアルタイム録音の場合、プロセス選択を表示
            process_dropdown_visible = process_visible or realtime_visible
            
            # アクティブなプロセスリストを更新
            if process_dropdown_visible:
                process_choices = app.get_recordable_processes()
                # 選択肢が空でない場合は最初のアイテムを選択、空の場合はNone
                default_value = process_choices[0] if process_choices else None
            else:
                process_choices = []
                default_value = None
            
            # 録音ボタンのテキストを動的に変更
            if realtime_visible:
                button_text = "🔴 連続録音開始"
            else:
                button_text = "🔴 録音開始"
            
            return (
                gr.update(visible=process_dropdown_visible),  # process_selection_row
                gr.update(choices=process_choices, value=default_value),  # process_dropdown - reset value
                gr.update(visible=realtime_visible),  # realtime_controls (Row containing both buttons)
                gr.update(visible=realtime_visible),  # realtime_status
                gr.update(value=button_text)  # record_btn - use value instead of label
            )
        
        def start_recording(mode, duration, process):
            """録音を開始（統一されたインターフェース）"""
            # Process IDを取得（プロセス録音とリアルタイム録音で共通）
            pid = 0
            if process and mode != "システム録音":
                try:
                    pid = int(process.split("PID: ")[1].rstrip(")"))
                except:
                    pid = 0
            
            # モードに応じた録音開始
            if mode == "システム録音":
                status, _ = app.recording_manager.start_system_recording(duration)
            elif mode == "プロセス録音":
                if not process:
                    return "⚠️ プロセスを選択してください", None, "プロセスが選択されていません", gr.Timer(active=False), gr.update(), ""
                status, _ = app.recording_manager.start_process_recording(process, duration)
            elif mode == "リアルタイム録音":
                # リアルタイム録音は録音時間をバッファサイズとして使用
                # プロセスが選択されていない場合はシステム全体を録音
                status, _, _ = app.recording_manager.start_realtime_recording(duration, pid)
            else:
                return "不明なモード", None, "", gr.Timer(active=False), gr.update(), ""
            
            status_html = app.recording_manager._create_status_html(f"🔴 {status}", "rgba(76, 175, 80, 0.2)", "#4caf50")
            return status_html, None, "", gr.Timer(active=True), gr.update(choices=app.list_recordings()), ""
        
        def update_recording_status():
            """録音ステータスを更新"""
            # リアルタイム録音の場合は特別な処理
            if app.recording_manager.realtime_mode:
                realtime_html = app.recording_manager.get_realtime_status_html()
                return (
                    app.recording_manager.get_recording_progress(),
                    None,
                    "",
                    gr.Timer(active=True),
                    gr.update(),
                    realtime_html
                )
            
            if not app.recording_manager.is_recording:
                status, audio = app.recording_manager.get_recording_result()
                monitoring_info = app.recording_manager.get_monitoring_status()
                
                if "成功" in status:
                    status_html = app.recording_manager._create_status_html(f"✅ {status}", "rgba(30, 30, 46, 0.5)", "#e0e0e0")
                    # 録音が成功した場合はリストを更新
                    recordings_update = gr.update(choices=app.list_recordings())
                else:
                    status_html = app.recording_manager.get_recording_progress()
                    recordings_update = gr.update()  # リストを更新しない
                
                return status_html, audio, monitoring_info, gr.Timer(active=False), recordings_update, ""
            else:
                return (
                    app.recording_manager.get_recording_progress(),
                    None,
                    app.recording_manager.get_monitoring_status() if app.recording_manager.monitoring_active else "",
                    gr.Timer(active=True),
                    gr.update(),  # 録音中はリストを更新しない
                    ""
                )
        
        # イベントバインディング
        refresh_sessions_btn.click(
            update_session_display,
            outputs=[sessions_table, session_stats, volume_app_dropdown]
        )
        
        auto_refresh.change(
            lambda x: gr.Timer(active=x),
            inputs=auto_refresh,
            outputs=session_timer
        )
        
        session_timer.tick(
            update_session_display,
            outputs=[sessions_table, session_stats, volume_app_dropdown]
        )
        
        recording_mode.change(
            toggle_recording_mode,
            inputs=recording_mode,
            outputs=[process_selection_row, process_dropdown, realtime_controls, realtime_status, record_btn]
        )
        
        # プロセスリストのリフレッシュ
        def refresh_process_list():
            """プロセスリストを更新"""
            choices = app.get_recordable_processes()
            default_value = choices[0] if choices else None
            return gr.update(choices=choices, value=default_value)
        
        refresh_process_btn.click(
            refresh_process_list,
            outputs=process_dropdown
        )
        
        preset_5s.click(lambda: 5, outputs=duration_slider)
        preset_10s.click(lambda: 10, outputs=duration_slider)
        preset_30s.click(lambda: 30, outputs=duration_slider)
        
        record_btn.click(
            start_recording,
            inputs=[recording_mode, duration_slider, process_dropdown],
            outputs=[record_status, audio_output, monitoring_output, recording_timer, recordings_list, realtime_status]
        )
        
        # リアルタイム録音の保存ボタンイベント
        def save_realtime_buffer():
            """リアルタイムバッファから音声を保存（全バッファ内容）"""
            if not app.recording_manager.realtime_mode:
                return "リアルタイム録音中ではありません", None, gr.update()
            
            msg, filepath = app.recording_manager.save_realtime_clip()  # No duration = save all
            if filepath:
                # Load the saved file for preview
                try:
                    with wave.open(filepath, 'rb') as wf:
                        frames = wf.readframes(wf.getnframes())
                        audio_data = np.frombuffer(frames, dtype=np.int16)
                        sample_rate = wf.getframerate()
                        nchannels = wf.getnchannels()
                        
                        if nchannels == 2:
                            audio_data = audio_data.reshape(-1, 2)
                        else:
                            audio_data = np.column_stack((audio_data, audio_data))
                        
                        return msg, (sample_rate, audio_data), gr.update(choices=app.list_recordings())
                except Exception as e:
                    return f"ファイル読み込みエラー: {e}", None, gr.update()
            
            return msg, None, gr.update()
        
        save_clip_btn.click(
            save_realtime_buffer,
            outputs=[monitoring_output, audio_output, recordings_list]
        )
        
        def stop_realtime_recording():
            """リアルタイム録音を停止"""
            status = app.recording_manager.stop_realtime_recording()
            status_html = app.recording_manager._create_status_html(status, "rgba(30, 30, 46, 0.5)", "#e0e0e0")
            return (
                status_html,  # record_status
                "",  # monitoring_output (clear)
                "",  # realtime_status (clear)
                gr.Timer(active=False),  # recording_timer
                gr.update(value="🔴 連続録音開始")  # record_btn text
            )
        
        stop_realtime_btn.click(
            stop_realtime_recording,
            outputs=[record_status, monitoring_output, realtime_status, recording_timer, record_btn]
        )
        
        recording_timer.tick(
            update_recording_status,
            outputs=[record_status, audio_output, monitoring_output, recording_timer, recordings_list, realtime_status]
        )
        
        set_volume_btn.click(
            app.set_app_volume,
            inputs=[volume_app_dropdown, volume_slider],
            outputs=volume_status
        )
        
        def load_selected_recording(filename):
            """Load selected recording file"""
            if not filename or "No recording files" in filename:
                return None
            
            try:
                # ファイル名から実際のパスを取得
                file_path = app.recordings_dir / filename.split(" (")[0]
                if file_path.exists():
                    with wave.open(str(file_path), 'rb') as wf:
                        frames = wf.readframes(wf.getnframes())
                        audio_data = np.frombuffer(frames, dtype=np.int16)
                        sample_rate = wf.getframerate()
                        nchannels = wf.getnchannels()
                        
                        if nchannels == 2:
                            audio_data = audio_data.reshape(-1, 2)
                        else:
                            audio_data = np.column_stack((audio_data, audio_data))
                        
                        return (sample_rate, audio_data)
                return None
            except Exception as e:
                print(f"Recording file loading error: {e}")
                return None
        
        refresh_recordings_btn.click(
            lambda: gr.update(choices=app.list_recordings(), value=None),
            outputs=recordings_list
        )
        
        load_recording_btn.click(
            load_selected_recording,
            inputs=recordings_list,
            outputs=audio_output
        )
    
    return demo


if __name__ == "__main__":
    print("Starting PyWAC Complete Feature Demo Application...")
    print("ブラウザで http://localhost:7860 を開いてください")
    
    demo = create_interface()
    demo.launch(share=False, inbrowser=True)
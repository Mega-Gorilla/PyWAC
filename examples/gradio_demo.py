"""
PyWAC 完全機能デモアプリケーション（リファクタリング版）
すべてのPyWAC機能を試せる統合デモ
"""

import gradio as gr
import pywac
import numpy as np
import wave
import time
import os
from datetime import datetime
from pathlib import Path
import threading
from typing import Optional, List, Dict, Any, Tuple

# Pre-import process_loopback_v2 to avoid threading issues
try:
    import process_loopback_v2
    test_capture = process_loopback_v2.ProcessCapture()
    del test_capture
except ImportError:
    pass


class RecordingManager:
    """録音機能を管理するクラス"""
    
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
    
    def start_system_recording(self, duration: int) -> Tuple[str, None]:
        """システム全体の音声を録音"""
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
        """特定プロセスの音声を録音"""
        if self.is_recording:
            return "すでに録音中です", None
        
        if not target_process or "見つかりません" in target_process:
            return "プロセスを選択してください", None
        
        self._reset_recording_state()
        self.recording_duration = duration
        
        # プロセス名とPIDを抽出
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
    
    def start_callback_recording(self, duration: int, monitor: bool) -> Tuple[str, None, str]:
        """コールバック録音（モニタリング付き）"""
        if self.is_recording:
            return "すでに録音中です", None, ""
        
        self._reset_recording_state()
        self.recording_duration = duration
        self.monitoring_active = monitor
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(self.recordings_dir / f"callback_{timestamp}.wav")
        
        self.recording_thread = threading.Thread(
            target=self._record_with_callback,
            args=(filename, duration),
            daemon=True
        )
        self.recording_thread.start()
        
        status = f"コールバック録音を開始しました（{duration}秒間）"
        if monitor:
            status += "\nモニタリング中..."
        
        return status, None, ""
    
    def _reset_recording_state(self):
        """録音状態をリセット"""
        self.is_recording = True
        self.audio_buffer = []  # 常にリストで初期化
        self.callback_messages = []
        self.recording_start_time = time.time()
        self.recording_status = "録音中"
    
    def _record_system_audio(self, filename: str, duration: int):
        """システム音声を録音（バックグラウンド）"""
        try:
            audio_data = pywac.record_audio(duration)
            # NumPy配列とリストの両方に対応
            has_data = False
            if isinstance(audio_data, np.ndarray):
                has_data = audio_data.size > 0
            elif isinstance(audio_data, list):
                has_data = len(audio_data) > 0
            
            if has_data:
                pywac.utils.save_to_wav(audio_data, filename, 48000)
                # WAVファイルから読み込んで正しいフォーマットを保証
                self._load_wav_to_buffer(filename)
                self.recording_status = f"録音成功: {Path(filename).name}"
                self.recording_filename = filename
            else:
                self.recording_status = "録音データが取得できませんでした"
        except Exception as e:
            self.recording_status = f"録音エラー: {str(e)}"
        finally:
            self.is_recording = False
    
    def _record_process_audio(self, process_name: str, pid: int, filename: str, duration: int):
        """プロセス音声を録音（バックグラウンド）"""
        try:
            success = (pywac.record_process_id(pid, filename, duration) if pid > 0 
                      else pywac.record_process(process_name, filename, duration))
            
            if success:
                self.recording_status = f"録音成功: {Path(filename).name}"
                self.recording_filename = filename
                self._load_wav_to_buffer(filename)
            else:
                self.recording_status = f"録音失敗: {process_name}"
        except Exception as e:
            self.recording_status = f"録音エラー: {str(e)}"
        finally:
            self.is_recording = False
    
    def _record_with_callback(self, filename: str, duration: int):
        """コールバック付き録音（バックグラウンド）"""
        try:
            pywac.record_with_callback(duration, self._audio_callback)
            time.sleep(duration + 0.5)  # コールバック完了まで待機
            
            # NumPy配列とリストの両方に対応した判定
            has_data = False
            if isinstance(self.audio_buffer, np.ndarray):
                has_data = self.audio_buffer.size > 0
            elif isinstance(self.audio_buffer, list):
                has_data = len(self.audio_buffer) > 0
            
            if has_data:
                pywac.utils.save_to_wav(self.audio_buffer, filename, 48000)
                self.recording_status = f"録音成功: {Path(filename).name}"
                self.recording_filename = filename
            else:
                self.recording_status = "録音失敗: データが取得できませんでした"
        except Exception as e:
            self.recording_status = f"録音エラー: {str(e)}"
        finally:
            self.is_recording = False
            self.monitoring_active = False
    
    def _audio_callback(self, audio_data):
        """録音完了時のコールバック処理"""
        # NumPy配列とリストの両方に対応
        if audio_data is not None:
            if isinstance(audio_data, np.ndarray):
                if audio_data.size > 0:
                    self._process_callback_data(audio_data)
            elif isinstance(audio_data, list):
                if len(audio_data) > 0:
                    self._process_callback_data(audio_data)
        else:
            self.callback_messages.append("録音データが取得できませんでした")
    
    def _process_callback_data(self, audio_data):
        """コールバックデータを処理"""
        self.audio_buffer = audio_data
        
        if self.monitoring_active:
            audio_array = np.array(audio_data) if not isinstance(audio_data, np.ndarray) else audio_data
            rms = np.sqrt(np.mean(audio_array ** 2))
            db = 20 * np.log10(rms + 1e-10)
            
            # サンプル数の取得
            sample_count = audio_array.size if isinstance(audio_array, np.ndarray) else len(audio_array)
            self.callback_messages.append(f"録音完了: {sample_count} サンプル, 平均音量: {db:.1f} dB")
            
            # 詳細な解析
            total_samples = audio_array.size if isinstance(audio_array, np.ndarray) else len(audio_array)
            chunk_size = total_samples // 10
            for i in range(10):
                start = i * chunk_size
                end = (i + 1) * chunk_size if i < 9 else total_samples
                chunk = audio_array[start:end] if audio_array.ndim == 1 else audio_array[start:end, :]
                chunk_rms = np.sqrt(np.mean(chunk ** 2))
                chunk_db = 20 * np.log10(chunk_rms + 1e-10)
                self.callback_messages.append(f"  セクション {i+1}/10: {chunk_db:.1f} dB")
    
    def _load_wav_to_buffer(self, filename: str):
        """WAVファイルをバッファに読み込み"""
        if os.path.exists(filename):
            with wave.open(filename, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                nchannels = wf.getnchannels()
                self.audio_buffer = np.frombuffer(frames, dtype=np.int16)
                if nchannels == 2:
                    self.audio_buffer = self.audio_buffer.reshape(-1, 2)
                self.sample_rate = wf.getframerate()
    
    def get_recording_result(self) -> Tuple[str, Optional[Tuple[int, np.ndarray]]]:
        """録音結果を取得"""
        if self.is_recording:
            return "録音中です", None
        
        # NumPy配列の場合とリストの場合で判定方法を変える
        if isinstance(self.audio_buffer, np.ndarray):
            if self.audio_buffer.size == 0:
                return self.recording_status, None
        elif isinstance(self.audio_buffer, list):
            if len(self.audio_buffer) == 0:
                return self.recording_status, None
        else:
            return self.recording_status, None
        
        # 音声データを適切な形式に変換
        if isinstance(self.audio_buffer, np.ndarray):
            # すでにint16の場合はそのまま使用
            if self.audio_buffer.dtype == np.int16:
                audio_output = self.audio_buffer
            elif self.audio_buffer.dtype == np.float32:
                audio_output = (self.audio_buffer * 32767).astype(np.int16)
            else:
                audio_output = self.audio_buffer.astype(np.int16)
        else:
            # リストの場合、float32と仮定
            audio_array = np.array(self.audio_buffer, dtype=np.float32)
            audio_output = (audio_array * 32767).astype(np.int16)
        
        # ステレオ形式に変換（必要な場合）
        if len(audio_output.shape) == 1:
            audio_output = np.column_stack((audio_output, audio_output))
        
        return self.recording_status, (self.sample_rate, audio_output)
    
    def get_recording_progress(self) -> str:
        """録音進捗状況をHTML形式で取得"""
        if not self.is_recording:
            return self._create_status_html("⏸️ 待機中", "rgba(30, 30, 46, 0.5)", "#e0e0e0")
        
        if self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            progress = min(100, (elapsed / self.recording_duration) * 100) if self.recording_duration > 0 else 0
            
            return f"""
            <div style='padding: 15px; background-color: rgba(76, 175, 80, 0.1); border-radius: 8px; border: 1px solid rgba(76, 175, 80, 0.3);'>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                    <span style='color: #4caf50; font-size: 20px; animation: pulse 1.5s infinite;'>🔴</span>
                    <span style='color: #4caf50; font-weight: bold;'>録音中...</span>
                    <span style='color: #e0e0e0;'>({elapsed:.1f}/{self.recording_duration}秒)</span>
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
        
        return self._create_status_html("🔴 録音準備中...", "rgba(76, 175, 80, 0.2)", "#4caf50")
    
    def get_monitoring_status(self) -> str:
        """モニタリング状況を取得"""
        if not self.monitoring_active and not self.callback_messages:
            return "モニタリング停止中"
        
        if self.monitoring_active and not self.callback_messages:
            return "録音中... (録音完了後に解析結果が表示されます)"
        
        if self.callback_messages:
            return "\n".join(self.callback_messages[-15:])
        
        return "待機中..."
    
    @staticmethod
    def _create_status_html(text: str, bg_color: str, text_color: str) -> str:
        """ステータスHTMLを生成"""
        return f"""<div style='padding: 10px; background-color: {bg_color}; 
                   border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); 
                   color: {text_color}; text-align: center;'>{text}</div>"""


class SessionController:
    """セッション管理機能を提供するクラス"""
    
    @staticmethod
    def get_sessions_table() -> str:
        """HTMLテーブル形式でセッション一覧を表示"""
        try:
            sessions = pywac.list_audio_sessions()
            if not sessions:
                return "<p style='color: gray; text-align: center;'>音声セッションが見つかりません</p>"
            
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
            return f"<p style='color: red;'>エラー: {str(e)}</p>"
    
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
        """セッション統計情報を表示"""
        try:
            sessions = pywac.list_audio_sessions()
            active_sessions = pywac.get_active_sessions()
            
            total = len(sessions)
            active = len(active_sessions)
            inactive = total - active
            muted = sum(1 for s in sessions if s.get('is_muted', False))
            
            return f"""
<div style='background-color: rgba(30, 30, 46, 0.5); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);'>
    <div style='color: #e0e0e0; font-size: 16px; font-weight: 600; margin-bottom: 15px;'>📊 セッション統計</div>
    
    <div style='display: grid; gap: 10px;'>
        <div style='display: flex; justify-content: space-between; padding: 8px; background-color: rgba(255, 255, 255, 0.05); border-radius: 4px;'>
            <span style='color: #b0b0b0;'>総セッション数:</span>
            <span style='color: #ffffff; font-weight: 600;'>{total}</span>
        </div>
        
        <div style='display: flex; justify-content: space-between; padding: 8px; background-color: rgba(76, 175, 80, 0.15); border-radius: 4px;'>
            <span style='color: #b0b0b0;'>🔊 アクティブ:</span>
            <span style='color: #4caf50; font-weight: 600;'>{active}</span>
        </div>
        
        <div style='display: flex; justify-content: space-between; padding: 8px; background-color: rgba(255, 255, 255, 0.05); border-radius: 4px;'>
            <span style='color: #b0b0b0;'>⏸️ 非アクティブ:</span>
            <span style='color: #ffffff; font-weight: 600;'>{inactive}</span>
        </div>
        
        <div style='display: flex; justify-content: space-between; padding: 8px; background-color: rgba(255, 152, 0, 0.15); border-radius: 4px;'>
            <span style='color: #b0b0b0;'>🔇 ミュート中:</span>
            <span style='color: #ff9800; font-weight: 600;'>{muted}</span>
        </div>
    </div>
    
    <div style='margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.1);'>
        <div style='color: #808080; font-size: 12px; text-align: center;'>
            最終更新: {datetime.now().strftime("%H:%M:%S")}
        </div>
    </div>
</div>
            """
        except Exception as e:
            return f"<div style='color: #ff5252;'>エラー: {str(e)}</div>"


class PyWACDemoApp:
    """PyWAC統合デモアプリケーション"""
    
    def __init__(self):
        # recordingsディレクトリを作成
        self.recordings_dir = Path(__file__).parent / "recordings"
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        
        # マネージャーの初期化
        self.recording_manager = RecordingManager(self.recordings_dir)
        self.session_controller = SessionController()
    
    def get_audio_sessions(self) -> List[str]:
        """利用可能な音声セッションのリストを取得"""
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
            return [f"エラー: {str(e)}"]
    
    def get_recordable_processes(self) -> List[str]:
        """録音可能なプロセス一覧を取得"""
        try:
            processes = pywac.list_recordable_processes()
            if not processes:
                return ["録音可能なプロセスが見つかりません"]
            
            return [f"{p.get('name', 'Unknown')} (PID: {p.get('pid', 0)})" for p in processes]
        except Exception as e:
            return [f"エラー: {str(e)}"]
    
    def list_recordings(self) -> List[str]:
        """録音ファイル一覧を取得（新しい順）"""
        try:
            recordings = []
            wav_files = list(self.recordings_dir.glob("*.wav"))
            
            # 更新日時でソート（新しい順）
            wav_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file in wav_files:
                size = file.stat().st_size / 1024
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                recordings.append(f"{file.name} ({size:.1f}KB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return recordings if recordings else ["録音ファイルがありません"]
        except Exception as e:
            return [f"エラー: {str(e)}"]
    
    def set_app_volume(self, target_app: str, volume: float) -> str:
        """アプリケーションの音量を設定"""
        if not target_app or "見つかりません" in target_app:
            return "アプリケーションを選択してください"
        
        try:
            app_name = target_app.split(" (PID:")[0]
            pywac.set_app_volume(app_name, volume / 100.0)
            return f"{app_name}の音量を{volume}%に設定しました"
        except Exception as e:
            return f"音量設定エラー: {str(e)}"


def create_interface():
    """Gradioインターフェースを作成"""
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
                        choices=["システム録音", "プロセス録音", "コールバック録音"],
                        value="システム録音",
                        label="録音モード"
                    )
                    
                    duration_slider = gr.Slider(
                        minimum=1,
                        maximum=60,
                        value=10,
                        step=1,
                        label="録音時間（秒）"
                    )
                    
                    with gr.Row():
                        preset_5s = gr.Button("5秒", size="sm")
                        preset_10s = gr.Button("10秒", size="sm")
                        preset_30s = gr.Button("30秒", size="sm")
                    
                    process_dropdown = gr.Dropdown(
                        label="対象プロセス",
                        choices=app.get_recordable_processes(),
                        visible=False
                    )
                    
                    enable_monitoring = gr.Checkbox(
                        label="📊 リアルタイムモニタリング",
                        value=False,
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
                    gr.Markdown("#### 🎵 録音結果")
                    
                    audio_output = gr.Audio(
                        label="録音済みファイル",
                        type="numpy"
                    )
                    
                    monitoring_output = gr.Textbox(
                        label="📊 モニタリング情報",
                        lines=8,
                        interactive=False,
                        visible=False
                    )
                    
                    with gr.Group():
                        gr.Markdown("#### 📁 録音履歴")
                        recordings_list = gr.Dropdown(
                            label="過去の録音ファイル",
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
                        label="対象アプリケーション",
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
            callback_visible = (mode == "コールバック録音")
            return (
                gr.update(visible=process_visible),
                gr.update(visible=callback_visible),
                gr.update(visible=callback_visible)
            )
        
        def start_recording(mode, duration, process, monitoring):
            """録音を開始"""
            if mode == "システム録音":
                status, _ = app.recording_manager.start_system_recording(duration)
            elif mode == "プロセス録音":
                if not process:
                    return "プロセスを選択してください", None, "", gr.Timer(active=False), gr.update()
                status, _ = app.recording_manager.start_process_recording(process, duration)
            elif mode == "コールバック録音":
                status, _, _ = app.recording_manager.start_callback_recording(duration, monitoring)
            else:
                return "不明なモード", None, "", gr.Timer(active=False), gr.update()
            
            status_html = app.recording_manager._create_status_html(f"🔴 {status}", "rgba(76, 175, 80, 0.2)", "#4caf50")
            return status_html, None, "", gr.Timer(active=True), gr.update(choices=app.list_recordings())
        
        def update_recording_status():
            """録音ステータスを更新"""
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
                
                return status_html, audio, monitoring_info, gr.Timer(active=False), recordings_update
            else:
                return (
                    app.recording_manager.get_recording_progress(),
                    None,
                    app.recording_manager.get_monitoring_status() if app.recording_manager.monitoring_active else "",
                    gr.Timer(active=True),
                    gr.update()  # 録音中はリストを更新しない
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
            outputs=[process_dropdown, enable_monitoring, monitoring_output]
        )
        
        preset_5s.click(lambda: 5, outputs=duration_slider)
        preset_10s.click(lambda: 10, outputs=duration_slider)
        preset_30s.click(lambda: 30, outputs=duration_slider)
        
        record_btn.click(
            start_recording,
            inputs=[recording_mode, duration_slider, process_dropdown, enable_monitoring],
            outputs=[record_status, audio_output, monitoring_output, recording_timer, recordings_list]
        )
        
        recording_timer.tick(
            update_recording_status,
            outputs=[record_status, audio_output, monitoring_output, recording_timer, recordings_list]
        )
        
        set_volume_btn.click(
            app.set_app_volume,
            inputs=[volume_app_dropdown, volume_slider],
            outputs=volume_status
        )
        
        def load_selected_recording(filename):
            """選択した録音ファイルを読み込み"""
            if not filename or "録音ファイルがありません" in filename:
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
                print(f"録音ファイル読み込みエラー: {e}")
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
    print("PyWAC 完全機能デモアプリケーションを起動中...")
    print("ブラウザで http://localhost:7860 を開いてください")
    
    demo = create_interface()
    demo.launch(share=False, inbrowser=True)
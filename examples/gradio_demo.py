"""
PyPAC 完全機能デモアプリケーション（日本語版）
すべてのPyPAC機能を試せる統合デモ
"""

import gradio as gr
import pypac
import numpy as np
import wave
import io
import time
import os
import json
import psutil
from datetime import datetime
from pathlib import Path
import threading
from typing import Optional, List, Dict, Any

class PyPACDemoApp:
    """PyPACのすべての機能を統合したデモアプリケーション"""
    
    def __init__(self):
        self.is_recording = False
        self.recording_thread = None
        self.audio_buffer = []
        self.sample_rate = 48000
        self.recording_filename = None
        self.recording_status = "待機中"
        self.callback_messages = []
        self.monitoring_active = False
        
        # recordingsディレクトリを作成
        self.recordings_dir = Path(__file__).parent / "recordings"
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
    
    # ===== セッション管理機能 =====
    
    def get_audio_sessions(self) -> List[str]:
        """利用可能な音声セッションのリストを取得"""
        try:
            sessions = pypac.list_audio_sessions()
            if not sessions:
                return ["音声セッションが見つかりません"]
            
            session_list = []
            for session in sessions:
                status = "再生中" if session.get('is_active', False) else "停止中"
                volume = session.get('volume', session.get('volume_percent', 0))
                if volume <= 1:
                    volume = volume * 100
                process_name = session.get('process_name', session.get('name', 'Unknown'))
                pid = session.get('process_id', session.get('pid', 0))
                session_str = f"{process_name} (PID: {pid}) - {status} - 音量: {volume:.0f}%"
                session_list.append(session_str)
            return session_list
        except Exception as e:
            return [f"エラー: {str(e)}"]
    
    def get_session_details(self, session_name: str) -> str:
        """セッションの詳細情報を取得"""
        if not session_name or session_name == "音声セッションが見つかりません":
            return "セッションを選択してください"
        
        try:
            app_name = session_name.split(" (PID:")[0]
            session = pypac.find_audio_session(app_name)
            
            if session:
                details = f"""
### セッション詳細情報

**プロセス名**: {session.get('process_name', 'Unknown')}
**プロセスID**: {session.get('process_id', 'N/A')}
**音量**: {session.get('volume_percent', 0):.1f}%
**ミュート状態**: {'ミュート中' if session.get('is_muted', False) else 'ミュート解除'}
**アクティブ**: {'はい' if session.get('is_active', False) else 'いいえ'}
**デバイス**: {session.get('device_name', 'デフォルト')}
                """
                return details
            else:
                return f"セッション情報を取得できませんでした: {app_name}"
        except Exception as e:
            return f"エラー: {str(e)}"
    
    def get_active_sessions(self) -> str:
        """アクティブなセッション一覧を取得"""
        try:
            active_sessions = pypac.get_active_sessions()
            if not active_sessions:
                return "アクティブなセッションがありません"
            
            result = "### アクティブなセッション\n\n"
            for session in active_sessions:
                result += f"- **{session['process_name']}** (PID: {session['process_id']})\n"
            return result
        except Exception as e:
            return f"エラー: {str(e)}"
    
    def get_recordable_processes(self) -> List[str]:
        """録音可能なプロセス一覧を取得"""
        try:
            processes = pypac.list_recordable_processes()
            if not processes:
                return ["録音可能なプロセスが見つかりません"]
            
            process_list = []
            for proc in processes:
                name = proc.get('name', 'Unknown')
                pid = proc.get('pid', 0)
                process_list.append(f"{name} (PID: {pid})")
            return process_list
        except Exception as e:
            return [f"エラー: {str(e)}"]
    
    # ===== 録音機能 =====
    
    def start_system_recording(self, duration: int):
        """システム全体の音声を録音"""
        if self.is_recording:
            return "すでに録音中です", None
        
        try:
            self.is_recording = True
            self.audio_buffer = []
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = str(self.recordings_dir / f"system_{timestamp}.wav")
            
            self.recording_thread = threading.Thread(
                target=self._record_system_audio,
                args=(filename, duration)
            )
            self.recording_thread.start()
            
            return f"システム音声の録音を開始しました（{duration}秒間）", None
        except Exception as e:
            self.is_recording = False
            return f"録音開始エラー: {str(e)}", None
    
    def _record_system_audio(self, filename: str, duration: int):
        """システム音声を録音（バックグラウンド）"""
        try:
            audio_data = pypac.record_audio(duration)
            if audio_data is not None and len(audio_data) > 0:
                # Fix argument order: audio_data first, then filename
                pypac.save_to_wav(audio_data, filename, 48000)
                # Convert to numpy array and then to int16
                audio_array = np.array(audio_data, dtype=np.float32)
                self.audio_buffer = (audio_array * 32767).astype(np.int16)
                self.recording_status = f"システム音声録音成功: {filename}"
                self.recording_filename = filename
            else:
                self.recording_status = "録音データが取得できませんでした"
        except Exception as e:
            self.recording_status = f"録音エラー: {str(e)}"
        finally:
            self.is_recording = False
    
    def start_process_recording(self, target_process: str, duration: int):
        """特定プロセスの音声を録音"""
        if self.is_recording:
            return "すでに録音中です", None
        
        if not target_process or target_process == "録音可能なプロセスが見つかりません":
            return "プロセスを選択してください", None
        
        try:
            # プロセス名とPIDを抽出
            parts = target_process.split(" (PID: ")
            process_name = parts[0]
            pid = int(parts[1].rstrip(")")) if len(parts) > 1 else 0
            
            self.is_recording = True
            self.audio_buffer = []
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = str(self.recordings_dir / f"process_{process_name.replace('.exe', '')}_{timestamp}.wav")
            
            self.recording_thread = threading.Thread(
                target=self._record_process_audio,
                args=(process_name, pid, filename, duration)
            )
            self.recording_thread.start()
            
            return f"{process_name}の録音を開始しました（{duration}秒間）", None
        except Exception as e:
            self.is_recording = False
            return f"録音開始エラー: {str(e)}", None
    
    def _record_process_audio(self, process_name: str, pid: int, filename: str, duration: int):
        """プロセス音声を録音（バックグラウンド）"""
        try:
            # PIDで録音を試みる
            if pid > 0:
                success = pypac.record_process_id(pid, filename, duration)
            else:
                success = pypac.record_process(process_name, filename, duration)
            
            if success:
                self.recording_status = f"プロセス録音成功: {process_name}"
                self.recording_filename = filename
                
                # WAVファイルを読み込み
                if os.path.exists(filename):
                    with wave.open(filename, 'rb') as wf:
                        frames = wf.readframes(wf.getnframes())
                        nchannels = wf.getnchannels()
                        self.audio_buffer = np.frombuffer(frames, dtype=np.int16)
                        if nchannels == 2:
                            self.audio_buffer = self.audio_buffer.reshape(-1, 2)
                        self.sample_rate = wf.getframerate()
            else:
                self.recording_status = f"プロセス録音失敗: {process_name}"
        except Exception as e:
            self.recording_status = f"録音エラー: {str(e)}"
        finally:
            self.is_recording = False
    
    def start_callback_recording(self, duration: int, monitor: bool):
        """コールバック録音（モニタリング付き）"""
        if self.is_recording:
            return "すでに録音中です", None, ""
        
        try:
            self.is_recording = True
            self.audio_buffer = []
            self.callback_messages = []
            self.monitoring_active = monitor
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = str(self.recordings_dir / f"callback_{timestamp}.wav")
            
            self.recording_thread = threading.Thread(
                target=self._record_with_callback,
                args=(filename, duration)
            )
            self.recording_thread.start()
            
            status = f"コールバック録音を開始しました（{duration}秒間）"
            if monitor:
                status += "\nモニタリング中..."
            
            return status, None, ""
        except Exception as e:
            self.is_recording = False
            return f"録音開始エラー: {str(e)}", None, ""
    
    def _audio_callback(self, audio_chunk: np.ndarray, chunk_index: int):
        """音声チャンクのコールバック処理"""
        if self.monitoring_active:
            # 音声レベル計算
            rms = np.sqrt(np.mean(audio_chunk ** 2))
            db = 20 * np.log10(rms + 1e-10)
            
            # メッセージ追加
            msg = f"チャンク {chunk_index}: {len(audio_chunk)} サンプル, {db:.1f} dB"
            self.callback_messages.append(msg)
            
            # 最新10件のみ保持
            if len(self.callback_messages) > 10:
                self.callback_messages = self.callback_messages[-10:]
        
        # バッファに追加
        self.audio_buffer.extend(audio_chunk.tolist())
    
    def _record_with_callback(self, filename: str, duration: int):
        """コールバック付き録音（バックグラウンド）"""
        try:
            # コールバック録音実行
            success = pypac.record_with_callback(
                duration=duration,
                callback=self._audio_callback,
                filename=filename
            )
            
            if success:
                self.recording_status = f"コールバック録音成功: {filename}"
                self.recording_filename = filename
                
                # NumPy配列に変換
                if len(self.audio_buffer) > 0:
                    self.audio_buffer = np.array(self.audio_buffer, dtype=np.float32)
            else:
                self.recording_status = "コールバック録音失敗"
        except Exception as e:
            self.recording_status = f"録音エラー: {str(e)}"
        finally:
            self.is_recording = False
            self.monitoring_active = False
    
    def stop_recording(self):
        """録音を停止"""
        if not self.is_recording and self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2)
        
        if not self.is_recording and len(self.audio_buffer) == 0:
            return "録音データがありません", None
        
        # 録音を強制停止
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1)
        
        if len(self.audio_buffer) == 0:
            return f"録音データがありません (状態: {self.recording_status})", None
        
        # audio_bufferがfloat32の場合はint16に変換
        if self.audio_buffer.dtype == np.float32:
            audio_output = (self.audio_buffer * 32767).astype(np.int16)
        else:
            audio_output = self.audio_buffer
        
        # 2次元配列に変換（ステレオ）
        if len(audio_output.shape) == 1:
            # モノラルをステレオに変換
            audio_output = np.column_stack((audio_output, audio_output))
        
        return f"録音を停止しました\n{self.recording_status}", (self.sample_rate, audio_output)
    
    def get_monitoring_status(self) -> str:
        """モニタリング状況を取得"""
        if not self.monitoring_active:
            return "モニタリング停止中"
        
        if len(self.callback_messages) == 0:
            return "モニタリング中..."
        
        return "\n".join(self.callback_messages)
    
    # ===== 音量制御機能 =====
    
    def set_app_volume(self, target_app: str, volume: float):
        """アプリケーションの音量を設定"""
        if not target_app or target_app == "音声セッションが見つかりません":
            return "アプリケーションを選択してください"
        
        try:
            app_name = target_app.split(" (PID:")[0]
            pypac.set_app_volume(app_name, volume / 100.0)
            return f"{app_name}の音量を{volume}%に設定しました"
        except Exception as e:
            return f"音量設定エラー: {str(e)}"
    
    def get_app_volume(self, target_app: str) -> str:
        """アプリケーションの現在の音量を取得"""
        if not target_app or target_app == "音声セッションが見つかりません":
            return "アプリケーションを選択してください"
        
        try:
            app_name = target_app.split(" (PID:")[0]
            volume = pypac.get_app_volume(app_name)
            return f"{app_name}の現在の音量: {volume * 100:.1f}%"
        except Exception as e:
            return f"音量取得エラー: {str(e)}"
    
    def adjust_app_volume(self, target_app: str, delta: float):
        """アプリケーションの音量を相対的に調整"""
        if not target_app or target_app == "音声セッションが見つかりません":
            return "アプリケーションを選択してください"
        
        try:
            app_name = target_app.split(" (PID:")[0]
            new_volume = pypac.adjust_volume(app_name, delta / 100.0)
            return f"{app_name}の音量を調整しました: {new_volume * 100:.1f}%"
        except Exception as e:
            return f"音量調整エラー: {str(e)}"
    
    def mute_app(self, target_app: str):
        """アプリケーションをミュート"""
        if not target_app or target_app == "音声セッションが見つかりません":
            return "アプリケーションを選択してください"
        
        try:
            app_name = target_app.split(" (PID:")[0]
            pypac.mute_app(app_name)
            return f"{app_name}をミュートしました"
        except Exception as e:
            return f"ミュートエラー: {str(e)}"
    
    def unmute_app(self, target_app: str):
        """アプリケーションのミュートを解除"""
        if not target_app or target_app == "音声セッションが見つかりません":
            return "アプリケーションを選択してください"
        
        try:
            app_name = target_app.split(" (PID:")[0]
            pypac.unmute_app(app_name)
            return f"{app_name}のミュートを解除しました"
        except Exception as e:
            return f"ミュート解除エラー: {str(e)}"
    
    def list_recordings(self) -> List[str]:
        """録音ファイル一覧を取得"""
        try:
            recordings = []
            for file in self.recordings_dir.glob("*.wav"):
                size = file.stat().st_size / 1024
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                recordings.append(f"{file.name} ({size:.1f}KB) - {mtime.strftime('%Y-%m-%d %H:%M')}")
            
            if not recordings:
                return ["録音ファイルがありません"]
            
            return sorted(recordings, reverse=True)
        except Exception as e:
            return [f"エラー: {str(e)}"]

# アプリケーションインスタンス
app = PyPACDemoApp()

# Gradioインターフェースの作成
with gr.Blocks(title="PyPAC完全機能デモ", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎙️ PyPAC 完全機能デモ（日本語版）
    
    Python Process Audio Capture - すべての機能を試せる統合デモ
    """)
    
    # ===== セッション管理タブ =====
    with gr.Tab("セッション管理"):
        with gr.Row():
            with gr.Column(scale=1):
                session_dropdown = gr.Dropdown(
                    label="音声セッション",
                    choices=app.get_audio_sessions(),
                    value=None,
                    interactive=True
                )
                
                refresh_sessions_btn = gr.Button("🔄 セッション更新", size="sm")
                
                get_details_btn = gr.Button("詳細情報を取得")
                get_active_btn = gr.Button("アクティブセッション一覧")
                
            with gr.Column(scale=2):
                session_info = gr.Markdown("セッションを選択してください")
    
    # ===== 録音タブ =====
    with gr.Tab("録音"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 録音モード選択")
                
                with gr.Tab("システム録音"):
                    system_duration = gr.Slider(1, 60, 10, step=1, label="録音時間（秒）")
                    system_record_btn = gr.Button("🔴 システム録音開始", variant="primary")
                
                with gr.Tab("プロセス録音"):
                    process_dropdown = gr.Dropdown(
                        label="対象プロセス",
                        choices=app.get_recordable_processes(),
                        value=None,
                        interactive=True
                    )
                    refresh_processes_btn = gr.Button("🔄 プロセス更新", size="sm")
                    process_duration = gr.Slider(1, 60, 10, step=1, label="録音時間（秒）")
                    process_record_btn = gr.Button("🔴 プロセス録音開始", variant="primary")
                
                with gr.Tab("コールバック録音"):
                    callback_duration = gr.Slider(1, 60, 10, step=1, label="録音時間（秒）")
                    enable_monitoring = gr.Checkbox(label="リアルタイムモニタリング", value=True)
                    callback_record_btn = gr.Button("🔴 コールバック録音開始", variant="primary")
                    monitoring_output = gr.Textbox(
                        label="モニタリング状況",
                        lines=5,
                        interactive=False
                    )
                
                stop_btn = gr.Button("⏹️ 録音停止", variant="stop")
                
                record_status = gr.Textbox(
                    label="録音ステータス",
                    value="待機中",
                    interactive=False
                )
            
            with gr.Column():
                audio_output = gr.Audio(
                    label="録音結果",
                    type="numpy"
                )
                
                recordings_list = gr.Dropdown(
                    label="録音済みファイル",
                    choices=app.list_recordings(),
                    interactive=True
                )
                refresh_recordings_btn = gr.Button("🔄 録音リスト更新", size="sm")
    
    # ===== 音量制御タブ =====
    with gr.Tab("音量制御"):
        with gr.Row():
            with gr.Column():
                volume_app_dropdown = gr.Dropdown(
                    label="対象アプリケーション",
                    choices=app.get_audio_sessions(),
                    value=None,
                    interactive=True
                )
                
                refresh_volume_btn = gr.Button("🔄 更新", size="sm")
                
                gr.Markdown("### 絶対音量設定")
                volume_slider = gr.Slider(0, 100, 50, step=1, label="音量（%）")
                set_volume_btn = gr.Button("音量を設定", variant="primary")
                
                gr.Markdown("### 相対音量調整")
                delta_slider = gr.Slider(-50, 50, 0, step=5, label="調整量（%）")
                adjust_volume_btn = gr.Button("音量を調整")
                
                gr.Markdown("### ミュート制御")
                with gr.Row():
                    mute_btn = gr.Button("🔇 ミュート")
                    unmute_btn = gr.Button("🔊 ミュート解除")
                
                get_volume_btn = gr.Button("現在の音量を取得")
                
            with gr.Column():
                volume_status = gr.Textbox(
                    label="ステータス",
                    lines=3,
                    interactive=False
                )
    
    # ===== Process Loopbackタブ =====
    with gr.Tab("Process Loopback"):
        gr.Markdown("""
        ### Windows Process Loopback API テスト
        
        プロセス固有の音声キャプチャ機能をテストします。
        Windows 10 バージョン2004以降が必要です。
        """)
        
        with gr.Row():
            with gr.Column():
                loopback_process = gr.Dropdown(
                    label="対象プロセス",
                    choices=app.get_recordable_processes(),
                    interactive=True
                )
                refresh_loopback_btn = gr.Button("🔄 プロセス更新", size="sm")
                
                loopback_duration = gr.Slider(1, 30, 5, step=1, label="録音時間（秒）")
                
                with gr.Row():
                    test_process_btn = gr.Button("プロセス録音テスト", variant="primary")
                    test_pid_btn = gr.Button("PID録音テスト")
                
                loopback_status = gr.Textbox(
                    label="テスト結果",
                    lines=5,
                    interactive=False
                )
            
            with gr.Column():
                loopback_audio = gr.Audio(
                    label="録音結果",
                    type="numpy"
                )
    
    # ===== ヘルプタブ =====
    with gr.Tab("ヘルプ"):
        gr.Markdown("""
        ## 📖 PyPAC 完全機能ガイド
        
        ### 🎯 主要機能
        
        #### 1. セッション管理
        - **list_audio_sessions()**: すべての音声セッションを列挙
        - **find_audio_session()**: 特定のセッションを検索
        - **get_active_sessions()**: アクティブなセッションのみ取得
        - **list_recordable_processes()**: 録音可能なプロセス一覧
        
        #### 2. 録音機能
        - **record_audio()**: システム全体の音声を録音
        - **record_process()**: プロセス名で特定アプリの音声を録音
        - **record_process_id()**: PIDで特定アプリの音声を録音
        - **record_with_callback()**: リアルタイムコールバック付き録音
        - **record_to_file()**: ファイルに直接録音
        
        #### 3. 音量制御
        - **set_app_volume()**: アプリの音量を設定（0.0-1.0）
        - **get_app_volume()**: 現在の音量を取得
        - **adjust_volume()**: 相対的に音量調整
        - **mute_app()**: アプリをミュート
        - **unmute_app()**: ミュート解除
        
        #### 4. ユーティリティ
        - **save_to_wav()**: NumPy配列をWAVファイルに保存
        - **convert_float32_to_int16()**: 音声フォーマット変換
        - **utils.calculate_db()**: 音量レベル計算
        
        ### 🔧 技術仕様
        
        - **対応OS**: Windows 10 バージョン2004以降
        - **音声フォーマット**: 48kHz / 32bit float / ステレオ
        - **Process Loopback**: Windows Process Loopback API使用
        - **最大録音時間**: 60秒（バッファサイズ制限）
        
        ### ⚠️ 注意事項
        
        - Process Loopback APIは管理者権限が必要な場合があります
        - 対象プロセスが音声を出力していない場合は無音になります
        - 一部のDRM保護されたコンテンツは録音できません
        
        ### 🐛 トラブルシューティング
        
        **Q: プロセス録音が無音になる**
        - A: 対象プロセスが音声を出力しているか確認
        - A: Windows 10 バージョン2004以降か確認
        - A: 管理者権限で実行してみる
        
        **Q: セッションが見つからない**
        - A: Windows音声ミキサーでアプリが表示されているか確認
        - A: アプリケーションを再起動してみる
        
        **Q: 録音が途中で切れる**
        - A: 録音時間を短くしてみる（推奨: 30秒以内）
        - A: システムメモリが十分か確認
        """)
    
    # ===== イベントハンドラー =====
    
    # セッション管理
    def refresh_sessions():
        sessions = app.get_audio_sessions()
        processes = app.get_recordable_processes()
        recordings = app.list_recordings()
        return {
            session_dropdown: gr.update(choices=sessions),
            volume_app_dropdown: gr.update(choices=sessions),
            process_dropdown: gr.update(choices=processes),
            loopback_process: gr.update(choices=processes),
            recordings_list: gr.update(choices=recordings)
        }
    
    # 録音機能
    def on_system_record(duration):
        status, audio = app.start_system_recording(duration)
        return status, audio
    
    def on_process_record(process, duration):
        status, audio = app.start_process_recording(process, duration)
        return status, audio
    
    def on_callback_record(duration, monitor):
        status, audio, monitoring = app.start_callback_recording(duration, monitor)
        return status, audio, monitoring
    
    def on_stop_recording():
        status, audio = app.stop_recording()
        return status, audio
    
    def update_monitoring():
        """モニタリング状況を定期更新"""
        if app.monitoring_active:
            return app.get_monitoring_status()
        return gr.update()
    
    # Process Loopbackテスト
    def test_process_loopback(process, duration):
        if not process:
            return "プロセスを選択してください", None
        
        try:
            process_name = process.split(" (PID:")[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = str(app.recordings_dir / f"loopback_test_{timestamp}.wav")
            
            success = pypac.record_process(process_name, filename, duration)
            
            if success and os.path.exists(filename):
                with wave.open(filename, 'rb') as wf:
                    frames = wf.readframes(wf.getnframes())
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                    sample_rate = wf.getframerate()
                    
                    if wf.getnchannels() == 2:
                        audio_data = audio_data.reshape(-1, 2)
                    else:
                        audio_data = np.column_stack((audio_data, audio_data))
                
                return f"Process Loopback成功: {process_name}", (sample_rate, audio_data)
            else:
                return f"Process Loopback失敗: {process_name}", None
        except Exception as e:
            return f"エラー: {str(e)}", None
    
    def test_pid_loopback(process, duration):
        if not process:
            return "プロセスを選択してください", None
        
        try:
            parts = process.split(" (PID: ")
            if len(parts) < 2:
                return "PIDが取得できません", None
            
            pid = int(parts[1].rstrip(")"))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = str(app.recordings_dir / f"pid_test_{timestamp}.wav")
            
            success = pypac.record_process_id(pid, filename, duration)
            
            if success and os.path.exists(filename):
                with wave.open(filename, 'rb') as wf:
                    frames = wf.readframes(wf.getnframes())
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                    sample_rate = wf.getframerate()
                    
                    if wf.getnchannels() == 2:
                        audio_data = audio_data.reshape(-1, 2)
                    else:
                        audio_data = np.column_stack((audio_data, audio_data))
                
                return f"PID録音成功: PID {pid}", (sample_rate, audio_data)
            else:
                return f"PID録音失敗: PID {pid}", None
        except Exception as e:
            return f"エラー: {str(e)}", None
    
    # イベントバインディング
    
    # 更新ボタン
    refresh_sessions_btn.click(refresh_sessions, outputs=[
        session_dropdown, volume_app_dropdown, process_dropdown,
        loopback_process, recordings_list
    ])
    refresh_processes_btn.click(refresh_sessions, outputs=[
        session_dropdown, volume_app_dropdown, process_dropdown,
        loopback_process, recordings_list
    ])
    refresh_volume_btn.click(refresh_sessions, outputs=[
        session_dropdown, volume_app_dropdown, process_dropdown,
        loopback_process, recordings_list
    ])
    refresh_loopback_btn.click(refresh_sessions, outputs=[
        session_dropdown, volume_app_dropdown, process_dropdown,
        loopback_process, recordings_list
    ])
    refresh_recordings_btn.click(refresh_sessions, outputs=[
        session_dropdown, volume_app_dropdown, process_dropdown,
        loopback_process, recordings_list
    ])
    
    # セッション管理
    get_details_btn.click(
        lambda x: app.get_session_details(x),
        inputs=session_dropdown,
        outputs=session_info
    )
    get_active_btn.click(
        app.get_active_sessions,
        outputs=session_info
    )
    
    # 録音
    system_record_btn.click(
        on_system_record,
        inputs=system_duration,
        outputs=[record_status, audio_output]
    )
    process_record_btn.click(
        on_process_record,
        inputs=[process_dropdown, process_duration],
        outputs=[record_status, audio_output]
    )
    callback_record_btn.click(
        on_callback_record,
        inputs=[callback_duration, enable_monitoring],
        outputs=[record_status, audio_output, monitoring_output]
    )
    stop_btn.click(
        on_stop_recording,
        outputs=[record_status, audio_output]
    )
    
    # モニタリング更新（1秒ごと）
    demo.load(
        update_monitoring,
        outputs=monitoring_output,
        every=1
    )
    
    # 音量制御
    set_volume_btn.click(
        app.set_app_volume,
        inputs=[volume_app_dropdown, volume_slider],
        outputs=volume_status
    )
    get_volume_btn.click(
        app.get_app_volume,
        inputs=volume_app_dropdown,
        outputs=volume_status
    )
    adjust_volume_btn.click(
        app.adjust_app_volume,
        inputs=[volume_app_dropdown, delta_slider],
        outputs=volume_status
    )
    mute_btn.click(
        app.mute_app,
        inputs=volume_app_dropdown,
        outputs=volume_status
    )
    unmute_btn.click(
        app.unmute_app,
        inputs=volume_app_dropdown,
        outputs=volume_status
    )
    
    # Process Loopback
    test_process_btn.click(
        test_process_loopback,
        inputs=[loopback_process, loopback_duration],
        outputs=[loopback_status, loopback_audio]
    )
    test_pid_btn.click(
        test_pid_loopback,
        inputs=[loopback_process, loopback_duration],
        outputs=[loopback_status, loopback_audio]
    )
    
    # 初期化時にリストを更新
    demo.load(refresh_sessions, outputs=[
        session_dropdown, volume_app_dropdown, process_dropdown,
        loopback_process, recordings_list
    ])

if __name__ == "__main__":
    print("PyPAC 完全機能デモアプリケーションを起動中...")
    print("ブラウザで http://localhost:7860 を開いてください")
    demo.launch(share=False, inbrowser=True)
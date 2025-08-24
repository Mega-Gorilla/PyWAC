"""
Gradio音声録音デモアプリ（日本語版）
PyPACを使用したリアルタイム音声録音インターフェース
"""

import gradio as gr
import pypac
import numpy as np
import wave
import io
import time
import os
from datetime import datetime
from pathlib import Path
import threading

class AudioRecorderApp:
    def __init__(self):
        self.is_recording = False
        self.recording_thread = None
        self.audio_buffer = []
        self.sample_rate = 48000
        self.recording_filename = None
        self.recording_status = "待機中"
        
    def get_audio_sessions(self):
        """利用可能な音声セッションのリストを取得"""
        try:
            sessions = pypac.list_audio_sessions()
            if not sessions:
                return ["音声セッションが見つかりません"]
            
            session_list = []
            for session in sessions:
                status = "再生中" if session.get('is_active', False) else "停止中"
                volume = session.get('volume', session.get('volume_percent', 0))
                if volume <= 1:  # 0-1の範囲の場合
                    volume = volume * 100
                process_name = session.get('process_name', session.get('name', 'Unknown'))
                pid = session.get('process_id', session.get('pid', 0))
                session_str = f"{process_name} (PID: {pid}) - {status} - 音量: {volume:.0f}%"
                session_list.append(session_str)
            return session_list
        except Exception as e:
            return [f"エラー: {str(e)}"]
    
    def start_recording(self, target_app, duration):
        """録音を開始"""
        if self.is_recording:
            return "すでに録音中です", None
        
        if not target_app or target_app == "音声セッションが見つかりません":
            return "アプリケーションを選択してください", None
        
        try:
            # アプリケーション名を抽出（形式: "app.exe (PID: 1234) - ..."）
            app_name = target_app.split(" (PID:")[0]
            
            self.is_recording = True
            self.audio_buffer = []
            
            # 録音スレッドを開始
            self.recording_thread = threading.Thread(
                target=self._record_audio,
                args=(app_name, duration)
            )
            self.recording_thread.start()
            
            return f"{app_name}の録音を開始しました（{duration}秒間）", None
        except Exception as e:
            self.is_recording = False
            return f"録音開始エラー: {str(e)}", None
    
    def _record_audio(self, app_name, duration):
        """バックグラウンドで音声を録音"""
        try:
            # recordingsディレクトリを作成
            recordings_dir = Path(__file__).parent / "recordings"
            recordings_dir.mkdir(parents=True, exist_ok=True)
            
            # タイムスタンプを生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = str(recordings_dir / f"gradio_{app_name.replace('.exe', '')}_{timestamp}.wav")
            
            # PyPACで録音
            self.recording_filename = filename
            success = pypac.record_process(app_name, filename, duration)
            
            if success:
                self.recording_status = f"プロセス録音成功: {app_name}"
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
                    self.recording_status = f"録音ファイルが見つかりません: {filename}"
            else:
                # システム音声で代替録音
                self.recording_status = "プロセス録音失敗、システム音声を録音中..."
                audio_data = pypac.record_audio(duration)
                if audio_data is not None and len(audio_data) > 0:
                    self.audio_buffer = (audio_data * 32767).astype(np.int16)
                    self.recording_status = "システム音声録音成功"
                
        except Exception as e:
            print(f"録音エラー: {str(e)}")
        finally:
            self.is_recording = False
    
    def stop_recording(self):
        """録音を停止"""
        if not self.is_recording and self.recording_thread and self.recording_thread.is_alive():
            # まだ録音スレッドが動いている場合は待つ
            self.recording_thread.join(timeout=2)
        
        if not self.is_recording and len(self.audio_buffer) == 0:
            return "録音データがありません", None
        
        # 録音を強制停止
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1)
        
        if len(self.audio_buffer) == 0:
            return f"録音データがありません (状態: {self.recording_status})", None
        
        # WAVデータを作成
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(2)  # ステレオ
            wav_file.setsampwidth(2)  # 16bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(self.audio_buffer.tobytes())
        
        wav_io.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # audio_bufferがすでに2次元配列の場合はそのまま、1次元の場合はreshape
        if len(self.audio_buffer.shape) == 1:
            audio_output = self.audio_buffer.reshape(-1, 2)
        else:
            audio_output = self.audio_buffer
        
        return "録音を停止しました", (self.sample_rate, audio_output)
    
    def set_app_volume(self, target_app, volume):
        """アプリケーションの音量を設定"""
        if not target_app or target_app == "音声セッションが見つかりません":
            return "アプリケーションを選択してください"
        
        try:
            app_name = target_app.split(" (PID:")[0]
            pypac.set_app_volume(app_name, volume / 100.0)
            return f"{app_name}の音量を{volume}%に設定しました"
        except Exception as e:
            return f"音量設定エラー: {str(e)}"

# アプリケーションインスタンス
app = AudioRecorderApp()

# Gradioインターフェースの作成
with gr.Blocks(title="PyPAC音声録音デモ", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎙️ PyPAC音声録音デモ（日本語版）
    
    Windows Process Audio Captureを使用したアプリケーション別音声録音
    """)
    
    with gr.Tab("録音"):
        with gr.Row():
            with gr.Column(scale=1):
                # セッションリスト
                session_dropdown = gr.Dropdown(
                    label="録音対象アプリケーション",
                    choices=app.get_audio_sessions(),
                    value=None,
                    interactive=True
                )
                
                refresh_btn = gr.Button("🔄 更新", size="sm")
                
                # 録音時間
                duration_slider = gr.Slider(
                    minimum=1,
                    maximum=30,
                    value=5,
                    step=1,
                    label="録音時間（秒）"
                )
                
                # 録音ボタン
                with gr.Row():
                    record_btn = gr.Button("🔴 録音開始", variant="primary")
                    stop_btn = gr.Button("⏹️ 録音停止", variant="stop")
                
                # ステータス表示
                status_text = gr.Textbox(
                    label="ステータス",
                    value="待機中...",
                    interactive=False
                )
            
            with gr.Column(scale=2):
                # 音声プレーヤー
                audio_output = gr.Audio(
                    label="録音結果",
                    type="numpy"
                )
                
                # 音声情報
                audio_info = gr.Markdown("録音データなし")
    
    with gr.Tab("音量調整"):
        with gr.Row():
            with gr.Column():
                volume_app_dropdown = gr.Dropdown(
                    label="対象アプリケーション",
                    choices=app.get_audio_sessions(),
                    value=None,
                    interactive=True
                )
                
                volume_slider = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=50,
                    step=1,
                    label="音量（%）"
                )
                
                volume_btn = gr.Button("音量を設定", variant="primary")
                volume_status = gr.Textbox(
                    label="ステータス",
                    value="",
                    interactive=False
                )
    
    with gr.Tab("使い方"):
        gr.Markdown("""
        ## 📖 使い方
        
        ### 録音手順
        1. **アプリケーション選択**: ドロップダウンから録音したいアプリを選択
        2. **録音時間設定**: スライダーで録音時間を調整（1-30秒）
        3. **録音開始**: 「録音開始」ボタンをクリック
        4. **録音停止**: 自動停止、または「録音停止」ボタンで手動停止
        5. **再生**: 録音結果を確認
        
        ### 注意事項
        - Windows 10 バージョン2004以降が必要です
        - 対象アプリケーションが音声を再生している必要があります
        - プロセス固有録音が失敗した場合、システム音声を録音します
        
        ### 機能
        - ✅ アプリケーション別録音
        - ✅ リアルタイム音量調整
        - ✅ WAV形式での保存
        - ✅ 日本語対応
        """)
    
    # イベントハンドラー
    def refresh_sessions():
        sessions = app.get_audio_sessions()
        return {
            session_dropdown: gr.update(choices=sessions),
            volume_app_dropdown: gr.update(choices=sessions)
        }
    
    def on_record_start(target_app, duration):
        status, audio = app.start_recording(target_app, duration)
        return status, audio
    
    def on_record_stop():
        status, audio = app.stop_recording()
        if audio is not None:
            sample_rate, data = audio
            duration = len(data) / sample_rate
            info = f"""
            ### 録音情報
            - サンプルレート: {sample_rate} Hz
            - 時間: {duration:.2f} 秒
            - サンプル数: {len(data)}
            """
            return status, audio, info
        return status, None, "録音データなし"
    
    def on_volume_change(target_app, volume):
        return app.set_app_volume(target_app, volume)
    
    # イベントバインディング
    refresh_btn.click(
        refresh_sessions,
        outputs=[session_dropdown, volume_app_dropdown]
    )
    
    record_btn.click(
        on_record_start,
        inputs=[session_dropdown, duration_slider],
        outputs=[status_text, audio_output]
    )
    
    stop_btn.click(
        on_record_stop,
        outputs=[status_text, audio_output, audio_info]
    )
    
    volume_btn.click(
        on_volume_change,
        inputs=[volume_app_dropdown, volume_slider],
        outputs=volume_status
    )
    
    # 初期化時にセッションリストを更新
    demo.load(refresh_sessions, outputs=[session_dropdown, volume_app_dropdown])

if __name__ == "__main__":
    print("PyPAC Gradio音声録音デモを起動中...")
    print("ブラウザで http://localhost:7860 を開いてください")
    demo.launch(share=False, inbrowser=True)
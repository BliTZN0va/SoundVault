import threading
import webview
import backend
import time
import sys
import os
import socket

drag_window = None

class NativeAPI:
    def select_file_in_explorer(self, file_path):
        import subprocess
        if not os.path.exists(file_path):
            return False
        try:
            subprocess.Popen(f'explorer /select,"{file_path}"', shell=True)
            return True
        except Exception as e:
            print(f"Select file error: {e}")
            return False

    def copy_to_clipboard(self, text):
        try:
            import subprocess
            text = text.strip()
            p = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True)
            p.communicate(input=text.encode('utf-16-le') + b'\0\0')
            return True
        except Exception as e:
            print(f"Clipboard error: {e}")
            return False

    def get_app_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.getcwd()

    def select_folder(self):
        try:
            result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
            if result:
                return result[0]
            return None
        except Exception as e:
            print(f"Folder dialog error: {e}")
            return None

    def select_audio_file(self):
        try:
            file_types = ('Audio files (*.mp3;*.wav;*.flac;*.m4a;*.ogg;*.aac;*.wma;*.mp4)', 'All files (*.*)')
            result = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
            if result:
                return result[0]
            return None
        except Exception as e:
            print(f"File dialog error: {e}")
            return None

    def select_image_file(self):
        try:
            file_types = ('Image files (*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.webp)', 'All files (*.*)')
            result = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
            if result:
                return result[0]
            return None
        except Exception as e:
            print(f"File dialog error: {e}")
            return None

def find_free_port(start=5000, max_attempts=20):
    for port in range(start, start + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def start_server(port):
    backend.app.run(port=port, debug=False, use_reloader=False, threaded=True)

if __name__ == '__main__':
    print("Initializing SoundVault...")
    backend.init_app()

    port = find_free_port()
    if port is None:
        print("ERROR: No available ports found")
        sys.exit(1)

    print(f"Starting Flask server on port {port}...")
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()

    time.sleep(1.5)

    api = NativeAPI()
    drag_window = webview.create_window(
        "SoundVault",
        f'http://localhost:{port}',
        width=1300,
        height=850,
        js_api=api,
        min_size=(900, 600)
    )

    webview.start()

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import json
import time
import random
import sys
import platform
import subprocess
import mimetypes
import shutil
import uuid
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__, static_folder='public')
CORS(app)

if getattr(sys, 'frozen', False):
    DATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'SoundVault')
    os.makedirs(DATA_DIR, exist_ok=True)
    BASE_DIR = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
else:
    BASE_DIR = os.getcwd()
    DATA_DIR = BASE_DIR

CONFIG_PATH = os.path.join(DATA_DIR, 'config.json')
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')

def load_config():
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "music_folder": "music",
            "auto_detect": True,
            "auto_detect_extensions": [".mp3", ".mp4", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma", ".opus", ".aiff", ".aif", ".wv", ".mid", ".midi", ".webm"],
            "data_file": "data.json",
            "backup_folder": "database",
            "tag_colors": {},
            "theme": "dark",
            "font_size": 13,
            "glass_blur": 16,
            "glass_opacity": 55,
            "anim_speed": 100,
            "compact": False,
            "bg_style": "gradient",
            "bg_gradient": "default",
            "bg_solid": "#0b0916",
            "bg_image": "",
            "bg_opacity": 30,
            "accent": ""
        }
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_data_path():
    config = load_config()
    data_file = config.get('data_file', 'data.json')
    backup_folder = config.get('backup_folder', 'database')
    if not os.path.isabs(data_file):
        return os.path.join(DATA_DIR, backup_folder, data_file)
    return data_file

def get_music_folder():
    config = load_config()
    music_folder = config.get('music_folder', 'music')
    if not os.path.isabs(music_folder):
        if getattr(sys, 'frozen', False):
            return os.path.join(DATA_DIR, music_folder)
        return os.path.join(BASE_DIR, music_folder)
    return music_folder

def get_music_folder_abs():
    return get_music_folder()

def load_data():
    data_path = get_data_path()
    if not os.path.exists(data_path):
        return {"tracks": [], "episodes": [], "availableTags": []}
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[DATA ERROR] Failed to load: {e}")
        return {"tracks": [], "episodes": [], "availableTags": []}

def save_data(data, backup=True):
    data_path = get_data_path()
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    if backup and os.path.exists(data_path):
        backup_dir = os.path.join(os.path.dirname(data_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'data_backup_{ts}.json')
        try:
            shutil.copy2(data_path, backup_path)
            backups = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith('data_backup_')],
                reverse=True
            )
            while len(backups) > 20:
                os.remove(os.path.join(backup_dir, backups.pop()))
        except Exception as e:
            print(f"[BACKUP WARNING] {e}")
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def normalize_filename(filename):
    name, ext = os.path.splitext(filename)
    name = name.replace('_', ' ').replace('-', ' ')
    name = ' '.join(name.split())
    return name.lower(), ext.lower()

def find_existing_track(data, filepath):
    filename = os.path.basename(filepath)
    normalized_name, ext = normalize_filename(filename)
    for track in data['tracks']:
        if 'location' in track and track['location']:
            existing_file = os.path.basename(track['location'])
            existing_name, existing_ext = normalize_filename(existing_file)
            if normalized_name == existing_name:
                return track
    return None

def extract_metadata_from_path(filepath):
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)
    artist = "Unknown"
    title = name
    if "(ARTIST_" in name:
        parts = name.split("(ARTIST_")
        title = parts[0].strip()
        artist_part = parts[1].split(")")[0].strip()
        artist = artist_part.replace("_", "").strip()
    elif " - " in name:
        parts = name.split(" - ", 1)
        title = parts[1].strip()
        artist = parts[0].strip()
    folder = os.path.basename(os.path.dirname(filepath))
    return title, artist, folder

def scan_for_music_files():
    config = load_config()
    music_folder = get_music_folder()
    extensions = [ext.lower() for ext in config.get('auto_detect_extensions', ['.mp3', '.mp4'])]
    found_files = []
    if not os.path.exists(music_folder):
        return found_files
    for root, dirs, files in os.walk(music_folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                full_path = os.path.join(root, file)
                found_files.append(full_path)
    return found_files

def generate_track_id(data=None):
    if data is None:
        data = load_data()
    existing_ids = {t['id'] for t in data.get('tracks', []) if 'id' in t}
    while True:
        new_id = int(time.time_ns() // 1000) + random.randint(0, 99999)
        if new_id not in existing_ids:
            return new_id

def auto_detect_new_tracks():
    config = load_config()
    if not config.get('auto_detect', True):
        return []
    data = load_data()
    existing_locations = set()
    for t in data['tracks']:
        loc = t.get('location', '')
        if loc:
            existing_locations.add(os.path.abspath(loc))
    found_files = scan_for_music_files()
    new_tracks = []
    for filepath in found_files:
        abs_path = os.path.abspath(filepath)
        if abs_path in existing_locations:
            continue
        if find_existing_track(data, filepath):
            continue
        title, artist, folder = extract_metadata_from_path(filepath)
        new_track = {
            "id": generate_track_id(data),
            "title": title,
            "artist": artist,
            "tags": [],
            "episodes": [],
            "notes": "",
            "starred": False,
            "used": False,
            "location": abs_path
        }
        new_tracks.append(new_track)
    if new_tracks:
        data['tracks'].extend(new_tracks)
        save_data(data)
        print(f"Auto-detected {len(new_tracks)} new tracks")
    return new_tracks

class MusicFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            config = load_config()
            extensions = [ext.lower() for ext in config.get('auto_detect_extensions', ['.mp3', '.mp4'])]
            ext = os.path.splitext(event.src_path)[1].lower()
            if ext in extensions:
                print(f"New file detected: {event.src_path}")
                time.sleep(1)
                auto_detect_new_tracks()
    def on_moved(self, event):
        if not event.is_directory:
            auto_detect_new_tracks()

def start_file_watcher():
    config = load_config()
    if not config.get('auto_detect', True):
        return None
    music_folder = get_music_folder()
    if not os.path.exists(music_folder):
        os.makedirs(music_folder, exist_ok=True)
    event_handler = MusicFolderHandler()
    observer = Observer()
    observer.schedule(event_handler, music_folder, recursive=True)
    observer.start()
    print(f"File watcher started for: {music_folder}")
    return observer

file_watcher = None
app_initialized = False

def ensure_music_folder():
    music_folder = get_music_folder()
    if not os.path.exists(music_folder):
        os.makedirs(music_folder, exist_ok=True)
    return music_folder

def init_app():
    global file_watcher, app_initialized
    if app_initialized:
        return
    os.makedirs(os.path.dirname(get_data_path()), exist_ok=True)
    ensure_music_folder()
    print("Scanning for audio files...")
    new_tracks = auto_detect_new_tracks()
    if new_tracks:
        print(f"Added {len(new_tracks)} new tracks on startup")
    file_watcher = start_file_watcher()
    app_initialized = True

def get_folder_tree():
    music_folder = get_music_folder()
    tree = {"name": os.path.basename(music_folder), "path": music_folder, "type": "folder", "children": []}
    if not os.path.exists(music_folder):
        return tree
    config = load_config()
    extensions = [ext.lower() for ext in config.get('auto_detect_extensions', ['.mp3', '.mp4'])]
    def scan_dir(dirpath, parent_tree):
        try:
            entries = sorted(os.listdir(dirpath))
        except PermissionError:
            return
        for entry in entries:
            full_path = os.path.join(dirpath, entry)
            if os.path.isdir(full_path):
                child = {"name": entry, "path": full_path, "type": "folder", "children": []}
                scan_dir(full_path, child)
                if child["children"]:
                    parent_tree["children"].append(child)
            else:
                ext = os.path.splitext(entry)[1].lower()
                if ext in extensions:
                    parent_tree["children"].append({"name": entry, "path": full_path, "type": "file"})
    scan_dir(music_folder, tree)
    return tree

def get_track_color(tag):
    config = load_config()
    tag_colors = config.get('tag_colors', {})
    return tag_colors.get(tag, '#555')

@app.route('/api/music', methods=['GET'])
def get_music():
    try:
        data = load_data()
        config = load_config()
        tag_colors = config.get('tag_colors', {})
        return jsonify({"tracks": data.get("tracks", []), "episodes": data.get("episodes", []), "availableTags": data.get("availableTags", []), "tagColors": tag_colors})
    except Exception as e:
        print(f"[API ERROR] {e}")
        return jsonify({"tracks": [], "episodes": [], "availableTags": [], "tagColors": {}}), 200

@app.route('/api/tracks', methods=['POST'])
def create_track():
    data = load_data()
    body = request.json
    new_track = {
        "id": generate_track_id(data),
        "title": body.get('title', ''),
        "artist": body.get('artist', 'Unknown'),
        "tags": body.get('tags', []),
        "episodes": body.get('episodes', []),
        "notes": body.get('notes', ''),
        "starred": False,
        "used": False,
        "location": body.get('location', '')
    }
    data['tracks'].append(new_track)
    save_data(data)
    return jsonify(new_track)

@app.route('/api/tracks/<int:track_id>', methods=['PUT'])
def update_track(track_id):
    data = load_data()
    idx = next((i for i, t in enumerate(data['tracks']) if t['id'] == track_id), None)
    if idx is None:
        return '', 404
    data['tracks'][idx] = {**data['tracks'][idx], **request.json}
    save_data(data)
    return jsonify(data['tracks'][idx])

@app.route('/api/tracks/<int:track_id>/location', methods=['PUT'])
def update_track_location(track_id):
    data = load_data()
    idx = next((i for i, t in enumerate(data['tracks']) if t['id'] == track_id), None)
    if idx is None:
        return '', 404
    location = request.json.get('location', '')
    if location:
        data['tracks'][idx]['location'] = location
        save_data(data)
    return jsonify(data['tracks'][idx])

@app.route('/api/tracks/<int:track_id>', methods=['DELETE'])
def delete_track(track_id):
    data = load_data()
    data['tracks'] = [t for t in data['tracks'] if t['id'] != track_id]
    save_data(data)
    return jsonify({"ok": True})

@app.route('/api/tracks/batch', methods=['POST'])
def batch_update_tracks():
    data = load_data()
    body = request.json
    track_ids = {int(i) for i in body.get('ids', [])}
    updates = body.get('updates', {})
    for track in data['tracks']:
        if track['id'] in track_ids:
            track.update(updates)
    save_data(data)
    return jsonify({"ok": True})

@app.route('/api/episodes', methods=['POST'])
def add_episode():
    data = load_data()
    name = request.json.get('name')
    if name and name.lower() not in [e.lower() for e in data['episodes']]:
        data['episodes'].append(name)
        save_data(data)
    return jsonify(data['episodes'])

@app.route('/api/episodes', methods=['DELETE'])
def delete_episode():
    data = load_data()
    name = request.json.get('name')
    if name:
        matched = next((e for e in data['episodes'] if e.lower() == name.lower()), None)
        if matched:
            data['episodes'].remove(matched)
            for track in data['tracks']:
                if matched in track.get('episodes', []):
                    track['episodes'].remove(matched)
            save_data(data)
    return jsonify(data['episodes'])

@app.route('/api/tags', methods=['POST'])
def add_tag():
    data = load_data()
    name = request.json.get('name')
    if name and name.lower() not in [t.lower() for t in data['availableTags']]:
        data['availableTags'].append(name)
        save_data(data)
    return jsonify(data['availableTags'])

@app.route('/api/tags', methods=['DELETE'])
def delete_tag():
    data = load_data()
    name = request.json.get('name')
    if name:
        matched = next((t for t in data['availableTags'] if t.lower() == name.lower()), None)
        if matched:
            data['availableTags'].remove(matched)
            for track in data['tracks']:
                if matched in track.get('tags', []):
                    track['tags'].remove(matched)
            save_data(data)
    return jsonify(data['availableTags'])

@app.route('/api/tags/color', methods=['PUT'])
def update_tag_color():
    config = load_config()
    body = request.json
    tag = body.get('tag')
    color = body.get('color')
    if tag and color:
        tag_colors = config.get('tag_colors', {})
        tag_colors[tag] = color
        config['tag_colors'] = tag_colors
        save_config(config)
        return jsonify({"ok": True})
    return jsonify({"error": "tag and color required"}), 400

@app.route('/api/tracks/<int:track_id>/play', methods=['GET'])
def play_track(track_id):
    data = load_data()
    track = next((t for t in data['tracks'] if t['id'] == track_id), None)
    if track is None:
        return '', 404
    location = track.get('location', '').strip()
    if not location:
        return jsonify({"error": "No location set"}), 400
    if not os.path.exists(location):
        return jsonify({"error": "File not found"}), 404
    try:
        if platform.system() == 'Darwin':
            subprocess.run(['open', location], check=False)
        elif platform.system() == 'Linux':
            subprocess.run(['xdg-open', location], check=False)
        else:
            os.startfile(location)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tracks/<int:track_id>/reveal', methods=['POST'])
def reveal_track(track_id):
    data = load_data()
    track = next((t for t in data['tracks'] if t['id'] == track_id), None)
    if track is None:
        return '', 404
    location = track.get('location', '').strip()
    if not location:
        return jsonify({"error": "No location set"}), 400
    if not os.path.exists(location):
        return jsonify({"error": "File not found"}), 404
    try:
        if platform.system() == 'Darwin':
            subprocess.run(['open', '-R', location], check=False)
        elif platform.system() == 'Linux':
            subprocess.run(['xdg-open', os.path.dirname(location)], check=False)
        else:
            subprocess.run(['explorer', '/select,' + location], check=False)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tracks/<int:track_id>/download', methods=['GET'])
def download_track(track_id):
    data = load_data()
    track = next((t for t in data['tracks'] if t['id'] == track_id), None)
    if track is None:
        return '', 404
    location = track.get('location', '').strip()
    if not location or not os.path.exists(location):
        return jsonify({"error": "File not found"}), 404
    filename = os.path.basename(location)
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = 'application/octet-stream'
    return send_from_directory(
        os.path.dirname(location),
        filename,
        mimetype=mime_type,
        as_attachment=False
    )

@app.route('/api/tracks/<int:track_id>/fileinfo', methods=['GET'])
def file_info(track_id):
    data = load_data()
    track = next((t for t in data['tracks'] if t['id'] == track_id), None)
    if track is None:
        return '', 404
    location = track.get('location', '').strip()
    if not location or not os.path.exists(location):
        return jsonify({"error": "File not found"}), 404
    filename = os.path.basename(location)
    filesize = os.path.getsize(location)
    _, ext = os.path.splitext(location)
    return jsonify({
        "filename": filename,
        "filesize": filesize,
        "path": location,
        "extension": ext.lower()
    })

@app.route('/api/folders', methods=['GET'])
def get_folders():
    try:
        tree = get_folder_tree()
        return jsonify(tree)
    except Exception as e:
        print(f"[FOLDERS ERROR] {e}")
        return jsonify({"name": "music", "path": "", "type": "folder", "children": []})

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(load_config())

@app.route('/api/config', methods=['PUT'])
def update_config():
    config = load_config()
    updates = request.json
    allowed_fields = ['music_folder', 'data_file', 'backup_folder', 'auto_detect', 'auto_detect_extensions', 'tag_colors', 'theme', 'font_size', 'glass_blur', 'glass_opacity', 'anim_speed', 'compact', 'bg_style', 'bg_gradient', 'bg_solid', 'bg_image', 'bg_opacity', 'accent']
    for key in updates:
        if key not in allowed_fields:
            return jsonify({"error": f"Invalid config field: {key}"}), 400
    if 'auto_detect_extensions' in updates:
        extensions = updates['auto_detect_extensions']
        if not isinstance(extensions, list):
            return jsonify({"error": "auto_detect_extensions must be a list"}), 400
        for ext in extensions:
            if not isinstance(ext, str) or not ext.startswith('.'):
                return jsonify({"error": f"Invalid extension format: {ext}"}), 400
    config.update(updates)
    save_config(config)
    if 'music_folder' in updates or 'auto_detect' in updates:
        global file_watcher
        if file_watcher:
            try:
                file_watcher.stop()
                file_watcher = None
            except:
                pass
        if config.get('auto_detect', True):
            file_watcher = start_file_watcher()
    return jsonify(config)

@app.route('/api/scan', methods=['POST'])
def manual_scan():
    new_tracks = auto_detect_new_tracks()
    return jsonify({"added": len(new_tracks), "tracks": new_tracks})

@app.route('/api/startup', methods=['POST'])
def startup():
    try:
        init_app()
        return jsonify({"ok": True, "message": "Startup complete"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_data():
    data = load_data()
    config = load_config()
    export = {
        "exported_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "data": data,
        "config": {k: v for k, v in config.items() if k != 'tag_colors'}
    }
    export.update({"tag_colors": config.get('tag_colors', {})})
    return jsonify(export)

@app.route('/api/import', methods=['POST'])
def import_data():
    body = request.json
    imported_data = body.get('data')
    if not imported_data or 'tracks' not in imported_data:
        return jsonify({"error": "Invalid import data"}), 400
    merge = body.get('merge', True)
    current = load_data()
    if merge:
        existing_paths = {os.path.abspath(t.get('location', '')) for t in current['tracks'] if t.get('location')}
        existing_ids = {t['id'] for t in current['tracks']}
        new_count = 0
        for t in imported_data.get('tracks', []):
            if os.path.abspath(t.get('location', '')) in existing_paths:
                continue
            if t.get('id') in existing_ids:
                t['id'] = generate_track_id(current)
            current['tracks'].append(t)
            existing_paths.add(os.path.abspath(t.get('location', '')))
            new_count += 1
        for tag in imported_data.get('availableTags', []):
            if tag not in current.get('availableTags', []):
                current.setdefault('availableTags', []).append(tag)
        for ep in imported_data.get('episodes', []):
            if ep not in current.get('episodes', []):
                current.setdefault('episodes', []).append(ep)
        save_data(current)
        return jsonify({"ok": True, "imported": new_count})
    else:
        save_data(imported_data)
        return jsonify({"ok": True, "imported": len(imported_data.get('tracks', []))})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    data = load_data()
    tracks = data.get('tracks', [])
    total = len(tracks)
    used = sum(1 for t in tracks if t.get('used'))
    starred = sum(1 for t in tracks if t.get('starred'))
    tagged = sum(1 for t in tracks if t.get('tags'))
    with_location = sum(1 for t in tracks if t.get('location'))
    tags_counts = {}
    for t in tracks:
        for tag in t.get('tags', []):
            tags_counts[tag] = tags_counts.get(tag, 0) + 1
    return jsonify({
        "total": total,
        "used": used,
        "unused": total - used,
        "starred": starred,
        "tagged": tagged,
        "withLocation": with_location,
        "topTags": dict(sorted(tags_counts.items(), key=lambda x: -x[1])[:10]),
        "backupCount": len(os.listdir(os.path.join(os.path.dirname(get_data_path()), 'backups'))) if os.path.exists(os.path.join(os.path.dirname(get_data_path()), 'backups')) else 0
    })

@app.route('/api/tracks/batch/tags', methods=['POST'])
def batch_tag_tracks():
    data = load_data()
    body = request.json
    track_ids = [int(i) for i in body.get('ids', [])]
    tags_to_add = body.get('addTags', [])
    tags_to_remove = body.get('removeTags', [])
    for track in data['tracks']:
        if track['id'] in track_ids:
            current_tags = set(track.get('tags', []))
            if tags_to_add:
                current_tags.update(tags_to_add)
            if tags_to_remove:
                current_tags.difference_update(tags_to_remove)
            track['tags'] = list(current_tags)
    save_data(data)
    return jsonify({"ok": True, "updated": len(track_ids)})

@app.route('/api/tracks/batch/delete', methods=['POST'])
def batch_delete_tracks():
    data = load_data()
    track_ids = {int(i) for i in request.json.get('ids', [])}
    data['tracks'] = [t for t in data['tracks'] if t['id'] not in track_ids]
    save_data(data)
    return jsonify({"ok": True, "deleted": len(track_ids)})

@app.route('/api/tracks/batch/episodes', methods=['POST'])
def batch_episode_tracks():
    data = load_data()
    body = request.json
    track_ids = {int(i) for i in body.get('ids', [])}
    ep_to_add = body.get('addEpisodes', [])
    ep_to_remove = body.get('removeEpisodes', [])
    for track in data['tracks']:
        if track['id'] in track_ids:
            current_eps = set(track.get('episodes', []))
            if ep_to_add:
                current_eps.update(ep_to_add)
            if ep_to_remove:
                current_eps.difference_update(ep_to_remove)
            track['episodes'] = list(current_eps)
    save_data(data)
    return jsonify({"ok": True, "updated": len(track_ids)})

@app.route('/api/log', methods=['POST'])
def log_message():
    try:
        data = request.json
        level = data.get('level', 'INFO')
        message = data.get('message', '')
        print(f"[{level}] {message}")
        return jsonify({"ok": True})
    except Exception as e:
        print(f"[LOG ERROR] {e}")
        return jsonify({"ok": False}), 500

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(PUBLIC_DIR, path)

@app.route('/', methods=['GET'])
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

if __name__ == '__main__':
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"CONFIG_PATH: {CONFIG_PATH}")
    print(f"DATA_PATH: {get_data_path()}")
    print(f"MUSIC_FOLDER: {get_music_folder()}")
    print("SoundVault server running on http://localhost:5000")
    try:
        app.run(port=5000, debug=False, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        if file_watcher:
            file_watcher.stop()
        print("\nShutting down...")

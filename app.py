import hashlib
import json
import os
import requests

from flask import Flask, render_template, jsonify

from main import index_videos_to_file
import SECRET

app = Flask(__name__)

COVERS_DIR = os.path.join(app.static_folder, "covers")
os.makedirs(COVERS_DIR, exist_ok=True)

YANDEX_TOKEN = SECRET.TOKEN
YANDEX_PATH = "/mytube"
VIDEOS_JSON = "videos.json"


def download_cover(cover_url):
    if not cover_url:
        return None
    file_name = hashlib.md5(cover_url.encode()).hexdigest() + ".jpg"
    file_path = os.path.join(COVERS_DIR, file_name)

    if not os.path.exists(file_path):
        try:
            response = requests.get(cover_url)
            response.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Скачана обложка: {file_path}")
        except requests.RequestException as e:
            print(f"Ошибка скачивания обложки {cover_url}: {e}")
            return None
    return f"covers/{file_name}"


@app.route('/')
def index():
    try:
        with open(VIDEOS_JSON, "r", encoding="utf-8") as f:
            shows = json.load(f)
    except FileNotFoundError:
        shows = []
        print("Файл videos.json не найден")

    for show in shows:
        show["cover_path"] = download_cover(show.get("cover_url"))

    return render_template('index.html', shows=shows)


@app.route('/reindex')
def reindex():
    try:
        shows = index_videos_to_file(YANDEX_TOKEN, YANDEX_PATH, VIDEOS_JSON)
        return jsonify({"status": "ok", "shows": [show["show_name"] for show in shows]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

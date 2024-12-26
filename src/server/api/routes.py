from flask import Flask, jsonify
from threading import Thread
from ..gstreamer.stream_manager import StreamManager

app = Flask(__name__)
stream_manager = StreamManager()

def start_server(port=5001):
    server_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=port))
    server_thread.daemon = True
    server_thread.start()
    return server_thread

@app.route('/start', methods=['POST'])
def start_stream():
    success = stream_manager.start_stream()
    return jsonify({"status": "started" if success else "error"})

@app.route('/stop', methods=['POST'])
def stop_stream():
    success = stream_manager.stop_stream()
    return jsonify({"status": "stopped" if success else "error"})
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst
import requests


class StreamReceiver(QThread):
    frame_received = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = False
        Gst.init(None)

    def run(self):
        try:
            pipeline_str = (
                'avfvideosrc device-index=0 ! videoconvert ! videoscale ! '
                'video/x-raw,width=1280,height=720,format=RGB,framerate=30/1 ! '
                'videoconvert ! videorate ! appsink name=sink emit-signals=true'
            )
            self.pipeline = Gst.parse_launch(pipeline_str)
            sink = self.pipeline.get_by_name('sink')

            if not sink:
                self.error_occurred.emit("Failed to create video sink")
                return

            sink.connect('new-sample', self.on_new_sample)

            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                self.error_occurred.emit("Failed to start camera stream")
                return

            self.running = True
            bus = self.pipeline.get_bus()
            while self.running:
                msg = bus.timed_pop_filtered(
                    Gst.CLOCK_TIME_NONE,
                    Gst.MessageType.ERROR | Gst.MessageType.EOS
                )
                if msg:
                    if msg.type == Gst.MessageType.ERROR:
                        err, _ = msg.parse_error()
                        self.error_occurred.emit(f"Stream error: {err.message}")
                    break

        except Exception as e:
            self.error_occurred.emit(f"Stream error: {str(e)}")

    def on_new_sample(self, sink):
        sample = sink.emit('pull-sample')
        buffer = sample.get_buffer()
        caps = sample.get_caps()

        width = caps.get_structure(0).get_value('width')
        height = caps.get_structure(0).get_value('height')

        success, mapinfo = buffer.map(Gst.MapFlags.READ)
        if success:
            image = QImage(
                mapinfo.data,
                width,
                height,
                width * 3,  # RGB stride
                QImage.Format_RGB888
            )
            self.frame_received.emit(image)
            buffer.unmap(mapinfo)

        return Gst.FlowReturn.OK

    def stop(self):
        self.running = False
        if hasattr(self, 'pipeline'):
            self.pipeline.set_state(Gst.State.NULL)


class VideoViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Stream Viewer")
        self.receiver = StreamReceiver()
        self.receiver.frame_received.connect(self.update_frame)
        self.receiver.error_occurred.connect(self.on_error)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("QLabel { background-color: black; border: 2px solid #333; }")
        self.video_label.setMinimumSize(640, 480)
        layout.addWidget(self.video_label)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
           QProgressBar {
               border: 2px solid grey;
               border-radius: 5px;
               text-align: center;
           }
           QProgressBar::chunk {
               background-color: #4CAF50;
               width: 20px;
           }
       """)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("QLabel { color: white; font-size: 14px; }")
        layout.addWidget(self.status_label)

        button_layout = QVBoxLayout()
        start_button = QPushButton("Start Stream")
        start_button.setStyleSheet("""
           QPushButton {
               background-color: #4CAF50;
               color: white;
               border: none;
               padding: 8px;
               border-radius: 4px;
               font-size: 14px;
           }
           QPushButton:hover {
               background-color: #45a049;
           }
       """)
        start_button.clicked.connect(self.start_stream)
        button_layout.addWidget(start_button)

        stop_button = QPushButton("Stop Stream")
        stop_button.setStyleSheet("""
           QPushButton {
               background-color: #f44336;
               color: white;
               border: none;
               padding: 8px;
               border-radius: 4px;
               font-size: 14px;
           }
           QPushButton:hover {
               background-color: #da190b;
           }
       """)
        stop_button.clicked.connect(self.stop_stream)
        button_layout.addWidget(stop_button)

        layout.addLayout(button_layout)

        # Set dark theme for main window
        self.setStyleSheet("""
           QMainWindow {
               background-color: #2b2b2b;
           }
           QWidget {
               background-color: #2b2b2b;
           }
       """)

        self.resize(1280, 800)

    def start_stream(self):
        self.status_label.setText("Starting stream...")
        self.progress.setMaximum(0)
        self.progress.show()
        self.video_label.setText("")
        requests.post('http://localhost:5001/start')
        self.receiver.start()

    def stop_stream(self):
        self.status_label.setText("Stream stopped")
        self.progress.hide()
        requests.post('http://localhost:5001/stop')
        self.receiver.stop()
        self.video_label.setText("Stream Closed")
        self.video_label.setStyleSheet(
            "QLabel { background-color: black; border: 2px solid #333; color: white; font-size: 18px; }")

    def on_error(self, error_msg):
        self.status_label.setText(error_msg)
        self.progress.hide()

    def update_frame(self, qimage):
        if self.progress.isVisible():
            self.progress.hide()
            self.status_label.setText("Stream active")
        pixmap = QPixmap.fromImage(qimage)
        scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.receiver.stop()
        super().closeEvent(event)
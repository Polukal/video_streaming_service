import sys
from PyQt5.QtWidgets import QApplication
from src.client.viewer import VideoViewer
from src.server.api.routes import start_server

def main():
    app = QApplication(sys.argv)
    start_server(port=5001)
    viewer = VideoViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
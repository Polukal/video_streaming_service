import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst


class GStreamerPipeline:
    def __init__(self):
        Gst.init(None)
        self.pipeline = None
        self.create_pipeline()

    def create_pipeline(self):
        pipeline_str = (
            'avfvideosrc device-index=0 ! videoconvert ! x264enc tune=zerolatency ! '
            'rtph264pay ! udpsink host=127.0.0.1 port=5002'
        )
        self.pipeline = Gst.parse_launch(pipeline_str)

    def start(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.PLAYING)
            return True
        return False

    def stop(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            return True
        return False
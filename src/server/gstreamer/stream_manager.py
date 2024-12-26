class StreamManager:
    def __init__(self):
        self.pipeline = None
        self.is_streaming = False

    def start_stream(self):
        from .pipeline import GStreamerPipeline
        if not self.is_streaming:
            self.pipeline = GStreamerPipeline()
            success = self.pipeline.start()
            self.is_streaming = success
            return success
        return False

    def stop_stream(self):
        if self.is_streaming and self.pipeline:
            success = self.pipeline.stop()
            self.is_streaming = not success
            return success
        return False
from app.playback.detector import PlaybackDetector

detector = PlaybackDetector()

print(detector.is_stremio_running())

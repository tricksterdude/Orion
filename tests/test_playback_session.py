from app.playback.session import PlaybackSession


print("=" * 60)
print("PLAYBACK SESSION")
print("=" * 60)

print()

session = PlaybackSession()

print(session.current())

print()

session.start()

print(session.current())
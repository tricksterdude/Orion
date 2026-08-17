import asyncio

from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager,
)


async def main():

    print("=" * 60)
    print("WINDOWS MEDIA SESSIONS")
    print("=" * 60)
    print()

    manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()

    sessions = manager.get_sessions()

    print(f"Found {len(sessions)} session(s)")
    print()

    if len(sessions) == 0:
        return

    for i, session in enumerate(sessions, start=1):

        print("-" * 60)
        print(f"Session {i}")

        try:
            print("App    :", session.source_app_user_model_id)

            info = await session.try_get_media_properties_async()

            print("Title  :", info.title)
            print("Artist :", info.artist)

            playback = session.get_playback_info()

            print("Status :", playback.playback_status)

        except Exception as ex:
            print("ERROR:", ex)


if __name__ == "__main__":
    asyncio.run(main())
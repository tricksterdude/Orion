class EventBus:

    def __init__(self):

        self._listeners = {}

    def subscribe(self, event_type, callback):

        self._listeners.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type, callback):

        if event_type not in self._listeners:
            return

        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)

    def publish(self, event):

        for callback in self._listeners.get(type(event), []):

            callback(event)
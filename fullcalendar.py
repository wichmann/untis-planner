from collections.abc import Callable
from pathlib import Path
from typing import Any

from nicegui import events, ui


class FullCalendar(ui.element, component='fullcalendar.js'):
    """
    Provides a NiceGUI element to create a interactive FullCalendar calendar
    display. This calendar can be customized with various options and can
    handle events such as clicks and view changes. The calendar supports
    adding, removing, and clearing events dynamically.

    Based on: https://github.com/zauberzeug/nicegui/tree/main/examples/fullcalendar

    References:
    - FullCalendar library: https://fullcalendar.io/
    - FullCalendar documentation: https://fullcalendar.io/docs
    - Example of the FullCalendar library with plugins: https://github.com/dorel14/NiceGui-FullCalendar_more_Options
    """

    def __init__(self, options: dict[str, Any], custom_css: str, on_click: Callable | None = None, on_change: Callable | None = None) -> None:
        """Creates a FullCalendar component.

        :param options: dictionary of FullCalendar properties for customization, such as "initialView", "slotMinTime", "slotMaxTime", "allDaySlot", "timeZone", "height", and "events".
        :param custom_css: custom CSS for styling the calendar.
        :param on_click: callback that is called when a calendar event is clicked.
        :param on_change: callback that is called when the calendar view changes.
        """
        super().__init__()
        self.add_resource(Path(__file__).parent / 'lib')
        self._props['options'] = options
        self._props['custom_css'] = custom_css
        self._update_method = 'update_calendar'

        if on_click:
            self.on('click', lambda e: events.handle_event(on_click, e))
        if on_change:
            self.on('change', lambda e: events.handle_event(on_change, e))

    def add_event(self, title: str, start: str, end: str, **kwargs) -> None:
        """Adds an event to the calendar.

        :param title: title of the event
        :param start: start time of the event
        :param end: end time of the event
        """
        event_dict = {'title': title, 'start': start, 'end': end, **kwargs}
        self._props['options']['events'].append(event_dict)

    def remove_event(self, title: str, start: str, end: str) -> None:
        """Removes an event from the calendar.

        :param title: title of the event
        :param start: start time of the event
        :param end: end time of the event
        """
        for event in self._props['options']['events']:
            if event['title'] == title and event['start'] == start and event['end'] == end:
                self._props['options']['events'].remove(event)
                break

    def clear_events(self) -> None:
        """Removes all events from the calendar."""
        self._props['options']['events'] = []

    @property
    def events(self) -> list[dict]:
        """List of events currently displayed in the calendar."""
        return self._props['options']['events']

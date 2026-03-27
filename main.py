#!/usr/bin/env python3

"""
A NiceGUI app to plan appointments for multiple teachers using timetables
from WebUntis. It fetches the timetables of specified teachers and displays a
weekly overview highlighting busy slots.
"""

import configparser
from datetime import datetime, timedelta

from fullcalendar import FullCalendar

import untisplaner
from nicegui import app, ui, events


APP_TITLE = 'UntisPlaner'


def prepare_events():
    """
    Prepare calendar events based on the selected teachers and date range.
    """
    # create list with five colors for teachers
    teacher_colors = [
        "#f5876f",
        "#fad07b",
        "#55d1da",
        "#c77dff",
        "#ff6f91"
    ]
    global up, fullCalendar
    calendar_events = []
    for i, teacher in enumerate(app.storage.selected_teachers):
        current_teacher = up.session.teachers().filter(surname=teacher)[0]
        tt = up.get_timetable(current_teacher, start=app.storage.start_date, end=app.storage.end_date)
        for po in tt:
            # filter out periods that aren't lessons
            if po.klassen and po.subjects[0].name != '---':
                for _ in po.teachers:
                    event = {
                        "title": teacher,
                        "start": str(po.start),
                        "end": str(po.end),
                        'display': 'block',
                        'color': teacher_colors[i % len(teacher_colors)],
                        'resourceId': str(po.klassen),
                    }
                    fullCalendar.add_event(title=teacher, start=str(po.start), end=str(po.end), display='block', color=teacher_colors[i % len(teacher_colors)], resourceId=str(po.klassen))
                    calendar_events.append(event)


def prepare_dropdown(teacher_list):  
    teacher_names = [teacher.surname for teacher in teacher_list]
    ui.select(options=teacher_names, multiple=True, with_input=True, new_value_mode='add-unique',
              clearable=True, label="Select teachers to display:", on_change=handle_teacher_change)


def handle_teacher_change(event: events.GenericEventArguments):
    app.storage.selected_teachers = event.value
    prepare_events()


def prepare_calendar():
    global fullCalendar
    options = {
            "editable": False,
            "selectable": False,
            "businessHours": {
                "daysOfWeek": [1, 2, 3, 4, 5],
                "startTime": "08:00",
                "endTime": "16:00",
            },
            "locale": "de",
            "height": "800px",
            "timeZone": 'local',
            "allDaySlot": False,
            "nowIndicator": True,
            "weekends": False,
            "headerToolbar": {
                "left": "",
                "center": "title",
                "right": "prev,next",
            },
            "slotMinTime": "06:00:00",
            "slotMaxTime": "18:00:00",
            "initialView": "timeGridWeek",
            'height': 'auto',
            'width': 'auto',
            'events': [],
        }
    custom_css="""
        .fc-event-time {
            display: none;
        }
        .fc-event-title {
            display: none;
            font-weight: 800;
        }
    """
    fullCalendar = FullCalendar(options, custom_css, on_click=handle_click, on_change=handle_change)


def handle_click(event: events.GenericEventArguments):
    if 'info' in event.args:
        print(f"Clicked on event: {event.args['info']}")
        ui.notify(event.args['info']['event'])


def handle_change(event: events.GenericEventArguments):
    if 'info' in event.args:
        start_date = datetime.fromisoformat(event.args['info']['startStr']).date()
        end_date = datetime.fromisoformat(event.args['info']['endStr']).date()
        print(f"Current view range: {start_date} - {end_date}")
        app.storage.start_date = start_date
        app.storage.end_date = end_date
        prepare_events()


def main():
    # load configuration from file
    configfile = 'webuntis-config.ini'
    config = configparser.ConfigParser()
    config.read(configfile)
    # create an UntisPlaner instance
    cred = config['credentials']
    global up
    up = untisplaner.UntisPlaner(cred['user'], cred['password'], cred['server'], cred['school'])
    teacher_list = up.get_list_of_teachers()
    # define defaults
    app.storage.start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
    app.storage.end_date = app.storage.start_date + timedelta(days=6)
    app.storage.selected_teachers = []
    # build UI elements
    ui.html(f'<h1 style="text-align: center;">{APP_TITLE}</h1>')
    prepare_dropdown(teacher_list)
    prepare_calendar()
    # run the NiceGUI app
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()

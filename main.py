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

DEBUG = False



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
            'editable': False,
            'selectable': False,
            'businessHours': {
                'daysOfWeek': [1, 2, 3, 4, 5],
                'startTime': '08:00',
                'endTime': '16:00',
            },
            'locale': 'de',
            'height': '800px',
            'timeZone': 'local',
            'allDaySlot': False,
            'nowIndicator': True,
            'weekends': False,
            'headerToolbar': {
                'left': '',
                'center': 'title',
                'right': 'prev,next',
            },
            'slotMinTime': '06:00:00',
            'slotMaxTime': '21:00:00',
            'initialView': 'timeGridWeek',
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
        e = event.args['info']['event']
        title = e['title']
        classes = e['extendedProps']['classes']
        subjects = e['extendedProps']['subjects']
        if DEBUG:
            ui.notify(f'Teacher: {title}, Class: {classes}, Subject: {subjects}')


def handle_change(event: events.GenericEventArguments):
    if 'info' in event.args:
        start_date = datetime.fromisoformat(event.args['info']['startStr']).date()
        end_date = datetime.fromisoformat(event.args['info']['endStr']).date()
        if DEBUG:
            print(f'Current view range: {start_date} - {end_date}')
        app.storage.start_date = start_date
        app.storage.end_date = end_date
        prepare_events()


@ui.refreshable
def prepare_legend():
    with ui.row().classes('justify-center gap-12 w-full'):
        for i, teacher_name in enumerate(app.storage.selected_teachers):
            with ui.column():
                color = TEACHER_COLORS[i % len(TEACHER_COLORS)]
                ui.label(teacher_name).classes('text-lg').style(f'background-color: {color}; padding: 10px 20px; border-radius: 10px; color: white; font-weight: bold;font-size: 125%')
                ui.space()


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
    ui.html(f'<h1>{APP_TITLE}</h1>')
    prepare_dropdown(teacher_list)
    prepare_calendar()
    prepare_legend()
    # run the NiceGUI app
    ui.run(host='0.0.0.0', port=8080, favicon='📆', language='de-DE')


if __name__ in {'__main__', '__mp_main__'}:
    main()

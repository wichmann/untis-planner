#!/usr/bin/env python3

"""
A NiceGUI app to plan appointments for multiple teachers using timetables
from WebUntis. It fetches the timetables of specified teachers and displays a
weekly overview highlighting busy slots.
"""

import configparser
from datetime import datetime, timedelta

from fastapi import Request
from starlette.responses import RedirectResponse
from nicegui import app, ui, events

import untisplanner
from fullcalendar import FullCalendar


APP_TITLE = 'UntisPlanner'

DEBUG = False

# create list with five colors for teachers
TEACHER_COLORS = [
    "#f5766f",
    '#fad07b',
    "#62d5dd",
    '#c77dff',
    "#71d93a"
]

UNTIS_API = None
LESSON_CALENDAR = None


def prepare_events():
    """
    Prepare calendar events based on the selected teachers and date range.
    """
    LESSON_CALENDAR.clear_events()
    for i, teacher in enumerate(app.storage.selected_teachers):
        current_teacher = UNTIS_API.session.teachers().filter(surname=teacher)[0]
        tt = UNTIS_API.get_timetable(current_teacher, start=app.storage.start_date, end=app.storage.end_date)
        for po in tt:
            # filter out periods that aren't lessons
            if po.klassen and po.subjects[0].name != '---':
                try:
                    for _ in po.teachers:
                        # remove existing event for the teacher in the same time slot to avoid duplicates
                        LESSON_CALENDAR.remove_event(title=teacher, start=str(po.start), end=str(po.end))
                        # create new event for all periods of the teacher
                        LESSON_CALENDAR.add_event(title=teacher, start=str(po.start), end=str(po.end),
                                            display='block', color=TEACHER_COLORS[i % len(TEACHER_COLORS)],
                                            classes=', '.join(str(klasse) for klasse in po.klassen),
                                            subjects=', '.join(str(subject) for subject in po.subjects))
                except IndexError as e:
                    if DEBUG:
                        ui.notify(f"Error processing period: {e}", color="error")


def prepare_dropdown(teacher_list):
    """Gets last names for all teachers and prepares the dropdown."""
    teacher_names = [teacher.surname for teacher in teacher_list]
    ui.select(options=teacher_names, multiple=True, with_input=True, new_value_mode='add-unique',
              clearable=True, label='Select teachers to display:', on_change=handle_teacher_change)


def handle_teacher_change(event: events.GenericEventArguments):
    """
    Updates the list of selected teachers based on changes in the dropdown.
    Reverts the list to the previous value if more than 5 items are selected.
    """
    if len(event.value) > 5:
        event.sender.value = app.storage.selected_teachers
        ui.notify("⚠️ Maximum 5 teachers allowed", color="warning")
    else:
        if DEBUG:
            added = set(event.value) - set(app.storage.selected_teachers)
            removed = set(app.storage.selected_teachers) - set(event.value)
            if added:
                ui.notify(f'Added: {", ".join(added)}')
            if removed:
                ui.notify(f'Removed: {", ".join(removed)}')
        app.storage.selected_teachers = event.value
        prepare_events()
        prepare_legend.refresh()


def prepare_calendar():
    """
    Prepares the FullCalendar component with specified options and styling. No
    events are added at this stage; they will be added dynamically based on the
    selected teachers and date range by prepare_events().
    """
    global LESSON_CALENDAR
    options = {
            'editable': False,
            'selectable': False,
            'businessHours': {
                'daysOfWeek': [1, 2, 3, 4, 5],
                'startTime': '08:00',
                'endTime': '16:00',
            },
            'locale': 'de',
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
    LESSON_CALENDAR = FullCalendar(options, custom_css, on_click=handle_click, on_change=handle_change)


def handle_click(event: events.GenericEventArguments):
    """Show notification with information about the clicked lesson."""
    if 'info' in event.args:
        e = event.args['info']['event']
        title = e['title']
        classes = e['extendedProps']['classes']
        subjects = e['extendedProps']['subjects']
        if DEBUG:
            ui.notify(f'Teacher: {title}, Class: {classes}, Subject: {subjects}')


def handle_change(event: events.GenericEventArguments):
    """Update the date range in storage when the calendar view changes and refresh events."""
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
    """Prepares a legend showing the selected teachers with their corresponding colors."""
    with ui.row().classes('justify-center gap-12 w-full'):
        for i, teacher_name in enumerate(app.storage.selected_teachers):
            with ui.column():
                color = TEACHER_COLORS[i % len(TEACHER_COLORS)]
                s = f'background-color: {color}; color: white; padding: 10px 20px;' \
                     'border-radius: 10px; font-weight: bold;font-size: 125%'
                ui.label(teacher_name).classes('text-lg').style(s)
                ui.space()


def preload_logged_in_user(request: Request, teacher_list):
    """Preloads the logged-in user's name into the dropdown if available."""
    if 'X-authentik-username' in request.headers:
        username_from_request = request.headers['X-authentik-username']
        if DEBUG:
            print(f"Authenticated user: {username_from_request}")
        teacher_name = [teacher.surname for teacher in teacher_list if str(teacher.surname).casefold() == str(username_from_request).casefold()]
        if teacher_name:
            app.storage.selected_teachers.append(teacher_name[0])
            prepare_events()
            prepare_legend.refresh()
        return username_from_request
    return None


@ui.page('/')
def main(request: Request) -> RedirectResponse | None:
    """Main function to set up the NiceGUI app, load configuration, and initialize components."""
    # load configuration from file
    configfile = 'webuntis-config.ini'
    config = configparser.ConfigParser()
    config.read(configfile)
    # create an UntisPlaner instance
    cred = config['credentials']
    global UNTIS_API
    UNTIS_API = untisplanner.UntisPlanner(cred['user'], cred['password'], cred['server'], cred['school'])
    teacher_list = UNTIS_API.get_list_of_teachers()
    # define defaults
    app.storage.start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
    app.storage.end_date = app.storage.start_date + timedelta(days=6)
    app.storage.selected_teachers = []
    # build UI elements
    ui.html(f'<h1>{APP_TITLE}</h1>')
    prepare_dropdown(teacher_list)
    prepare_calendar()
    prepare_legend()
    username = preload_logged_in_user(request, teacher_list)
    ui.label(str(username))


if __name__ in {'__main__', '__mp_main__'}:
    # run the NiceGUI app
    ui.run(host='0.0.0.0', port=8080, favicon='📆', language='de-DE')

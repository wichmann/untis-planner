#!/usr/bin/env python3

"""
A NiceGUI app to plan appointments for multiple teachers using timetables
from WebUntis. It fetches the timetables of specified teachers and displays a
weekly overview highlighting busy slots.
"""

import configparser
from datetime import datetime, timedelta

from fastapi import Request
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


class Language:
    """
    A class to handle language selection and retrieval.

    Based on: https://github.com/zauberzeug/nicegui/discussions/5840
    """
    @property
    def current(self) -> str:
        """Gets the current language code from user storage, defaulting to 'en' if not set."""
        return app.storage.user.get('language', 'en')

    @current.setter
    def current(self, code: str) -> None:
        """Sets the current language code in user storage if it's a supported language."""
        if code in ('de', 'en'):
            app.storage.user['language'] = code

    def detect_from_request(self):
        """Detects the preferred language from the client's request headers and sets it accordingly."""
        if ui.context.client.request:
            for lang in ui.context.client.request.headers.get('accept-language', '').split(','):
                if lang[:2] in ('de', 'en'):
                    code = lang[:2]
                    break
            app.storage.user['language'] = code

    @property
    def is_de(self) -> bool:
        """Returns True if the current language is German ('de'), otherwise False."""
        return self.current == 'de'

    @property
    def is_en(self) -> bool:
        """Returns True if the current language is English ('en'), otherwise False."""
        return self.current == 'en'


LANGUAGE = Language()


def prepare_events():
    """Prepare calendar events based on the selected teachers and date range."""
    LESSON_CALENDAR.clear_events()
    for i, teacher in enumerate(app.storage.client['selected_teachers']):
        current_teacher = UNTIS_API.session.teachers().filter(surname=teacher)[0]
        timetable_entries = UNTIS_API.get_timetable(current_teacher, start=app.storage.client['start_date'],
                                     end=app.storage.client['end_date'])
        for lesson in timetable_entries:
            # filter out periods that aren't lessons
            if lesson.klassen and lesson.subjects[0].name != '---':
                add_event_for_lesson(teacher, lesson, TEACHER_COLORS[i % len(TEACHER_COLORS)])

def add_event_for_lesson(teacher, lesson, color):
    """
    Adds an event to the calendar for a given lesson, ensuring no duplicates
    for the same teacher and time slot.
    """
    try:
        for _ in lesson.teachers:
                        # remove existing event for the teacher in the same time slot to avoid duplicates
            LESSON_CALENDAR.remove_event(title=teacher, start=str(lesson.start), end=str(lesson.end))
                        # create new event for all periods of the teacher
            LESSON_CALENDAR.add_event(title=teacher, start=str(lesson.start), end=str(lesson.end),
                                      display='block', color=color,
                                      classes=', '.join(str(klasse) for klasse in lesson.klassen),
                                      subjects=', '.join(str(subject) for subject in lesson.subjects))
            if DEBUG:
                print(f'Added event: Teacher={teacher}, Start={lesson.start}, End={lesson.end}, '
                                  f'Classes={lesson.klassen}, Subjects={lesson.subjects}')
    except IndexError as e:
        if DEBUG:
            print(f'Error processing period: {e}')


def prepare_dropdown(teacher_list):
    """Gets last names for all teachers and prepares the dropdown."""
    teacher_names = [teacher.surname for teacher in teacher_list]
    ui.select(options=teacher_names, multiple=True, with_input=True, new_value_mode='add-unique',
              clearable=True, label='Select teachers:' if LANGUAGE.is_en else 'Lehrkraft auswählen:',
              on_change=handle_teacher_change)


def handle_teacher_change(event: events.GenericEventArguments):
    """
    Updates the list of selected teachers based on changes in the dropdown.
    Reverts the list to the previous value if more than 5 items are selected.
    """
    if len(event.value) > 5:
        event.sender.value = app.storage.client['selected_teachers']
        ui.notify('You can only select up to 5 teachers' if LANGUAGE.is_en
                  else 'Sie können nur bis zu 5 Lehrkräfte auswählen', color='warning')
    else:
        if DEBUG:
            added = set(event.value) - set(app.storage.client['selected_teachers'])
            removed = set(app.storage.client['selected_teachers']) - set(event.value)
            if added:
                ui.notify(f'Added: {", ".join(added)}' if LANGUAGE.is_en else f'Hinzugefügt: {", ".join(added)}')
            if removed:
                ui.notify(f'Removed: {", ".join(removed)}' if LANGUAGE.is_en else f'Entfernt: {", ".join(removed)}')
        app.storage.client['selected_teachers'] = event.value
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
                'endTime': '15:00',
            },
            'locale': LANGUAGE.current,
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
            ui.notify(f'Teacher: {title}, Class: {classes}, Subject: {subjects}' if LANGUAGE.is_en
                      else f'Lehrkraft: {title}, Klasse: {classes}, Fach: {subjects}')


def handle_change(event: events.GenericEventArguments):
    """Update the date range in storage when the calendar view changes and refresh events."""
    if 'info' in event.args:
        start_date = datetime.fromisoformat(event.args['info']['startStr']).date()
        end_date = datetime.fromisoformat(event.args['info']['endStr']).date()
        if DEBUG:
            print(f'Current view range: {start_date} - {end_date}' if LANGUAGE.is_en
                  else f'Aktuelle Ansicht: {start_date} - {end_date}')
        app.storage.client['start_date'] = start_date
        app.storage.client['end_date'] = end_date
        prepare_events()


@ui.refreshable
def prepare_legend():
    """Prepares a legend showing the selected teachers with their corresponding colors."""
    with ui.row().classes('justify-center gap-12 w-full'):
        for i, teacher_name in enumerate(app.storage.client['selected_teachers']):
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
            print(f"Authenticated user: {username_from_request}" if LANGUAGE.is_en
                  else f"Authentifizierter Benutzer: {username_from_request}")
        teacher_name = [teacher.surname for teacher in teacher_list
                        if str(teacher.surname).casefold() == str(username_from_request).casefold()]
        if teacher_name:
            app.storage.client['selected_teachers'].append(teacher_name[0])
            prepare_events()
            prepare_legend.refresh()
        return username_from_request
    return None


@ui.page('/')
def main():
    """Main function to set up the NiceGUI app, load configuration, and initialize components."""
    LANGUAGE.detect_from_request()
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
    app.storage.client['start_date'] = datetime.now().date() - timedelta(days=datetime.now().weekday())
    app.storage.client['end_date'] = app.storage.client['start_date'] + timedelta(days=6)
    app.storage.client['selected_teachers'] = []
    # build UI elements
    ui.html(f'<h1 style="font-size: 4em;">{APP_TITLE}</h1>')
    prepare_dropdown(teacher_list)
    prepare_calendar()
    prepare_legend()


if __name__ in {'__main__', '__mp_main__'}:
    # run the NiceGUI app
    ui.run(host='0.0.0.0', port=8080, favicon='📆', language='de-DE',
           storage_secret='uqu7geitaic7eawee2Ieyaoshatietioshai8aiya')

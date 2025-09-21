
"""
A Streamlit app to plan appointments for multiple teachers using timetables
from WebUntis. It fetches the timetables of specified teachers and displays a
weekly overview highlighting busy slots.
"""

import configparser
from datetime import datetime, timedelta

import streamlit as st
from streamlit_calendar import calendar as st_calendar

import untisplaner


APP_TITLE = 'UntisPlaner'


def prepare_sidebar(up, teacher_list):
    """
    Prepare the sidebar with configuration options: teacher selection and date range.
    """
    st.sidebar.title(APP_TITLE)
    st.sidebar.write('Termin-Planungstool für mehrere Lehrer mithilfe von Stundenplänen')
    st.sidebar.header('Konfiguration')
    # create a dropdown to select teachers
    st.sidebar.subheader('Lehrer auswählen')
    selected_teachers = st.sidebar.multiselect(
        label='Wählen Sie einen Lehrer aus...',
        options=[t.long_name for t in teacher_list],
        max_selections=5,
        accept_new_options=True,
    )
    # get dates for next week
    start_next_week = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
    end_next_week = start_next_week + timedelta(days=6)
    #
    # create input fields to select a specific date
    st.sidebar.subheader('Wählen Sie ein spezifisches Datum')
    start_date, end_date = up.get_dates_for_school_year()
    selected_date = st.sidebar.date_input(
        'Wählen Sie ein Datumsbereich aus:',
        value=(start_next_week.date(), end_next_week.date()),
        min_value=start_date,
        max_value=end_date
    )
    return selected_date, selected_teachers


def prepare_events(up, selected_teachers, selected_date):
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
    calendar_events = []
    if len(selected_date) < 2:
        return calendar_events
    for i, teacher in enumerate(selected_teachers):
        current_teacher = up.session.teachers().filter(surname=teacher)[0]
        tt = up.get_timetable(current_teacher, start=selected_date[0], end=selected_date[1])
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
                    calendar_events.append(event)
    return calendar_events


def prepare_calendar(up, selected_teachers, selected_date):
    """
    Prepare and display the calendar with events.
    """
    calendar_options = {
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
    }
    custom_css="""
        .fc-event-time {
            display: none;
        }
        .fc-event-title {
            font-weight: 800;
        }
    """
    calendar_events = prepare_events(up, selected_teachers, selected_date)
    calendar = st_calendar(
        events=calendar_events,
        options=calendar_options,
        custom_css=custom_css,
        key='calendar',
        )
    st.write(calendar)


def main():
    """
    Main function to run the Streamlit app.
    """
    about_text = 'Termin-Planungstool für mehrere Lehrer mithilfe von Stundenplänen'
    sources_info = """Ein einfacher Tool zur Planung von Terminen für mehrere
Lehrer mithilfe von Stundenplänen aus einem WebUntis-Server. Es ruft die
Stundenpläne der ausgewählten Lehrer ab und zeigt eine Wochenübersicht mit den
belegten Zeitfenstern an."""
    st.title(APP_TITLE)
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon='📅',
        layout='wide',
        initial_sidebar_state='expanded',
        menu_items={
            'About': f'# {APP_TITLE}\n{about_text}\n\n{sources_info}'
        }
    )
    # load configuration from file
    configfile = 'webuntis-config.ini'
    config = configparser.ConfigParser()
    config.read(configfile)
    cred = config['credentials']
    # create an UntisPlaner instance
    up = untisplaner.UntisPlaner(cred['user'], cred['password'], cred['server'], cred['school'])
    teacher_list = up.get_list_of_teachers()
    # build UI components and fill calendar with events
    selected_date, selected_teachers = prepare_sidebar(up, teacher_list)
    prepare_calendar(up, selected_teachers, selected_date)


if __name__ == "__main__":
    main()

# UntisPlaner - Simple appointment planer using timetables from a WebUntis server
A simple command line tool to plan appointments for multiple teachers using
timetables from WebUntis. It fetches the timetables of specified teachers and
displays a weekly overview highlighting busy slots.

## Build
Run app for development:

    pdm run streamlit run ./app.py

Build Docker container for development:

    docker build -t untisplaner .
    docker run -p 8501:8501 -d untisplaner

## Links
* https://github.com/im-perativa/streamlit-calendar/
* https://fullcalendar.io/demos
* https://docs.streamlit.io/develop/api-reference/widgets

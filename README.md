# UntisPlaner - Simple appointment planner using timetables from a WebUntis server
A simple command line tool and a NiceGUI app to plan appointments for multiple
teachers using timetables from WebUntis. It fetches the timetables of specified
teachers and displays a weekly overview highlighting busy slots.

## Build
Run app for development:

    pdm run python main.py

Build Docker container for development:

    docker build -t untisplanner .
    docker run -p 8080:8080 -d untisplanner

## Links
* https://github.com/zauberzeug/nicegui
* https://nicegui.io/documentation
* https://fullcalendar.io/demos
* https://github.com/python-webuntis/python-webuntis

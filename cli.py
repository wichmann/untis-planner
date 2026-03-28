#!/usr/bin/env python3

"""
A simple command line tool to plan appointments for multiple teachers using
timetables from WebUntis. It fetches the timetables of specified teachers and
displays a weekly overview highlighting busy slots.
"""

import locale
import logging
import readline
import configparser
from datetime import datetime, timedelta

from rich.console import Console
from rich.table import Table

import untisplanner


def choose_teachers(list_of_all_teachers):
    """
    Prompt user to input teacher names with auto-completion.
    """
    teacher_names = [t.long_name for t in list_of_all_teachers]
    teachers_to_plan = []

    # set up auto-completion for teacher names
    def completer(text, state):
        options = [i for i in teacher_names if i.casefold().startswith(text.casefold())]
        if state < len(options):
            return options[state]
        return None
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)

    while True:
        teacher = input('Input teacher name (leave empty to finish): ')
        if not teacher:
            break
        if teacher in teacher_names:
            teachers_to_plan.append(teacher)
        else:
            logging.info(f"Teacher '{teacher}' not found. Please try again.")
    return teachers_to_plan


def output_lessons(lessons: dict, start: datetime.date, end: datetime.date):
    """
    Display the lessons in a formatted table using rich.
    """
    # create two dimensional array with "days" as columns and "hours" as
    # rows beginning at index 1
    days = (end - start).days + 1
    timetable = [[[] for _ in range(10)] for _ in range(days)]
    for date, teachers in lessons.items():
        day = date.day - start.day - 1
        hour = match_time_to_lesson(date)
        # ignore all lessons outside of daytime school hours
        if hour:
            timetable[day][hour].extend(teachers)
    # colors in rich: https://rich.readthedocs.io/en/latest/appendix/colors.html
    table = Table(title='[bold bright_blue]Untis Planer[/bold bright_blue]',
                  show_lines=True, style="bright_white", header_style="bright_blue")
    for i in range(days):
        day_label = (start + timedelta(days=i)).strftime("%a %d.%m")
        table.add_column(day_label, justify="center", style="cyan", no_wrap=True)
    for hour in range(1, 10):
        row = []
        for day in range(days):
            if timetable[day][hour]:
                teachers = '\n'.join([t.long_name for t in timetable[day][hour]])
                if len(timetable[day][hour]) > 2:
                    row.append(f"[bright_red]{teachers}[/bright_red]")
                elif len(timetable[day][hour]) > 1:
                    row.append(f"[bright_yellow]{teachers}[/bright_yellow]")
                else:
                    row.append(f"[bright_green]{teachers}[/bright_green]")
            else:
                row.append("")
        table.add_row(*row)
    console = Console()
    console.print(table)


def match_time_to_lesson(date):
    """
    Match the time to its corresponding lesson slot. Returns 0 if the time does
    not match daytime school hours.
    """
    match date:
        case datetime(hour=8, minute=0):
            hour = 1
        case datetime(hour=8, minute=45):
            hour = 2
        case datetime(hour=9, minute=50):
            hour = 3
        case datetime(hour=10, minute=35):
            hour = 4
        case datetime(hour=11, minute=40):
            hour = 5
        case datetime(hour=12, minute=25):
            hour = 6
        case datetime(hour=13, minute=30):
            hour = 7
        case datetime(hour=14, minute=15):
            hour = 8
        case datetime(hour=15, minute=15):
            hour = 9
        case _:
            hour = 0
    return hour


def main():
    """Main function to read config and start the UntisPlaner."""
    locale.setlocale(locale.LC_ALL, '')
    logging.basicConfig(level=logging.INFO)
    logging.debug("Reading config file")
    configfile = 'webuntis-config.ini'
    config = configparser.ConfigParser()
    config.read(configfile)
    cred = config['credentials']
    up = untisplanner.UntisPlanner(cred['user'], cred['password'], cred['server'], cred['school'])
    start = datetime.fromisoformat('2026-04-04').date()
    end = start + timedelta(days=7)
    up.set_start_and_end(start, end)
    teachers_to_plan = choose_teachers(up.get_list_of_teachers())
    all_lessons = up.plan_week(teachers_to_plan)
    output_lessons(all_lessons, start, end)


if __name__ == "__main__":
    main()

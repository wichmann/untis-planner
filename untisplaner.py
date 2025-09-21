#!/usr/bin/env python3

"""
A simple command line tool to plan appointments for multiple teachers using
timetables from WebUntis. It fetches the timetables of specified teachers and
displays a weekly overview highlighting busy slots.
"""

import os
import locale
import logging
import datetime
import configparser
from collections import defaultdict
import readline

import webuntis
# Doc: https://python-webuntis.readthedocs.io/en/latest/objects.html
import webuntis.objects
from rich.console import Console
from rich.table import Table


class UntisPlaner:
    """
    A class to fetch and display timetables for multiple teachers from WebUntis.
    """
    def __init__(self, untis_user: str, untis_pass: str, server: str, school: str):
        self.session = webuntis.Session(
            username=untis_user,
            password=untis_pass,
            server=server,
            school=school,
            useragent="untisplaner")
        self.days = 5
        self.session.login()
        self.start = datetime.datetime.now()
        #self.start = self.start.replace(day=self.start.day, month=self.start.month)
        self.end = self.start + datetime.timedelta(days=self.days)

        teachers_to_plan = self.choose_teachers()
        self.plan_week(teachers_to_plan)

    def choose_teachers(self):
        """
        Prompt user to input teacher names with auto-completion.
        """
        list_of_all_teachers = self.session.teachers()
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
                print(f"Teacher '{teacher}' not found. Please try again.")
        return teachers_to_plan

    def plan_week(self, teachers_to_plan):
        """
        Fetch the timetables for the specified teachers and sort them by lesson
        date and time.
        """
        all_lessons  = defaultdict(list)
        for teacher in teachers_to_plan:
            current_teacher = self.session.teachers().filter(surname=teacher)[0]
            tt = self.get_timetable(current_teacher)
            l = self.extract_lessons(tt)
            for date in sorted(l.keys()):
                all_lessons[date].append(current_teacher)
        self.output_lessons(all_lessons)

    def get_timetable(self, teacher):
        """
        Fetch the timetable for a specific teacher within the defined date range.
        """
        current_year = self.session.schoolyears().current
        assert current_year.start <= self.start <= current_year.end, f"Start date not in current school year {self.start}"
        assert current_year.start <= self.end <= current_year.end, f"End date not in current school year {self.end}"
        logging.debug("creating time table between %s and %s", self.start, self.end)
        tt = self.session.timetable(start=self.start, end=self.end, teacher=teacher)
        return tt

    def extract_lessons(self, timetable: webuntis.objects.PeriodList):
        """
        Extract lessons from the timetable and organize them by start time.
        """
        tt = list(timetable)
        tt = sorted(tt, key=lambda x: x.start)
        # create dict with list as default value
        lessons = defaultdict(list)
        for po in tt:
            # filter out periods that aren't lessons
            if po.klassen:
                for t in po.teachers:
                    lessons[po.start].append(t)
                    # more fields in data: po.start, po.end, po.klassen, po.teachers, po.rooms, po.subjects, po.code
        return lessons

    def output_lessons(self, lessons: dict):
        """
        Display the lessons in a formatted table using rich.
        """
        # create two dimensional array with "days" as columns and "hours" as rows beginning at index 1
        timetable = [[[] for _ in range(10)] for _ in range(self.days)]
        for date, teachers in lessons.items():
            day = date.day - self.start.day - 1
            match date:
                case datetime.datetime(hour=8, minute=0):
                    hour = 1
                case datetime.datetime(hour=8, minute=45):
                    hour = 2
                case datetime.datetime(hour=9, minute=50):
                    hour = 3
                case datetime.datetime(hour=10, minute=35):
                    hour = 4
                case datetime.datetime(hour=11, minute=40):
                    hour = 5
                case datetime.datetime(hour=12, minute=25):
                    hour = 6
                case datetime.datetime(hour=13, minute=30):
                    hour = 7
                case datetime.datetime(hour=14, minute=15):
                    hour = 8
                case datetime.datetime(hour=15, minute=15):
                    hour = 9
                case _:
                    hour = 0
            # ignore all lessons outside of daytime school hours
            if hour:
                timetable[day][hour].extend(teachers)

        # colors in rich: https://rich.readthedocs.io/en/latest/appendix/colors.html#standard-colors
        table = Table(title='[bold bright_blue]Untis Planer[/bold bright_blue]', show_lines=True, style="bright_white", header_style="bright_blue")
        for i in range(self.days):
            day_label = (self.start + datetime.timedelta(days=i)).strftime("%a %d.%m")
            table.add_column(day_label, justify="center", style="cyan", no_wrap=True)
        for hour in range(1, 10):
            row = []
            for day in range(self.days):
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


def main():
    """
    Main function to read config and start the UntisPlaner.
    """
    locale.setlocale(locale.LC_ALL, '')
    logging.basicConfig(level=logging.INFO)
    logging.debug("Reading config file")
    configfile = os.path.expanduser('webuntis-config.ini')
    config = configparser.ConfigParser()
    config.read(configfile)
    cred = config['credentials']
    UntisPlaner(cred['user'], cred['password'], cred['server'], cred['school'])


if __name__ == "__main__":
    main()

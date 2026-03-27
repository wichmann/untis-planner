
"""
A library for fetching timetables for multiple teachers from WebUntis.
"""

import logging
import datetime
from collections import defaultdict

import webuntis
# Doc: https://python-webuntis.readthedocs.io/en/latest/objects.html
import webuntis.objects


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
        self.session.login()
        self.start = datetime.datetime.now().date()
        self.end = (datetime.datetime.now() + datetime.timedelta(days=7)).date()
        self.list_of_all_teachers = None
        self.current_school_year = None

    def set_start_and_end(self, start: datetime.date, end: datetime.date):
        """
        Set the start and end date for fetching timetables.
        """
        self.start = start
        self.end = end

    def get_dates_for_school_year(self):
        """
        Fetch and return the start and end dates of the current school year.
        """
        if self.current_school_year is None:
            self.current_school_year = self.session.schoolyears().current
        return self.current_school_year.start.date(), self.current_school_year.end.date()

    def get_list_of_teachers(self):
        """
        Fetch and return a list of all teachers from the WebUntis server.
        """
        if self.list_of_all_teachers is None:
            self.list_of_all_teachers = self.session.teachers()
        return self.list_of_all_teachers

    def plan_week(self, teachers_to_plan):
        """
        Fetch the timetables for the specified teachers and sort them by lesson
        date and time.
        """
        all_lessons  = defaultdict(list)
        for teacher in teachers_to_plan:
            current_teacher = self.session.teachers().filter(surname=teacher)[0]
            tt = self.get_timetable(current_teacher, start=self.start, end=self.end)
            l = self.extract_lessons(tt)
            for date in sorted(l.keys()):
                all_lessons[date].append(current_teacher)
        return all_lessons

    def get_timetable(self, teacher, start, end):
        """
        Fetch the timetable for a specific teacher within the defined date range.
        """
        # check if given dates are within the current school year
        start_date, end_date = self.get_dates_for_school_year()
        assert start_date <= start <= end_date, f"Start date not in current school year {start}"
        assert start_date <= end <= end_date, f"End date not in current school year {end}"
        # getting the timetable for the specified teacher and the given date range
        self.set_start_and_end(start, end)
        tt = self.session.timetable(start=start-datetime.timedelta(days=1), end=end, teacher=teacher)
        logging.debug(f"Fetched {len(tt)} periods for {teacher.long_name} from {start} to {end}")
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
            if po.klassen and po.subjects[0].name != '---':
                for t in po.teachers:
                    lessons[po.start].append(t)
                    # more fields in data:
                    # po.start, po.end, po.klassen, po.teachers, po.rooms, po.subjects, po.code
        return lessons

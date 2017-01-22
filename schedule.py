""" This module defines a class which represents calendar entries."""

from enum import Enum


class AppointmentState(Enum):
    RESERVABLE = 1
    RESERVED = 2
    NOT_RESERVABLE = 3
    OTHER = 4


class ScheduleEntry:
    """ This class represents a single calendar entry."""

    def __init__(self, name, classload, appointment_state,
                 program, date, start_time, end_time, coach):
        self.name = name
        self.classload = classload
        self.appointment_state = appointment_state
        self.program = program
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.coach = coach

    def __str__(self):
        class_descr = self.get_basic_description()
        state = "state: {}".format(
                AppointmentState(self.appointment_state).name)
        classload = "classload: {}, ".format(self.classload)
        coach = "coach: {}".format(self.coach)

        properties = state + classload + coach

        return class_descr + properties

    def get_basic_description(self):
        class_descr = "{} class on {} from {} to {}. ".format(
            self.program,
            self.date,
            self.start_time,
            self.end_time
            )
        return class_descr

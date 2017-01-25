""" This module defines a class which represents calendar entries."""

from enum import Enum
import calendar


class AppointmentState(Enum):
    RESERVABLE = 1
    RESERVED = 2
    EXPIRED = 3
    FULL = 4
    FUTURE = 5


class ScheduleEntry:
    """ This class represents a single calendar entry."""

    def __init__(self, name, classload, appointment_state,
                 program, date, start_time, end_time, coach):
        self.name = name
        self.classload = classload
        self.appointment_state = appointment_state
        self.program = program
        self.date = date
        self.weekday = calendar.day_name[date.weekday()]
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
        class_descr = "{} class on {}, {} from {} to {}. ".format(
            self.program,
            self.weekday,
            self.date,
            self.start_time,
            self.end_time
            )
        return class_descr

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.get_basic_description() == other.get_basic_description()

    def __ne__(self, other):
        return not self == other

    def update(self, other):
        assert self == other
        if (self.__str__() != other.__str__()):
            print("Found update for "+self.get_basic_description())
        if self.appointment_state != other.appointment_state:
            print("Appointment state: " +
                  AppointmentState(self.appointment_state).name +
                  " -> " +
                  AppointmentState(other.appointment_state).name)
            self.appointment_state = other.appointment_state
        if self.classload != other.classload:
            print("Classload: " + self.classload + " -> " + other.classload)
            self.classload = other.classload
        if self.coach != other.coach:
            print("Coach: " + self.coach + " -> " + other.coach)
            self.coach = other.coach

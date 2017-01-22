
class ScheduleEntry:
    def __init__(self, name, classload, can_make_appointment, can_cancel,
                 program, date, start_time, end_time, coach):
        self.name = name
        self.classload = classload
        self.can_make_appointment = can_make_appointment
        self.can_cancel = can_cancel
        self.program = program
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.coach = coach

    def __str__(self):
        class_descr = "{} class on {} from {] to {}. ".format(
                self.program,
                self.date,
                self.start_time,
                self.end_time
                )
        bookable = "bookable: {}, ".format(self.can_make_appointment)
        cancellable = "cancellable: {}, ".format(self.can_cancel)
        classload = "classload: {}, ".format(self.classload)
        coach = "coach: {}".format(self.coach)

        properties = bookable + cancellable + classload + coach

        return class_descr + properties

#!/usr/bin/env python3

import pickle
data = pickle.load(open("sched.p", "rb"))
for date in data:
    for app in data[date]:
        print(app.get_basic_description(), app.appointment_state)

#!/usr/bin/env python3

import pickle
from collections import defaultdict
a = defaultdict(list)
pickle.dump(a, open("sched.p", "wb"))

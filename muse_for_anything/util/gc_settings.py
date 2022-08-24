import gc
from time import time

from flask import Flask
from flask.globals import g

gc_stats = []


def gc_phase_information(phase, information):
    try:
        g._get_current_object()
        if "nr_of_gc_runs" not in g:
            g.nr_of_gc_runs = 1
        else:
            g.nr_of_gc_runs = 1 + g.nr_of_gc_runs
    except RuntimeError:
        pass


gc.callbacks.append(gc_phase_information)

gc.set_threshold(10000, 15, 10)

print("\n\nGC Thresholds:", gc.get_threshold(), "\n\n")


def before_request():
    g.nr_of_gc_runs = 0
    g.request_start_time = time()


def teardown(something):
    runs = (g.nr_of_gc_runs,)
    time_ = (time() - g.request_start_time,)
    gc_stats.append((runs, time_))
    print(
        "Nr. of GC runs:",
        runs,
        "Request duration:",
        time_,
    )
    if len(gc_stats) > 20:
        gc_stats.sort()
        print("#########################################")
        print(gc_stats[-5:])
        print("#########################################")
        gc_stats.clear()


def register_gc_handler(app: Flask):
    """Register the GC handler with the flask app."""
    app.before_request(before_request)
    app.teardown_request(teardown)

#!/usr/bin/env python

import time
import sqlite3
import os
import subprocess
import argparse
from taskw import TaskWarrior
import signal
import sys

home = os.environ['HOME']
table = home + '/.task/pomodoro/table.db'

long_break_time = 1500
short_break_time = 300
work_time = 1500

class GracefulInterruptHandler(object):

    def __init__(self, sig=signal.SIGINT):
        self.sig = sig

    def __enter__(self):

        self.interrupted = False
        self.released = False

        self.original_handler = signal.getsignal(self.sig)

        def handler(signum, frame):
            self.release()
            self.interrupted = True

        signal.signal(self.sig, handler)

        return self

    def __exit__(self, type, value, tb):
        self.release()

    def release(self):

        if self.released:
            return False

        signal.signal(self.sig, self.original_handler)

        self.released = True

        return True

def conn_decorator(function):
    def wrap_function(*args, **kwargs):
        try:
            conn = sqlite3.connect(table)
            function(conn, *args, **kwargs)
        finally:
            conn.close()
    return wrap_function

def await_user_input(function):
    def wrap_function(*args, **kwargs):
        subprocess.call(["say", "-v", "Cellos", "bom bom boom"])
        input("Press Enter to continue...")
        return function(*args, **kwargs)
    return wrap_function

def create_or_connect():
    if os.path.exists(table):
        conn = sqlite3.connect(table)
    else:
        conn = sqlite3.connect(table)
        c = conn.cursor()
        c.execute('''CREATE TABLE pomodoro_token 
                (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_started INTEGER,
                time_ended INTEGER,
                type TEXT)''')
        c.execute('''CREATE TABLE pomodoro_assigned_task
                (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pomodoro_token_id INTEGER,
                task_id TEXT, 
                FOREIGN KEY(pomodoro_token_id) REFERENCES pomodoro_token(id) 
                )''')
        conn.close()

def take_break(conn, break_time):
    print("Take break")
    t_start = time.time()
    time.sleep(short_break_time)
    print("-----")
    t_end = time.time()
    t = (t_start, t_end, 'break')
    c = conn.cursor()
    c.execute('INSERT INTO pomodoro_token (time_started, time_ended, type) VALUES (?,?,?)', t)
    # return the last row inserted into our data store
    return c.lastrowid

def do_work(conn, work_time):
    print("Do work")
    t_start = time.time()
    time.sleep(work_time)
    print("-----")
    t_end = time.time()
    t = (t_start, t_end, 'work')
    c = conn.cursor()
    c.execute('INSERT INTO pomodoro_token (time_started, time_ended, type) VALUES (?,?,?)', t)
    # return the last row inserted into our data store
    return c.lastrowid

def assign_token_to_task(conn, task_uuid, token_id):
    c = conn.cursor()
    t = (token_id, task_uuid)
    c.execute('INSERT INTO pomodoro_assigned_task (pomodoro_token_id, task_id) VALUES (?,?)', t)

@conn_decorator
@await_user_input
def take_short_break(conn, task_uuid=None):
    with GracefulInterruptHandler() as h:
        token_id = take_break(conn, short_break_time)
        assign_token_to_task(conn, task_uuid, token_id)
        if h.interrupted:
            conn.rollback()
            raise KeyboardInterrupt
        else:
            conn.commit()

@conn_decorator
@await_user_input
def take_long_break(conn, task_uuid=None):
    with GracefulInterruptHandler() as h:
        token_id = take_break(conn, long_break_time)
        assign_token_to_task(conn, task_uuid, token_id)
        if h.interrupted:
            conn.rollback()
            raise KeyboardInterrupt
        else:
            conn.commit()

@conn_decorator
@await_user_input
def do_task_work(conn, task_uuid):
    with GracefulInterruptHandler() as h:
        token_id = do_work(conn, work_time)
        assign_token_to_task(conn, task_uuid, token_id)
        if h.interrupted:
            conn.rollback()
            raise KeyboardInterrupt
        else:
            conn.commit()

def do_task_break(pomodoro_counter, task_uuid):
    if pomodoro_counter % 4 == 0:
        take_long_break(task_uuid=task_uuid)
    else:
        take_short_break(task_uuid=task_uuid)

def exit_gracefully():
    print("\n...wrapping up jobs and terminating.")

def main(args):
    w = TaskWarrior()
    try:
        create_or_connect()
        pomodoro_counter = args.pomodoro_counter
        task_id, task_body = w.get_task(id=args.taskw_id)
        print("Starting our pomodoro break period: %d on task: %s" % (pomodoro_counter, task_body['description']))
        task_uuid = task_body['uuid']
        subprocess.call(["task", str(task_id), "start"])
        while True:
            do_task_work(task_uuid)
            pomodoro_counter += 1
            do_task_break(pomodoro_counter, task_uuid)
    except KeyboardInterrupt:
        pass
    finally:
        exit_gracefully()
        subprocess.call(["task", str(task_id), "stop"])

def parse_options():
    parser = argparse.ArgumentParser(description='Add pomodoro support to taskwarrior.')
    parser.add_argument('--position', dest='pomodoro_counter', 
                    type=int, default=0,
                    help='start at pomodoro index, determines length of next break, 3 = long break')
    parser.add_argument('--workon', dest='taskw_id',
                    type=int, required=True,
                    help='start target id of task warrior task')

    return parser.parse_args()

if __name__ == "__main__":
    main(parse_options())

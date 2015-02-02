import time
import sqlite3
import os.path
import subprocess

table = '/Users/nickma/.task/pomodoro/table.db'

long_break_time = 1500
short_break_time = 300
work_time = 1500

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
        raw_input("Press Enter to continue...")
        return function(*args, **kwargs)
    return wrap_function

def create_or_connect():
    if os.path.exists(table):
        conn = sqlite3.connect(table)
    else:
        conn = sqlite3.connect(table)
        c = conn.cursor()
        c.execute('''CREATE TABLE pomodoro_work_token 
                (last_modified integer, time_started integer, time_worked integer)''')
        c.execute('''CREATE TABLE pomodoro_break_token 
                (last_modified integer, time_started integer, time_breaked integer)''')
        conn.close()

@conn_decorator
@await_user_input
def take_short_break(conn):
    print("Take break")
    t_start = time.time()
    time.sleep(short_break_time)
    print("-----")
    t_end = time.time()
    t = (t_end, t_start, short_break_time)
    c = conn.cursor()
    c.execute('INSERT INTO pomodoro_break_token VALUES (?,?,?)', t)

@conn_decorator
@await_user_input
def take_long_break(conn):
    print("Take break")
    t_start = time.time()
    time.sleep(long_break_time)
    print("-----")
    t_end = time.time()
    t = (t_end, t_start, long_break_time)
    c = conn.cursor()
    c.execute('INSERT INTO pomodoro_break_token VALUES (?,?,?)', t)

@conn_decorator
@await_user_input
def do_task(conn):
    print("Do work")
    t_start = time.time()
    time.sleep(work_time)
    print("-----")
    t_end = time.time()
    t = (t_end, t_start, work_time)
    c = conn.cursor()
    c.execute('INSERT INTO pomodoro_work_token VALUES (?,?,?)', t)

def main():
    create_or_connect()
    print("Starting our main task")
    pomodoro_counter = 0
    while True:
        do_task()
        pomodoro_counter += 1
        if pomodoro_counter % 4 == 0:
            take_long_break()
        else:
            take_short_break()

if __name__ == "__main__":
    main()

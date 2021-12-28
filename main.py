import asyncio
import asyncsched
import time
import threading
from typing import Callable

# loop = asyncio.get_event_loop()
log = print
scheduler = asyncsched.AsyncSchedule()
# sched 遇到的坑

class SchedPriorityTask:

    def __init__(self) -> None:
        pass

    # 生成一个定时任务
    def add_tasks_before_exec(self, task: Callable, times: int, interval: int, *args, **kwargs):
        # 按照指定的间隔, 任务持续调用 times 次
        # interval seconds
        start_time = 0
        def inner_task(*args, **kwargs):
            nonlocal start_time
            if start_time < times:
                scheduler.enter(interval, 1, inner_task, argument=args, kwargs=kwargs)
                print()
                print()
                log(f'---> caculating inner task {start_time}: {task.__name__, interval, args, kwargs} <-----')
                task(*args, **kwargs)
                start_time += 1
        log(f'adding inner task {task.__name__, interval, args, kwargs}')
        log(f'{scheduler=}')
        scheduler.enter(interval, 1, inner_task, argument=args, kwargs=kwargs)
    
    def run(self, taskid):
        print(f'start {threading.currentThread().ident}')
        print(f'task id {time.time(), taskid, threading.currentThread().ident}')
        print(f"....{scheduler}...{len(scheduler._queue)}")
        # time.sleep(1)
        print(f'-----> end task {threading.currentThread().ident}<---')
        print()
        print()


    def start_add_task(self, times, interval, taskid):
        self.add_tasks_before_exec(self.run, times, interval, taskid)

class SchedTask:

    def __init__(self) -> None:
        pass

    # 生成一个定时任务
    def add_tasks_before_exec(self, task: Callable, times: int, interval: int, *args, **kwargs):
        # 按照指定的间隔, 任务持续调用 times 次
        # interval seconds
        start_time = 0
        def inner_task(*args, **kwargs):
            nonlocal start_time
            if start_time < times:
                scheduler.enter(interval, inner_task, argument=args, kwargs=kwargs)
                print()
                print()
                log(f'---> caculating inner task {start_time}: {task.__name__, interval, args, kwargs} <-----')
                task(*args, **kwargs)
                start_time += 1
        log(f'adding inner task {task.__name__, interval, args, kwargs}')
        log(f'{scheduler=}')
        handler = scheduler.enter(interval, inner_task, argument=args, kwargs=kwargs)
        log(f'{handler=}')
    
    def run(self, taskid):
        print(f'start {threading.currentThread().ident}')
        print(f'task id {time.time(), taskid, threading.currentThread().ident}')
        print(f"....{scheduler}...{len(scheduler._queue)}")
        # time.sleep(1)
        print(f'-----> end task {threading.currentThread().ident}<---')
        print()
        print()


    def start_add_task(self, times, interval, taskid):
        self.add_tasks_before_exec(self.run, times, interval, taskid)


from fastapi import FastAPI

schedtask = SchedTask()
app = FastAPI()

@app.get('/api')
def api(times:int, taskid:str):
    schedtask.start_add_task(times=times, taskid=taskid, interval=5)
    return f'current {threading.currentThread().ident}'

@app.get('/task')
def tasks():
    time_f = lambda t : time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
    return {"data":[(time_f(e.time), str(e)) for e in scheduler.queue]}

# if __name__ == '__main__':
#     from daphne.server import Server
#     from daphne.endpoints import build_endpoint_description_strings
    
#     Server(application=app, endpoints=build_endpoint_description_strings('0.0.0.0', 5000)).run()


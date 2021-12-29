- ### sled

--------------

an `async scheduler` module, it was written in the 2021 christmas to pass the boring christmas ~.~

The sled module defines some class which implements a general purpose event scheduler.
some useful async schedule class that refer to the standard library `sched`.

AsyncPrioritySchedule use the same namedtuple and the same interface to the `sched`.
if u do not need the priority attribute. AsyncSchedule, PrefSchdule is perfer to use.

all of that needed to be used in async module which required to make sure event loop is running.

PrefSchdule, don't store the event.
AsyncSchedule, don't have the priority.
AsyncPrioritySchedule is almost the same to the sched, but just Coroutine, not the thread.

----------------------------------------------------------------------------------------------

参考标准库`sched`实现的一个基于协程的事件调度框架。  
可以用于执行一些定时任务。  
其中 AsyncPrioritySchedule 可以兼容 标准库`sched`模块。  
PrefSchdule, AsyncSchedule 拥有比标准库更易用的定时任务函数. timer 和 ticker。  
但是两者都有一定的限制,不支持自定义的时间函数。  
性能首选 PrefSchdule。  
不需要优先级，但是需要查看积累的任务，选用 AsyncSchedule。  
需要在异步编程环境下，替换 sched 选用 AsyncPrioritySchedule。  

-----------
#### intall
 
 >pip install sled

-------------
##### usage

``` python
    import time
    import asyncio

    from sled import AsyncPrioritySchedule, AsyncSchedule, PrefSchedule

    def func(s):
        print(s, time.time())
        
    async def afunc(s):
        print(s, time.time())

    # using AsyncPrioritySchedule
    schedule = AsyncPrioritySchedule()
    schedule.enter(3, 1, func, argument=('test enter',)) # run a task in laster 3 seconds, priority 1.
    schedule.enterabs(time.time()+3, 1, afunc('test enterabs async',))

    # using AsyncSchedule
    asyncSchedule = AsyncSchedule()
    asyncSchedule.timer(3, afunc('test async timer'))
    asyncSchedule.ticker(1, 3, afunc, argument=('test Asyncschedule',)) # interval is 1, times is 3

    # using PrefSchedule
    perfSchedule = PrefSchedule()
    perfSchedule.ticker(2, 3, afunc, argument=('test PrefSchedule',))

    # make sure loop is running in ur code
    loop = asyncio.get_event_loop()
    loop.run_forever()


```



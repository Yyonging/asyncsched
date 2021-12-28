The asyncscheduler module defines some class which implements a general purpose event scheduler.
some useful async schedule class that refer to the standard library `sched`.
AsyncPrioritySchedule use the same namedtuple and the same interface to the `sched`.
if u do not need the priority attribute. AsyncSchedule, PrefSchdule is perfer to use.
all of that needed to be used in async module which required to using event loop.
PrefSchdule, don't have queue to store the event.
AsyncSchedule, don't have the priority.
AsyncPrioritySchedule is almost the same to the sched, but just Coroutine, not the thread.
----------------------------------------------------------------------------------------------

参考标准库sched实现的一个基于协程的时间调度框架。
可以用于执行一些定时任务。
其中 AsyncPrioritySchedule 可以兼容 标准库sched模块。
PrefSchdule, AsyncSchedule 拥有比标准库更易用的定时任务函数. timer 和 ticker。
但是两者都有一定的限制,不支持自定义的时间函数。
性能首选 PrefSchdule。
不需要优先级，但是需要查看积累的任务，选用 AsyncSchedule。
需要在异步编程环境下，替换 sched 选用 AsyncPrioritySchedule。


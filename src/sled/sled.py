"""some useful async schedule for replace the standard library `sched`
AsyncPrioritySchedule use the same namedtuple and interface to the sched.
if u do not need the priority, AsyncSchedule is perfer to use.
"""
import asyncio
from asyncio.events import TimerHandle
import heapq
from collections import namedtuple
from itertools import count
from time import time as _time
from typing import Callable, Coroutine, Union, List

__all__ = ["AsyncPriorityScheduler", "AsyncScheduler", "PerfScheduler"]

Event = namedtuple('Event', 'time, priority, sequence, action, argument, kwargs')
Event.time.__doc__ = ('''Numeric type compatible with the return value of the
timefunc function passed to the constructor.''')
Event.priority.__doc__ = ('''Events scheduled for the same time will be executed
in the order of their priority.''')
Event.sequence.__doc__ = ('''A continually increasing sequence number that
    separates events if time and priority are equal.''')
Event.action.__doc__ = ('''Executing the event means executing
action(*argument, **kwargs)''')
Event.argument.__doc__ = ('''argument is a sequence holding the positional
arguments for the action.''')
Event.kwargs.__doc__ = ('''kwargs is a dictionary holding the keyword
arguments for the action.''')

_sentinel = object()


class AsyncScheduler:

    def __init__(self, loop=None):
        self._queue = []
        self.timefunc = _time
        self.delayfunc = asyncio.sleep
        self._sequence_generator = count()
        if not loop:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.__is_stop = False

    def enterabs(self, time: Union[int, float], action: Union[Callable, Coroutine],
                    argument: tuple=(), kwargs: dict=_sentinel) -> Event:
        if kwargs is _sentinel:
            kwargs = {}
        event = Event(time, None, next(self._sequence_generator),
                            action, argument, kwargs)
        at_time = time - self.timefunc() + self.loop.time()
        heapq.heappush(self._queue, event)
        action = AsyncScheduler.toc(action, *argument, **kwargs)
        def wrapper_action():
            try:
                if not self.__is_stop:
                    self._queue.remove(event)
                    self.loop.create_task(action)
            except ValueError:
                ...
        self.loop.call_at(at_time, wrapper_action)
        return event

    def enter(self, delay: Union[int, float], action: Union[Callable, Coroutine],
                    argument: tuple=(), kwargs: dict=_sentinel) -> Event:
        """A variant that specifies the time as a relative time.

        This is actually the more commonly used interface.

        """
        time = self.timefunc() + delay
        return self.enterabs(time, action, argument, kwargs)

    def cancel(self, event: Event):
        """Remove an event from the queue.

        This must be presented the ID as returned by enter().
        If the event is not in the queue, this raises ValueError.

        """
        self._queue.remove(event)
        heapq.heapify(self._queue)

    def clear(self):
        ''' Remove all the event from the queue
        '''
        self._queue.clear()

    def empty(self):
        """Check whether the queue is empty."""
        return not self._queue

    @property
    def queue(self):
        """An ordered list of upcoming events.

        Events are named tuples with fields for:
            time, priority, action, arguments, kwargs

        """
        # Use heapq to sort the queue rather than using 'sorted(self._queue)'.
        # With heapq, two events scheduled at the same time will show in
        # the actual order they would be retrieved.
        events = self._queue[:]
        return list(map(heapq.heappop, [events]*len(events)))

    def ticker(self, interval: Union[int, float], times: int, func: Callable,
                    argument: tuple=(), kwargs: dict=_sentinel, run_forever: bool=False):
        if kwargs is _sentinel:
            kwargs = {}
        i = 2
        if not run_forever:
            times = i + times
        start_time = self.timefunc()
        async def wrapper_action(func, *args, **kwargs):
            nonlocal i, start_time
            if not run_forever and i < times:
                self.enterabs(start_time+(i*interval), action=wrapper_action(func, *args, **kwargs))
                await AsyncScheduler.toc(func, *args, **kwargs)
                i += 1
            elif run_forever:
                self.enterabs(start_time+(i*interval), action=wrapper_action(func, *args, **kwargs))
                await AsyncScheduler.toc(func, *args, **kwargs)
                if i > 4294967294: # reset
                    start_time += i * interval
                    i = 0
                i += 1
        return self.enterabs(start_time+interval, action=wrapper_action(func, *argument, **kwargs))

    def timer(self, time: Union[int, float], action: Union[Callable, Coroutine], argument: tuple=(), kwargs:dict =_sentinel):
        return self.enterabs(time, action, argument=argument, kwargs=kwargs)

    def stop(self) -> bool:
        ''' stop the ticker
        '''
        self.__is_stop = True
        return self.__is_stop

    @staticmethod
    def toc(action: Callable, *args, **kwargs) -> Coroutine:
        if asyncio.iscoroutinefunction(action):
            action = action(*args, **kwargs)
        elif not asyncio.iscoroutine(action):
            action = asyncio.to_thread(action, *args, **kwargs)
        return action

class AsyncPriorityScheduler:

    def __init__(self, timefunc=_time, delayfunc=asyncio.sleep, loop=None):
        """Initialize a new instance, passing the time and delay
        functions"""
        self._queue = []
        self.timefunc = timefunc
        self.delayfunc = delayfunc
        self._sequence_generator = count()
        if not loop:
            loop = asyncio.get_event_loop()
        self.loop = loop

    def enterabs(self, time: Union[int, float], priority: int=0,
                action: Union[Callable, Coroutine]=None, argument: tuple=(),
                    kwargs: dict=_sentinel) -> Event:
        if kwargs is _sentinel:
            kwargs = {}
        event = Event(time, priority, next(self._sequence_generator), action, argument, kwargs)
        heapq.heappush(self._queue, event)
        async def inner():
            q = self._queue
            delayfunc = self.delayfunc
            timefunc = self.timefunc
            pop = heapq.heappop
            while True:
                if not q:
                    break 
                time, _, _, action, argument, kwargs = q[0]
                now = timefunc()
                if time > now:
                    delay = True
                else:
                    delay = False
                    pop(q)
                if delay:
                    await delayfunc(time - now)
                else:
                    action = AsyncScheduler.toc(action, *argument, **kwargs)
                    await action
        self.loop.create_task(inner())
        return event

    def enter(self, delay: Union[int, float], priority: int=0, action: Union[Callable, Coroutine]=None,
                argument: tuple=(), kwargs: dict=_sentinel) -> Event:
        """A variant that specifies the time as a relative time.

        This is actually the more commonly used interface.

        """
        time = self.timefunc() + delay
        return self.enterabs(time, priority, action, argument, kwargs)

    def cancel(self, event: Event):
        """Remove an event from the queue.

        This must be presented the ID as returned by enter().
        If the event is not in the queue, this raises ValueError.

        """
        self._queue.remove(event)
        heapq.heapify(self._queue)

    def empty(self) -> bool:
        """Check whether the queue is empty."""
        return not self._queue

    @property
    def queue(self) -> List[Event]:
        """An ordered list of upcoming events.
 
        Events are named tuples with fields for:
            time, priority, action, arguments, kwargs

        """
        # Use heapq to sort the queue rather than using 'sorted(self._queue)'.
        # With heapq, two events scheduled at the same time will show in
        # the actual order they would be retrieved.
        events = self._queue[:]
        return list(map(heapq.heappop, [events]*len(events)))

class PerfScheduler:
    def __init__(self, loop=None):
        self.timefunc = _time
        self.delayfunc = asyncio.sleep
        if not loop:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.__is_stop = False

    def ticker(self, interval: Union[int, float], times: Union[int, float],
                func: Union[Callable, Coroutine], argument: tuple=(), kwargs: dict=_sentinel,
                    run_forever: bool=False):
        if kwargs is _sentinel:
            kwargs = {}
        i = 2
        times = i + times
        loop = self.loop
        start_time = self.timefunc()
        async def wrapper_action(func, *args, **kwargs):
            nonlocal i, start_time
            if not run_forever and i < times and not self.__is_stop:
                self.enterabs(start_time+(i*interval), action=wrapper_action(func, *args, **kwargs))
                loop.create_task(AsyncScheduler.toc(func, *args, **kwargs))
                i += 1
            elif run_forever and not self.__is_stop:
                self.enterabs(start_time+(i*interval), action=wrapper_action(func, *args, **kwargs))
                loop.create_task(AsyncScheduler.toc(func, *args, **kwargs))
                if i > 4294967294: # reset
                    start_time += i * interval
                    i = 0
                i += 1
        return self.enterabs(start_time+interval, action=wrapper_action(func, *argument, **kwargs))

    def timer(self, time: Union[int, float], action: Callable,
                argument: tuple=(), kwargs: dict=_sentinel) -> TimerHandle:
        return self.enterabs(time, action, argument=argument, kwargs=kwargs)

    def enterabs(self, time: Union[int, float], action: Union[Callable, Coroutine],
                    argument: tuple=(), kwargs: dict=_sentinel) -> TimerHandle:
        if kwargs is _sentinel:
            kwargs = {}
        at_time = time - self.timefunc() + self.loop.time()
        if self.__is_stop:
            return 
        wrapper_action = lambda : self.loop.create_task(AsyncScheduler.toc(action, *argument, **kwargs))
        return self.loop.call_at(at_time, wrapper_action)

    def enter(self, delay: Union[int, float], action: Union[Callable, Coroutine],
                argument: tuple=(), kwargs: dict=_sentinel):
        time = self.timefunc() + delay
        return self.enterabs(time, action, argument, kwargs)

    def stop(self) -> bool:
        ''' stop the ticker
        '''
        self.__is_stop = True
        return self.__is_stop

if __name__ == '__main__':

    asyncScheduler = AsyncScheduler()

    rv = []
    def test():
        print('s')
        rv.append('s')

    event = asyncScheduler.enter(3, test)

    print(event)
    loop = asyncio.get_event_loop()
    loop.run_forever()


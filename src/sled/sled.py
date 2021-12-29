"""some useful async schedule for replace the standard library `sched`
AsyncPrioritySchedule use the same namedtuple and interface to the sched.
if u do not need the priority, AsyncSchedule is perfer to use.
"""
import asyncio
import heapq
from collections import namedtuple
from itertools import count
from time import time as _time
from typing import Coroutine

__all__ = ["AsyncPrioritySchedule", "AsyncSchedule", "PrefSchedule"]

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


class AsyncSchedule:

    def __init__(self, loop=None):
        self._queue = []
        self.timefunc = _time
        self.delayfunc = asyncio.sleep
        self._sequence_generator = count()
        if not loop:
            loop = asyncio.get_event_loop()
        self.loop = loop

    def enterabs(self, time, action, argument=(), kwargs=_sentinel):
        if kwargs is _sentinel:
            kwargs = {}
        event = Event(time, None, next(self._sequence_generator),
                            action, argument, kwargs)
        at_time = time - self.timefunc() + self.loop.time()
        heapq.heappush(self._queue, event)
        action = AsyncSchedule.toc(action, *argument, **kwargs)
        def wrapper_action():
            try:
                self._queue.remove(event)
                self.loop.create_task(action)
            except ValueError:
                ...
        return self.loop.call_at(at_time, wrapper_action)

    def enter(self, delay, action, argument=(), kwargs=_sentinel):
        """A variant that specifies the time as a relative time.

        This is actually the more commonly used interface.

        """
        time = self.timefunc() + delay
        return self.enterabs(time, action, argument, kwargs)

    def cancel(self, event):
        """Remove an event from the queue.

        This must be presented the ID as returned by enter().
        If the event is not in the queue, this raises ValueError.

        """
        self._queue.remove(event)
        heapq.heapify(self._queue)

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

    def ticker(self, interval, times, func, argument=(), kwargs=_sentinel, run_forver=False):
        if kwargs is _sentinel:
            kwargs = {}
        i = 2
        times = i + times
        start_time = self.timefunc()
        async def wrapper_action(func, *args, **kwargs):
            nonlocal i
            if not run_forver and i < times:
                self.enterabs(start_time+(i*interval), action=wrapper_action(func, *args, **kwargs))
                await AsyncSchedule.toc(func, *args, **kwargs)
                i += 1
            elif run_forver:
                self.enterabs(start_time+(i*interval), action=wrapper_action(func, *args, **kwargs))
                await AsyncSchedule.ftoc(func, *args, **kwargs)
        return self.enterabs(start_time+interval, action=wrapper_action(func, *argument, **kwargs))

    def timer(self, time, action, argument=(), kwargs=_sentinel):
        return self.enterabs(time, action, argument=argument, kwargs=kwargs)

    @staticmethod
    def ftoc(func, *args, **kwargs) -> Coroutine:
        return asyncio.to_thread(func, *args, **kwargs)

    @staticmethod
    def toc(action, *args, **kwargs) -> Coroutine:
        if asyncio.iscoroutinefunction(action):
            action = action(*args, **kwargs)
        elif not asyncio.iscoroutine(action):
            action = AsyncSchedule.ftoc(action, *args, **kwargs)
        return action

class AsyncPrioritySchedule:

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

    def enterabs(self, time, priority=None, action=None, argument=(), kwargs=_sentinel):
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
                    action = AsyncSchedule.toc(action, *argument, **kwargs)
                    await action
        return self.loop.create_task(inner())

    def enter(self, delay, priority=0, action=None, argument=(), kwargs=_sentinel):
        """A variant that specifies the time as a relative time.

        This is actually the more commonly used interface.

        """
        time = self.timefunc() + delay
        return self.enterabs(time, priority, action, argument, kwargs)

    def cancel(self, event):
        """Remove an event from the queue.

        This must be presented the ID as returned by enter().
        If the event is not in the queue, this raises ValueError.

        """
        self._queue.remove(event)
        heapq.heapify(self._queue)

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

class PrefSchedule:
    def __init__(self, loop=None):
        self.timefunc = _time
        self.delayfunc = asyncio.sleep
        if not loop:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.__is_stop = False

    def ticker(self, interval, times, func, argument=(), kwargs=_sentinel, run_forver=False):
        if kwargs is _sentinel:
            kwargs = {}
        i = 2
        times = i + times
        loop = self.loop
        start_time = self.timefunc()
        async def wrapper_action(func, *args, **kwargs):
            nonlocal i
            if not run_forver and i < times:
                self.enterabs(start_time+(i*interval), action=wrapper_action(func, *args, **kwargs))
                loop.create_task(AsyncSchedule.toc(func, *args, **kwargs))
                i += 1
            elif run_forver:
                self.enterabs(start_time+(i*interval), action=wrapper_action(func, *args, **kwargs))
                loop.create_task(AsyncSchedule.toc(func, *args, **kwargs))
        return self.enterabs(start_time+interval, action=wrapper_action(func, *argument, **kwargs))

    def timer(self, time, action, argument=(), kwargs=_sentinel):
        return self.enterabs(time, action, argument=argument, kwargs=kwargs)

    def enterabs(self, time, action, argument=(), kwargs=_sentinel):
        if kwargs is _sentinel:
            kwargs = {}
        at_time = time - self.timefunc() + self.loop.time()
        if self.__is_stop:
            return 
        wrapper_action = lambda : self.loop.create_task(AsyncSchedule.toc(action, *argument, **kwargs))
        return self.loop.call_at(at_time, wrapper_action)

    def enter(self, delay, action, argument=(), kwargs=_sentinel):
        time = self.timefunc() + delay
        return self.enterabs(time, action, argument, kwargs)

    def cancel(self):
        self.__is_stop = True
        return self.__is_stop

import asyncio
import sys
sys.path.append('.')
from asyncsched import AsyncPrioritySchedule, AsyncSchedule

import pytest
import asyncio
import time

# import logging
# log = logging.getLogger(__name__).debug
# print = log

@pytest.fixture()
def asyncSchedule():
    return AsyncSchedule()

@pytest.fixture()
def asyncPrioritySchedule():
    return AsyncPrioritySchedule()

param_schdule = pytest.mark.parametrize('schedule',
                      [pytest.lazy_fixture('asyncSchedule'),
                       pytest.lazy_fixture('asyncPrioritySchedule')])

@pytest.fixture()
def loop():
    print('start')
    loop = asyncio.get_event_loop()
    yield loop
    print('closing')
    loop.close

@param_schdule
def test_enter(schedule, loop):
    rv = []
    func = lambda s: rv.append(s)
    priority = 1
    delay = 3
    if isinstance(schedule, AsyncPrioritySchedule):
        start_time = time.time()
        task = schedule.enter(delay, priority, func, ('test',))
        assert len(schedule._queue) == 1
        loop.run_until_complete(task)
        spend_time = time.time() - start_time
        assert delay-0.001 < spend_time < delay + 0.02  # assert 0.01 > time.time() - start_time raise error why?
        assert len(schedule._queue) == 0
        assert rv[0] == 'test'
    else: 
        handler = schedule.enter(delay, func, ('test',))
        assert len(schedule._queue) == 1
        call_at = handler.when()
        now = loop.time()
        assert  now-0.001 < call_at < now+delay+0.02
        loop.run_until_complete(asyncio.sleep(delay+1))
        assert len(schedule._queue) == 0
        assert rv[0] == 'test'

@param_schdule
def test_enterabs(schedule, loop):
    rv = []
    func = lambda s: rv.append(s)
    priority = 1
    delay = 3
    if isinstance(schedule, AsyncPrioritySchedule):
        schedule.enterabs(time.time()+delay, priority, func, ('test',))
        assert schedule._queue[0].priority == priority
    else:
        schedule.enterabs(time.time()+delay, func, ('test',))
    assert len(schedule._queue) == 1
    assert schedule._queue[0].action == func
    loop.run_until_complete(asyncio.sleep(delay+1))
    assert len(schedule._queue) == 0
    assert rv[0] == 'test'

@pytest.mark.ticker
def test_ticker(asyncSchedule, loop):
    rv = []
    interval = 1
    times = 3
    async def func(s):
        rv.append(s)
    asyncSchedule.ticker(interval, times, func, argument=('test',))
    loop.run_until_complete(asyncio.sleep(1))
    assert len(rv) == 1
    loop.run_until_complete(asyncio.sleep(1))
    assert len(rv) == 2
    loop.run_until_complete(asyncio.sleep(1))
    assert len(rv) == 3
    assert 'test' == rv[0]

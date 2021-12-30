import time
import pytest
import asyncio

from sled import AsyncPriorityScheduler, AsyncScheduler, PerfScheduler

@pytest.fixture()
def asyncScheduler():
    return AsyncScheduler()

@pytest.fixture()
def asyncPriorityScheduler():
    return AsyncPriorityScheduler()

@pytest.fixture()
def perfSchedule():
    return PerfScheduler()

param_schdule = pytest.mark.parametrize('schedule',
                      [pytest.lazy_fixture('asyncScheduler'),
                       pytest.lazy_fixture('asyncPriorityScheduler')])


allow_time_delta = 0.05

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
    if isinstance(schedule, AsyncPriorityScheduler):
        start_time = time.time()
        task = schedule.enter(delay, priority, func, ('test',))
        assert len(schedule._queue) == 1
        loop.run_until_complete(task)
        spend_time = time.time() - start_time
        assert delay-allow_time_delta < spend_time < delay + allow_time_delta
        assert len(schedule._queue) == 0
        assert rv[0] == 'test'
    else: 
        handler = schedule.enter(delay, func, ('test',))
        assert len(schedule._queue) == 1
        call_at = handler.when()
        now = loop.time()
        assert  now-allow_time_delta < call_at < now+delay+allow_time_delta
        loop.run_until_complete(asyncio.sleep(delay+1))
        assert len(schedule._queue) == 0
        assert rv[0] == 'test'

@pytest.mark.pri
def test_priority_enterabs_func_async(asyncPriorityScheduler, loop):
    rv = []
    func = lambda s: rv.append(s)
    async def afunc(s):
        rv.append(s)
    priority = 1
    delay = 3
    start_time = time.time()
    asyncPriorityScheduler.enterabs(start_time+delay, priority, func, ('test',))
    assert asyncPriorityScheduler.empty() is False
    asyncPriorityScheduler.enter(start_time+delay, priority+1, afunc('test async'))
    loop.run_until_complete(asyncio.sleep(delay+allow_time_delta))
    assert rv[-1] == 'test'

@param_schdule
def test_enterabs_corountine(schedule, loop):
    rv = []
    async def func(s):
        rv.append(s)
    priority = 1
    delay = 3
    start_time = time.time()
    if isinstance(schedule, AsyncPriorityScheduler):
        task = schedule.enterabs(start_time+delay, priority, func('test'))
        assert len(schedule._queue) == 1
        loop.run_until_complete(task)
        spend_time = time.time() - start_time
        assert delay-allow_time_delta < spend_time < delay + allow_time_delta
        assert len(schedule._queue) == 0
        assert rv[0] == 'test'
    else: 
        handler = schedule.enterabs(start_time+delay, func('test'))
        assert len(schedule._queue) == 1
        call_at = handler.when()
        now = loop.time()
        assert  now-allow_time_delta < call_at < now+delay+allow_time_delta
        loop.run_until_complete(asyncio.sleep(delay+1))
        assert len(schedule._queue) == 0
        assert rv[0] == 'test'


@param_schdule
def test_enterabs(schedule, loop):
    rv = []
    func = lambda s: rv.append(s)
    priority = 1
    delay = 3
    if isinstance(schedule, AsyncPriorityScheduler):
        schedule.enterabs(time.time()+delay, priority, func, ('test',))
        assert schedule._queue[0].priority == priority
    else:
        schedule.enterabs(time.time()+delay, func, ('test',))
    assert len(schedule._queue) == 1
    assert schedule._queue[0].action == func
    loop.run_until_complete(asyncio.sleep(delay+allow_time_delta))
    assert len(schedule._queue) == 0
    assert rv[0] == 'test'

@pytest.mark.ticker
def test_ticker(asyncScheduler, loop):
    rv = []
    interval = 1
    times = 3
    async def func(s):
        rv.append(s)
    asyncScheduler.ticker(interval, times, func, argument=('test',))
    loop.run_until_complete(asyncio.sleep(interval+allow_time_delta))
    assert len(rv) == 1
    loop.run_until_complete(asyncio.sleep(interval))
    assert len(rv) == 2
    loop.run_until_complete(asyncio.sleep(interval))
    assert len(rv) == 3
    assert 'test' == rv[0]

@pytest.mark.perf
def test_perf_enter(perfSchedule, loop):
    rv = []
    func = lambda s: rv.append(s)
    delay = 1
    perfSchedule.enter(delay, func, ('test',))
    loop.run_until_complete(asyncio.sleep(delay+allow_time_delta))
    assert len(rv) == 1
    assert 'test' == rv[0]

@pytest.mark.perf
def test_perf_enter_async(perfSchedule, loop):
    rv = []
    async def func(s):
        rv.append(s)
    delay = 1
    perfSchedule.enter(delay, func, ('test',))
    loop.run_until_complete(asyncio.sleep(delay+allow_time_delta))
    assert len(rv) == 1
    assert 'test' == rv[0]

@pytest.mark.perf
def test_perf_ticker(perfSchedule, loop):
    rv = []
    def func(s):
        rv.append(s)
    interval = 0.5
    times = 3
    perfSchedule.ticker(interval, times, func, argument=('test',))
    loop.run_until_complete(asyncio.sleep(interval+allow_time_delta))
    assert len(rv) == 1
    loop.run_until_complete(asyncio.sleep(interval))
    assert len(rv) == 2
    loop.run_until_complete(asyncio.sleep(interval))
    assert len(rv) == 3
    assert 'test' == rv[-1]
    loop.run_until_complete(asyncio.sleep(interval*3))
    assert len(rv) == 3

@pytest.mark.perf
def test_perf_ticker_async(perfSchedule, loop):
    rv = []
    async def func(s):
        rv.append(s)
    interval = 0.5
    times = 3
    perfSchedule.ticker(interval, times, func, argument=('test',))
    loop.run_until_complete(asyncio.sleep(interval+allow_time_delta))
    assert len(rv) == 1
    loop.run_until_complete(asyncio.sleep(interval))
    assert len(rv) == 2
    loop.run_until_complete(asyncio.sleep(interval))
    assert len(rv) == 3
    assert 'test' == rv[0]
    loop.run_until_complete(asyncio.sleep(interval*3))
    assert len(rv) == 3

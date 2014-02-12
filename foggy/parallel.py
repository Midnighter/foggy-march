# -*- coding: utf-8 -*-


"""
=================================
Parallel Random Walks on Networks
=================================

:Author:
    Moritz Emanuel Beber
:Date:
    2014-02-12
:Copyright:
    Copyright |c| 2014, Jacobs University Bremen gGmbH, all rights reserved.
:File:
    parallel.py

.. |c| unicode:: U+A9
"""


__all__ = ["uniform_random_walker", "directed_random_walker", "march",
        "iterative_march", "deletory_march", "buffered_march"]
#        "limited_uniform_random_walker",


import sys

import numpy

from IPython.parallel import interactive, require, LoadBalancedView

from .visits import ConstantValue


@require(numpy)
@interactive
def uniform_random_walker(node):
    """
    Perform a single random walk on a network with a uniform probability of a
    next step.

    Parameters
    ----------
    node: int
        Source node's index from where to start the random walk.

    Returns
    -------
    list: All nodes visited on the random walk.
    """
    # accessing globals `probabilities`, `neighbours`, and `steps that were pushed before
    local_probs = probabilities
    local_nbrs = neighbours
    smpl = numpy.random.random_sample
    choose = numpy.searchsorted
    path = [node]
    for s in xrange(steps):
        nbrs = local_nbrs[node]
        if len(nbrs) == 0:
            break
        draw = smpl()
        # the nbrs list and probs list correspond to each other
        # we use a binary search to find the index to the left of the
        # probability and take that node
        node = nbrs[choose(local_probs[node], draw)]
        path.append(node)
    return path

#@require(numpy, bisect)
#@interactive
#def limited_uniform_random_walker(node, max_steps=None):
#    """
#    Perform a single random walk on a network with a uniform probability of a
#    next step.
#
#    Parameters
#    ----------
#    """
#    # accessing globals `probabilities`, `neighbours`, and `steps` that were pushed before
#    local_probs = probabilities
#    local_nbrs = neighbours
#    if max_steps is None:
#        max_steps = steps
#    smpl = numpy.random.random_sample
#    choose = bisect.bisect_left
#    path = [node]
#    for s in xrange(max_steps):
#        nbrs = local_nbrs[node]
#        if len(nbrs) == 0:
#            break
#        draw = smpl()
#        # the nbrs list and probs list correspond to each other
#        # we use a binary search to find the index to the left of the
#        # probability and take that node
#        node = nbrs[choose(local_probs[node], draw)]
#        path.append(node)
#    return path

@require(numpy)
@interactive
def directed_random_walker(node):
    """
    Perform a single directed random walk on a network with a uniform probability of a
    next step.

    Parameters
    ----------
    node: int
        Source node's index from where to start the random walk.

    Returns
    -------
    list: All nodes visited on the random walk.
    """
    # accessing globals `probabilities`, `neighbours`, and `steps that were pushed before
    local_probs = probabilities
    local_nbrs = neighbours
    sample = numpy.random.random_sample
    choose = numpy.random.randint
    path = [node]
    for s in xrange(steps):
        nbrs = local_nbrs[node]
        if len(nbrs) == 0:
            break
        nbr_index = choose(len(nbrs))
        prob = local_probs[node][nbr_index]
        if prob == 1.0:
            path.append(nbrs[nbr_index])
        elif sample() < prob:
            path.append(nbrs[nbr_index])
    return path

def clear_client(rc):
    """
    Particularly with older versions of IPython memory becomes a huge issue.

    Frequent use of this function should alleviate the issue.
    """
    assert not rc.outstanding, "Can't clear a client with outstanding tasks!"
    rc.results.clear()
    rc.metadata.clear()
    rc.history = list()
    rc.session.digest_history.clear()

def clear_view(view):
    """
    Particularly with older versions of IPython memory becomes a huge issue.

    Frequent use of this function should alleviate the issue.
    """
    view.results.clear()
    view.history = list()

def march(d_view, neighbours, probabilities, sources, num_walkers, time_points,
        steps, assessor=ConstantValue(), transient=0, lb_view=None, seed=None):
    """
    Start a number of random walks on the given network for a number of time
    points. Records the activity at visited nodes.

    Parameters
    ----------
    d_view: DirectView
        An IPython.parallel.DirectView instance.
    neighbours: list of lists
        Adjacency list structure as returned by prepare_uniform_walk.
    probabilities: list of lists
        Transition probabilities list structure as returned by
        prepare_uniform_walk.
    sources: list
        List of valid starting node indices.
    num_walkers: callable
        A callable that returns an integer z >= 0.
    time_points: int
        Number of experiments to measure activity for.
    steps: int
        The maximum number of steps for each individual random walker.
    assessor: callable (optional)
        Called with the node index as argument, it should return the activity
        value of a visit.
    transient: int (optional)
        Cut-off the first transient steps of each random walk.
    lb_view: LoadBalancedView (optional)
        An IPython.parallel.LoadBalancedView instance which may have performance
        advantages over a DirectView.
    seed: (optional)
        A valid seed for numpy.random that makes runs deterministic in
        combination with using only a DirectView.

    Returns
    -------
    An array of dimensions number of nodes N x number of time points T that
    records the activity at each node per time point.

    Warning
    -------
    The use of a seed for reproducible results can only work with a
    ``DirectView``. Use of a ``LoadBalancedView`` will assign jobs to remote
    kernels in unpredictable order.
    """
    time_points = int(time_points)
    steps = int(steps)
    transient = int(transient)
    length = len(sources)
    rand_int = numpy.random.randint
    visits = numpy.zeros(shape=(len(neighbours), time_points), dtype=float)
    sys.stdout.flush()
    # make available on remote kernels
    d_view.push(dict(neighbours=neighbours, probabilities=probabilities,
        steps=steps), block=True)
    # assign different but deterministic seeds to all remote engines
    numpy.random.seed(seed)
    remote_seeds = set()
    while len(remote_seeds) < len(d_view):
        remote_seeds.add(rand_int(sys.maxint))
    d_view.scatter("seed", remote_seeds, block=True)
    d_view.execute("import numpy", block=True)
    d_view.execute("numpy.random.seed(seed[0])", block=True)
    view = isinstance(lb_view, LoadBalancedView)
    if view:
        num_krnl = len(lb_view)
    sys.stdout.write("\r{0:7.2%} complete".format(0.0))
    sys.stdout.flush()
    time_norm = float(time_points)
    for time in xrange(time_points):
        curr_visits = visits[:, time]
        curr_num = num_walkers()
        if curr_num == 0:
            sys.stdout.write("\r{0:7.2%} complete".format(time / time_norm))
            sys.stdout.flush()
            continue
        if view:
            size = max((curr_num - 1) // (num_krnl * 2), 1)
            results = lb_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False, ordered=False, chunksize=size)
        else:
            results = d_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False)
        for path in results:
            for node in path[transient:]:
                curr_visits[node] += assessor(node)
        # clear cache
        clear_client(d_view.client)
        if view:
            clear_view(lb_view)
        clear_view(d_view)
        sys.stdout.write("\r{0:7.2%} complete".format(time / time_norm))
        sys.stdout.flush()
    sys.stdout.write("\r{0:7.2%} complete".format(1.0))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return visits

def iterative_march(d_view, neighbours, probabilities, sources, num_walkers, time_points,
        steps, assessor=ConstantValue(), transient=0, lb_view=None, seed=None):
    """
    Start a number of random walks on the given network for a number of time points
    and compute running mean and standard deviation of the visits at each node.

    Parameters
    ----------
    d_view: DirectView
        An IPython.parallel.DirectView instance.
    neighbours: list of lists
        Adjacency list structure as returned by prepare_uniform_walk.
    probabilities: list of lists
        Transition probabilities list structure as returned by
        prepare_uniform_walk.
    sources: list
        List of valid starting node indices.
    num_walkers: callable
        A callable that returns an integer z >= 0.
    time_points: int
        Number of experiments to measure activity for.
    steps: int
        The maximum number of steps for each individual random walker.
    assessor: callable (optional)
        Called with the node index as argument, it should return the activity
        value of a visit.
    transient: int (optional)
        Cut-off the first transient steps of each random walk.
    lb_view: LoadBalancedView (optional)
        An IPython.parallel.LoadBalancedView instance which may have performance
        advantages over a DirectView.
    seed: (optional)
        A valid seed for numpy.random that makes runs deterministic in
        combination with using only a DirectView.

    Returns
    -------
    list: Running average of the activity at each node.
    list: Running standard deviation of the activity at each node.


    Warning
    -------
    The use of a seed for reproducible results can only work with a
    ``DirectView``. Use of a ``LoadBalancedView`` will assign jobs to remote
    kernels in unpredictable order.
    """
    time_points = int(time_points)
    steps = int(steps)
    transient = int(transient)
    length = len(sources)
    rand_int = numpy.random.randint
    # compute a running mean and sd as per:
    # http://en.wikipedia.org/wiki/Standard_deviation#Rapid_calculation_methods
    visits = numpy.zeros(len(neighbours))
    mean_fluxes = numpy.zeros(len(neighbours))
    subtraction = numpy.zeros(len(neighbours))
    std_fluxes = numpy.zeros(len(neighbours))
    # make available on remote kernels
    d_view.push(dict(neighbours=neighbours, probabilities=probabilities,
        steps=steps), block=True)
    # assign different but deterministic seeds to all remote engines
    numpy.random.seed(seed)
    remote_seeds = set()
    while len(remote_seeds) < len(d_view):
        remote_seeds.add(rand_int(sys.maxint))
    d_view.scatter("seed", remote_seeds, block=True)
    d_view.execute("import numpy", block=True)
    d_view.execute("numpy.random.seed(seed[0])", block=True)
    view = isinstance(lb_view, LoadBalancedView)
    if view:
        num_krnl = len(lb_view)
    sys.stdout.write("\r{0:7.2%} complete".format(0.0))
    sys.stdout.flush()
    time_norm = float(time_points)
    for time in xrange(1, time_points + 1):
        visits.fill(0)
        curr_num = num_walkers()
        if curr_num == 0:
            subtraction = -mean_fluxes
            mean_fluxes += subtraction / time
            std_fluxes += subtraction * (-mean_fluxes)
            sys.stdout.write("\r{0:7.2%} complete".format(time / time_norm))
            sys.stdout.flush()
            continue
        if view:
            size = max((curr_num - 1) // (num_krnl * 2), 1)
            results = lb_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False, ordered=False, chunksize=size)
        else:
            results = d_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False)
        for path in results:
            for node in path[transient:]:
                visits[node] += assessor(node)
        # clear cache
        clear_client(d_view.client)
        if view:
            clear_view(lb_view)
        clear_view(d_view)
        # compute running average and variation
        subtraction = visits - mean_fluxes
        mean_fluxes += subtraction / time
        std_fluxes += subtraction * (visits - mean_fluxes)
        sys.stdout.write("\r{0:7.2%} complete".format(time / time_norm))
        sys.stdout.flush()
    std_fluxes /= float(time - 1)
    numpy.sqrt(std_fluxes, std_fluxes)
    sys.stdout.write("\r{0:7.2%} complete".format(1.0))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return (mean_fluxes, std_fluxes)

def deletory_march(d_view, neighbours, probabilities, sources,
        num_walkers, time_points, steps, capacity, assessor=ConstantValue(),
        transient=0, lb_view=None, seed=None):
    """
    Start a number of random walks on the given network for a number of time
    points. Records the activity at visited nodes. And removes any walkers if
    the throughput capacity for the time point is exceeded.

    Parameters
    ----------
    d_view: DirectView
        An IPython.parallel.DirectView instance.
    neighbours: list of lists
        Adjacency list structure as returned by prepare_uniform_walk.
    probabilities: list of lists
        Transition probabilities list structure as returned by
        prepare_uniform_walk.
    sources: list
        List of valid starting node indices.
    num_walkers: callable
        A callable that returns an integer z >= 0.
    time_points: int
        Number of experiments to measure activity for.
    steps: int
        The maximum number of steps for each individual random walker.
    capacity: list or dict
        Contains maximum capacity of nodes at their respective index.
    assessor: callable (optional)
        Called with the node index as argument, it should return the activity
        value of a visit.
    transient: int (optional)
        Cut-off the first transient steps of each random walk.
    lb_view: LoadBalancedView (optional)
        An IPython.parallel.LoadBalancedView instance which may have performance
        advantages over a DirectView.
    seed: (optional)
        A valid seed for numpy.random that makes runs deterministic in
        combination with using only a DirectView.

    Returns
    -------
    An array of dimensions number of nodes N x number of time points T that
    records the activity at each node per time point. An array of equal
    dimension that measures the number of removed walkers.

    Warning
    -------
    The use of a seed for reproducible results can only work with a
    ``DirectView``. Use of a ``LoadBalancedView`` will assign jobs to remote
    kernels in unpredictable order.
    """
    time_points = int(time_points)
    steps = int(steps)
    transient = int(transient)
    length = len(sources)
    rand_int = numpy.random.randint
    visits = numpy.zeros(shape=(len(neighbours), time_points), dtype=float)
    removed = numpy.zeros(shape=(len(neighbours), time_points), dtype=int)
    sys.stdout.flush()
    # make available on remote kernels
    d_view.push(dict(neighbours=neighbours, probabilities=probabilities,
        steps=steps), block=True)
    # assign different but deterministic seeds to all remote engines
    numpy.random.seed(seed)
    remote_seeds = set()
    while len(remote_seeds) < len(d_view):
        remote_seeds.add(rand_int(sys.maxint))
    d_view.scatter("seed", remote_seeds, block=True)
    d_view.execute("import numpy", block=True)
    d_view.execute("numpy.random.seed(seed[0])", block=True)
    view = isinstance(lb_view, LoadBalancedView)
    if view:
        num_krnl = len(lb_view)
    sys.stdout.write("\r{0:7.2%} complete".format(0.0))
    sys.stdout.flush()
    time_norm = float(time_points)
    for time in xrange(time_points):
        curr_visits = visits[:, time]
        curr_num = num_walkers()
        if curr_num == 0:
            sys.stdout.write("\r{0:7.2%} complete".format(time / time_norm))
            sys.stdout.write("\r{0:7.2%} complete, removed: {1:12d}".format(time / time_norm,
                    removed[:, time].sum()))
            sys.stdout.flush()
            continue
        if view:
            size = max((curr_num - 1) // (num_krnl * 2), 1)
            results = lb_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False, ordered=False, chunksize=size)
        else:
            results = d_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False)
        for path in results:
            # if transient > 0, the nodes visited in the transient are ignored
            for node in path[transient:]:
                if curr_visits[node] >= capacity[node]:
                    removed[node, time] += 1
                    break
                curr_visits[node] += assessor(node)
        # clear cache
        clear_client(d_view.client)
        if view:
            clear_view(lb_view)
        clear_view(d_view)
        sys.stdout.write("\r{0:7.2%} complete".format(time / time_norm))
        sys.stdout.write("\r{0:7.2%} complete, removed: {1:12d}".format(time / time_norm,
                removed[:, time].sum()))
        sys.stdout.flush()
    sys.stdout.write("\r{0:7.2%} complete".format(1.0))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return (visits, removed)

def buffered_march(d_view, neighbours, probabilities, sources,
        num_walkers, time_points, steps, capacity, assessor=ConstantValue(),
        transient=0, lb_view=None, seed=None):
    """
    Start a number of random walks on the given network for a number of time
    points. Records the activity at visited nodes. And stores any walkers if
    the throughput capacity for the time point is exceeded. The buffered walker
    is then reintroduced at the next time point at that node.

    Parameters
    ----------
    d_view: DirectView
        An IPython.parallel.DirectView instance.
    neighbours: list of lists
        Adjacency list structure as returned by prepare_uniform_walk.
    probabilities: list of lists
        Transition probabilities list structure as returned by
        prepare_uniform_walk.
    sources: list
        List of valid starting node indices.
    num_walkers: callable
        A callable that returns an integer z >= 0.
    time_points: int
        Number of experiments to measure activity for.
    steps: int
        The maximum number of steps for each individual random walker.
    capacity: dict
        Map between node indices and their maximum capacity.
    assessor: callable (optional)
        Called with the node index as argument, it should return the activity
        value of a visit.
    transient: int (optional)
        Cut-off the first transient steps of each random walk.
    lb_view: LoadBalancedView (optional)
        An IPython.parallel.LoadBalancedView instance which may have performance
        advantages over a DirectView.
    seed: (optional)
        A valid seed for numpy.random that makes runs deterministic in
        combination with using only a DirectView.

    Returns
    -------
    An array of dimensions number of nodes N x number of time points T that
    records the activity at each node per time point. An array of equal
    dimension that measures the backlog at each time point.

    Warning
    -------
    The use of a seed for reproducible results can only work with a
    ``DirectView``. Use of a ``LoadBalancedView`` will assign jobs to remote
    kernels in unknown order.
    """
    time_points = int(time_points)
    steps = int(steps)
    transient = int(transient)
    length = len(sources)
    rand_int = numpy.random.randint
    total_throughput = sum(capacity[node] for node in range(len(neighbours)))
    visits = numpy.zeros(shape=(len(neighbours), time_points), dtype=float)
    backlog = numpy.zeros(shape=(len(neighbours), time_points), dtype=int)
    sys.stdout.flush()
    # make available on remote kernels
    d_view.push(dict(neighbours=neighbours, probabilities=probabilities,
        steps=steps), block=True)
    # assign different but deterministic seeds to all remote engines
    numpy.random.seed(seed)
    remote_seeds = set()
    while len(remote_seeds) < len(d_view):
        remote_seeds.add(rand_int(sys.maxint))
    d_view.scatter("seed", remote_seeds, block=True)
    d_view.execute("import numpy", block=True)
    d_view.execute("numpy.random.seed(seed[0])", block=True)
    view = isinstance(lb_view, LoadBalancedView)
    if view:
        num_krnl = len(lb_view)
    sys.stdout.write("\r{0:7.2%} complete".format(0.0))
    sys.stdout.flush()
    old_buffer = list()
    new_buffer = list()
    time_norm = float(time_points)
    for time in xrange(time_points):
        rem_time = time_points - time
        curr_visits = visits[:, time]
        curr_num = num_walkers()
        if curr_num == 0:
            old_buffer = new_buffer
            new_buffer = list()
            for path in old_buffer:
                # no need to cut transient since the buffered paths have been cut
                for (i, node) in enumerate(path):
                    if curr_visits[node] >= capacity[node]:
                        backlog[node, time] += 1
                        new_buffer.append(path[i:])
                        break
                    curr_visits[node] += assessor(node)
            sys.stdout.write("\r{0:7.2%} complete, backlog: {1:12d}".format(time / time_norm,
                len(new_buffer)))
            sys.stdout.flush()
            continue
        if view:
            size = max((curr_num - 1) // (num_krnl * 2), 1)
            results = lb_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False, ordered=False, chunksize=size)
        else:
            results = d_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False)
        old_buffer = new_buffer[:total_throughput * rem_time]
        new_buffer = list()
        for path in old_buffer:
            # no need to cut transient since the buffered paths have been cut
            for (i, node) in enumerate(path):
                if curr_visits[node] >= capacity[node]:
                    backlog[node, time] += 1
                    break
                curr_visits[node] += assessor(node)
            if i < len(path):
                new_buffer.append(path[i:])
        for path in results:
            path = path[transient:]
            # if transient > 0, the nodes visited in the transient are ignored
            for (i, node) in enumerate(path):
                if curr_visits[node] >= capacity[node]:
                    backlog[node, time] += 1
                    new_buffer.append(path[i:])
                    break
                curr_visits[node] += assessor(node)
        # clear cache
        clear_client(d_view.client)
        if view:
            clear_view(lb_view)
        clear_view(d_view)
        sys.stdout.write("\r{0:7.2%} complete, backlog: {1:12d}".format(time / time_norm,
            len(new_buffer)))
        sys.stdout.flush()
    sys.stdout.write("\r{0:7.2%} complete".format(1.0))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return (visits, backlog)


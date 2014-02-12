# -*- coding: utf-8 -*-


"""
========================
Random Walks on Networks
========================

:Author:
    Moritz Emanuel Beber
:Date:
    2012-10-23
:Copyright:
    Copyright |c| 2013, Jacobs University Bremen gGmbH, all rights reserved.
:File:
    walkers.py

.. |c| unicode:: U+A9
"""


__all__ = ["prepare_uniform_walk", "prepare_directed_walk", "march",
        "deletory_march", "buffered_march"]

#        "limited_uniform_random_walker",

import sys
import itertools

import numpy
import networkx as nx

from collections import deque

from .visits import ConstantValue


def prepare_uniform_walk(graph, node2id=None, weight=None):
    """
    Prepare data structures for a uniform random walk.

    Works for undirected as well as directed graphs. For multi-graphs simply
    provide a suitable edge weight.

    Parameters
    ----------
    graph: nx.(Di)Graph
        The underlying network.
    node2id: dict
        A mapping from nodes in graph to indices running from 0 to (N - 1).
    weight: hashable
        The keyword for edge data that should be used to weigh the propagation
        probability.
    """
    nodes = sorted(graph.nodes())
    if len(nodes) < 2:
        raise nx.NetworkXError("network is too small")
    if node2id is None:
        node2id = dict(itertools.izip(nodes, itertools.count()))
    probabilities = range(len(nodes))
    neighbours = range(len(nodes))
    for node in nodes:
        i = node2id[node]
        adj = graph[node]
        out_deg = len(adj)
        if out_deg == 0:
            probabilities[i] = list()
            neighbours[i] = list()
            continue
        prob = 0.0
        probabilities[i] = numpy.zeros(out_deg, dtype=float)
        neighbours[i] = numpy.zeros(out_deg, dtype=int)
        for (j, (nhbr, data)) in enumerate(adj.iteritems()):
            neighbours[i][j] = node2id[nhbr]
            prob += data.get(weight, 1.0)
            probabilities[i][j] = prob
        # prob is now the sum of all edge weights, normalise to unity
        probabilities[i] /= prob
    return (probabilities, neighbours, node2id)

def prepare_directed_walk(graph, input_layer, output_layer, temperature,
        node2id=None, weight=None):
    """
    Prepare data structures for a directed random walk (see docs).

    Works for undirected as well as directed graphs. For multi-graphs simply
    provide a suitable edge weight.

    Parameters
    ----------
    graph: nx.(Di)Graph
        The underlying network.
    node2id: dict
        A mapping from nodes in graph to indices running from 0 to (N - 1).
    weight: hashable
        The keyword for edge data that should be used to weigh the propagation
        probability.
    """
    nodes = sorted(graph.nodes())
    if len(nodes) < 2:
        raise nx.NetworkXError("network is too small")
    if node2id is None:
        node2id = dict(itertools.izip(nodes, itertools.count()))
    shortest_paths = nx.shortest_path_length(graph, weight=weight)
    min_separation = min(shortest_paths[in_node][out_node]\
                for in_node in input_layer for out_node in output_layer)
    middle_nodes = set(nodes).difference(input_layer, output_layer)
    for node in middle_nodes:
        min_in = min(shortest_paths[node][in_node] for in_node in input_layer)
        min_out = min(shortest_paths[node][out_node] for out_node in output_layer)
        graph.node[node]["in"] = min_in
        graph.node[node]["out"] = min_out
        graph.node[node]["coord"] = 0.5 * (
                1.0 + (min_in / min_separation) - (min_out / min_separation))
    probabilities = range(len(nodes))
    neighbours = range(len(nodes))
    for node in nodes:
        i = node2id[node]
        adj = graph[node]
        out_deg = len(adj)
        if out_deg == 0:
            probabilities[i] = list()
            neighbours[i] = list()
            continue
        probabilities[i] = numpy.zeros(out_deg, dtype=float)
        neighbours[i] = numpy.zeros(out_deg, dtype=int)
        for (j, (nhbr, data)) in enumerate(adj.iteritems()):
            neigh = node2id[nhbr]
            neighbours[i][j] = neigh
            coord_diff = graph.node[neigh] - graph.node[node]
            if coord_diff > 0.0:
                probabilities[i][j] = 1.0
            else:
                probabilities[i][j] = numpy.exp(coord_diff / temperature)
    return (probabilities, neighbours, node2id)

def march(neighbours, probabilities, sources, num_walkers, time_points,
        steps, assessor=ConstantValue(), transient=0, seed=None):
    """
    Start a number of random walks on the given network for a number of time
    points. Records the activity at visited nodes.

    Parameters
    ----------
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
    seed: (optional)
        A valid seed for numpy.random that makes runs deterministic.

    Returns
    -------
    An array of dimensions number of nodes N x number of time points T that
    records the activity at each node per time point.

    """
    time_points = int(time_points)
    steps = int(steps)
    transient = int(transient)
    numpy.random.seed(seed)
    rand_int = numpy.random.randint
    smpl = numpy.random.random_sample
    choose = numpy.searchsorted
    visits = numpy.zeros(shape=(len(neighbours), time_points), dtype=float)
    sys.stdout.write("\r{0:7.2%} complete".format(0.0))
    sys.stdout.flush()
    time_norm = float(time_points)
    for time in xrange(time_points):
        curr_visits = visits[:, time]
        curr_num = num_walkers()
        for i in xrange(curr_num):
            node = sources[rand_int(len(sources))]
            if transient == 0:
                curr_visits[node] += assessor(node)
            for s in xrange(steps):
                nbrs = neighbours[node]
                if len(nbrs) == 0:
                    break
                draw = smpl()
                node = nbrs[choose(probabilities[node], draw)]
                if s > transient:
                    curr_visits[node] += assessor(node)
        sys.stdout.write("\r{0:7.2%} complete".format(time / time_norm))
        sys.stdout.flush()
    sys.stdout.write("\r{0:7.2%} complete".format(1.0))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return visits

def deletory_march(neighbours, probabilities, sources, num_walkers, time_points,
        steps, capacity, assessor=ConstantValue(), transient=0, seed=None):
    """
    Start a number of random walks on the given network for a number of time
    points. Records the activity at visited nodes.

    Parameters
    ----------
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
    seed: (optional)
        A valid seed for numpy.random that makes runs deterministic.

    Returns
    -------
    An array of dimensions number of nodes N x number of time points T that
    records the activity at each node per time point. An array of equal
    dimension that measures the number of removed walkers.
    """
    time_points = int(time_points)
    steps = int(steps)
    transient = int(transient)
    numpy.random.seed(seed)
    rand_int = numpy.random.randint
    smpl = numpy.random.random_sample
    choose = numpy.searchsorted
    visits = numpy.zeros(shape=(len(neighbours), time_points), dtype=float)
    removed = numpy.zeros(shape=(len(neighbours), time_points), dtype=int)
    sys.stdout.write("\r{0:7.2%} complete".format(0.0))
    sys.stdout.flush()
    time_norm = float(time_points)
    for time in xrange(time_points):
        curr_visits = visits[:, time]
        curr_num = num_walkers()
        for _ in xrange(curr_num):
            node = sources[rand_int(len(sources))]
            if curr_visits[node] >= capacity[node]:
                removed[node, time] += 1
                continue
            if transient == 0:
                curr_visits[node] += assessor(node)
            for s in xrange(steps):
                nbrs = neighbours[node]
                if len(nbrs) == 0:
                    break
                draw = smpl()
                node = nbrs[choose(probabilities[node], draw)]
                if curr_visits[node] >= capacity[node]:
                    removed[node, time] += 1
                    break
                if s > transient:
                    curr_visits[node] += assessor(node)
        sys.stdout.write("\r{0:7.2%} complete".format(time / time_norm))
        sys.stdout.flush()
    sys.stdout.write("\r{0:7.2%} complete".format(1.0))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return (visits, removed)

def buffered_march(neighbours, probabilities, sources, num_walkers, time_points,
        steps, capacity, assessor=ConstantValue(), transient=0, seed=None):
    """
    Start a number of random walks on the given network for a number of time
    points. Records the activity at visited nodes.

    Parameters
    ----------
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
    seed: (optional)
        A valid seed for numpy.random that makes runs deterministic.

    Returns
    -------
    An array of dimensions number of nodes N x number of time points T that
    records the activity at each node per time point. An array of equal
    dimension that measures the number of stored walkers.
    """
    time_points = int(time_points)
    steps = int(steps)
    transient = int(transient)
    numpy.random.seed(seed)
    rand_int = numpy.random.randint
    smpl = numpy.random.random_sample
    choose = numpy.searchsorted
    visits = numpy.zeros(shape=(len(neighbours), time_points), dtype=float)
    backlog = numpy.zeros(shape=(len(neighbours), time_points), dtype=int)
    sys.stdout.write("\r{0:7.2%} complete".format(0.0))
    sys.stdout.flush()
    time_norm = float(time_points)
    store = deque()
    for time in xrange(time_points):
        curr_visits = visits[:, time]
        curr_num = num_walkers()
        today_store = len(store)
        for _ in xrange(today_store):
            (node, performed) = store.pop()
            if curr_visits[node] >= capacity[node]:
                backlog[node, time] += 1
                store.appendleft((node, performed))
                continue
            if performed > transient:
                curr_visits[node] += assessor(node)
            for s in xrange(steps - performed):
                nbrs = neighbours[node]
                if len(nbrs) == 0:
                    break
                draw = smpl()
                node = nbrs[choose(probabilities[node], draw)]
                performed += 1
                if curr_visits[node] >= capacity[node]:
                    backlog[node, time] += 1
                    store.appendleft((node, performed))
                    break
                if performed > transient:
                    curr_visits[node] += assessor(node)
        for _ in xrange(curr_num):
            node = sources[rand_int(len(sources))]
            if curr_visits[node] >= capacity[node]:
                backlog[node, time] += 1
                store.appendleft((node, 0))
                continue
            if transient == 0:
                curr_visits[node] += assessor(node)
            for s in xrange(steps):
                nbrs = neighbours[node]
                if len(nbrs) == 0:
                    break
                draw = smpl()
                node = nbrs[choose(probabilities[node], draw)]
                if curr_visits[node] >= capacity[node]:
                    backlog[node, time] += 1
                    store.appendleft((node, s + 1))
                    break
                if s > transient:
                    curr_visits[node] += assessor(node)
        sys.stdout.write("\r{0:7.2%} complete".format(time / time_norm))
        sys.stdout.flush()
    sys.stdout.write("\r{0:7.2%} complete".format(1.0))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return (visits, backlog)


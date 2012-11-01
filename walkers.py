# -*- coding: utf-8 -*-


"""
==========================
Random Walkers on Networks
==========================

:Author:
    Moritz Emanuel Beber
:Date:
    2012-10-23
:Copyright:
    Copyright(c) 2012 Jacobs University of Bremen. All rights reserved.
:File:
    walkers.py
"""


import sys
#import itertools
import bisect
import multiprocessing
import numpy
import networkx as nx

from Queue import Empty


class UniformInterval(object):

    def __init__(self, mid_point, variation=0, **kw_args):
        super(UniformInterval, self).__init__(**kw_args)
        self.rand_int = numpy.random.random_integers
        self.mid_point = int(mid_point)
        self.variation = int(variation)

    def __call__(self):
        if self.variation > 0:
            self.__call__ = self.variable
        else:
            self.__call__ = self.constant
        return self.__call__()

    def constant(self):
        return self.mid_point

    def variable(self):
        return self.mid_point + self.rand_int(-self.variation, self.variation)


def uniform_random_walk((adj, node, steps)):
    """
    Perform a single random walk on a network with a uniform probability of a
    next step.

    Arguments
    ---------
    graph: nx.DiGraph
        The underlying network.
    node: hashable
        A node from the network.
    steps: int
        A positive number of steps the walker should go until it is removed.
    """
    smpl = numpy.random.random_sample
    choose = bisect.bisect_left
    path = [node]
    for s in xrange(steps):
        (nbrs, probs) = adj.get(node, (False, False))
        if not nbrs:
            return path
        draw = smpl()
        # the nbrs list and probs list correspond to each other
        # we use a binary search to find the index to the left of the
        # probability and take that node
        node = nbrs[choose(probs, draw)]
        path.append(node)
    return path

def prepare_uniform_walk_adjacency(graph, weight=None):
    nodes = sorted(graph.nodes())
    if len(nodes) < 2:
        raise nx.NetworkXError("network is too small")
    adj = dict()
    indices = dict()
    for (i, node) in enumerate(nodes):
        indices[node] = i
        neighbours = list()
        probabilities = list()
        if graph.out_degree(node) == 0:
            continue
        prob = 0.0
        for (u, v, data) in graph.out_edges_iter(data=True):
            neighbours.append(v)
            prob += data.get(weight, 1.0)
            probabilities.append(prob)
        probabilities = numpy.asarray(probabilities)
        # prob is now the sum of all edge weights, normalise to unity
        probabilities /= prob
        adj[node] = (neighbours, probabilities)
    return (adj, indices)

def walks_pool(adjacency, indices, num_walkers, time_points, steps, num_cpu=1):
    """
    Start a number of random walkers on the given network for given time points.
    """
    time_points = int(time_points)
    steps = int(steps)
    num_cpu = int(num_cpu)
    nodes = sorted(indices.keys())
    length = len(nodes)
    rand_int = numpy.random.randint
    # compute a running mean and sd as per:
    # http://en.wikipedia.org/wiki/Standard_deviation#Rapid_calculation_methods
    visits = numpy.zeros(length, dtype="int32")
    mean_fluxes = numpy.zeros(length)
    subtraction = numpy.zeros(length)
    std_fluxes = numpy.zeros(length)
    pool = multiprocessing.Pool(num_cpu)
    for time in xrange(1, time_points + 1):
        sys.stdout.write("\r{0:.2%} completed".format(
            time / float(time_points)))
        sys.stdout.flush()
        visits.fill(0)
        # a large number of walkers will probably exceed available memory
        visited = pool.imap(uniform_random_walk,
                [(adjacency, nodes[rand_int(length)], steps)\
                for i in xrange(num_walkers())])
        for path in visited:
            for node in path:
                visits[indices[node]] += 1
        # compute running average and variation
        subtraction = visits - mean_fluxes
        mean_fluxes += subtraction / time
        std_fluxes += subtraction * (visits - mean_fluxes)
    std_fluxes /= time - 1
    std_fluxes = numpy.sqrt(std_fluxes)
    sys.stdout.write("\n")
    return (mean_fluxes, std_fluxes)

def uniform_random_walk_worker(in_queue, out_queue, adjacency):
    """
    Perform a single random walk on a network with a uniform probability of a
    next step.

    Arguments
    ---------
    """
    smpl = numpy.random.random_sample
    choose = bisect.bisect_left
    for (node, steps) in iter(in_queue.get, "STOP"):
        path = [node]
        for s in xrange(steps):
            (nbrs, probs) = adjacency.get(node, (False, False))
            if not nbrs:
                out_queue.put(path)
                continue
            draw = smpl()
            # the nbrs list and probs list correspond to each other
            # we use a binary search to find the index to the left of the
            # probability and take that node
            node = nbrs[choose(probs, draw)]
            path.append(node)
        out_queue.put(path)

def walks_queue(adjacency, indices, num_walkers, time_points, steps, num_cpu=1):
    """
    Start a number of random walkers on the given network for given time points.
    """
    time_points = int(time_points)
    steps = int(steps)
    num_cpu = int(num_cpu)
    nodes = sorted(indices.keys())
    length = len(nodes)
    rand_int = numpy.random.randint
    # compute a running mean and sd as per:
    # http://en.wikipedia.org/wiki/Standard_deviation#Rapid_calculation_methods
    visits = numpy.zeros(length, dtype="int32")
    mean_fluxes = numpy.zeros(length)
    subtraction = numpy.zeros(length)
    std_fluxes = numpy.zeros(length)
    # worker queues
    in_queue = multiprocessing.Queue()
    out_queue = multiprocessing.Queue()
    # start processes
    workers = [multiprocessing.Process(target=uniform_random_walk_worker,
            args=(in_queue, out_queue, adjacency))\
            for i in range(num_cpu)]
    for proc in workers:
        proc.daemon = True
        proc.start()
    sys.stdout.write("\r{0:.2%} complete".format(0.0))
    sys.stdout.flush()
    for time in xrange(1, time_points + 1):
        visits.fill(0)
        curr_num = num_walkers()
        for i in xrange(curr_num):
            in_queue.put((nodes[rand_int(length)], steps), block=False)
        for i in xrange(curr_num):
            path = out_queue.get()
            for node in path:
                visits[indices[node]] += 1
        # compute running average and variation
        subtraction = visits - mean_fluxes
        mean_fluxes += subtraction / time
        std_fluxes += subtraction * (visits - mean_fluxes)
        sys.stdout.write("\r{0:.2%} complete".format(time / float(time_points)))
        sys.stdout.flush()
    std_fluxes /= time - 1
    std_fluxes = numpy.sqrt(std_fluxes)
    sys.stdout.write("\n")
    for proc in workers:
        in_queue.put("STOP")
    return (mean_fluxes, std_fluxes)


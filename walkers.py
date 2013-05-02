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
    Copyright |c| 2013, Jacobs University Bremen gGmbH, all rights reserved.
:File:
    walkers.py

.. |c| unicode:: U+A9
"""


import sys
import itertools
import bisect
import multiprocessing
import numpy
import networkx as nx


class UniformInterval(object):

    def __init__(self, mid_point, variation=0, **kw_args):
        super(UniformInterval, self).__init__(**kw_args)
        self.rand_int = numpy.random.random_integers
        self.mid_point = int(mid_point)
        self.variation = int(variation)
        self.mini = self.mid_point - self.variation
        self.maxi = self.mid_point + self.variation

    def __call__(self):
        if self.variation > 0:
            self.__call__ = self.variable
        else:
            self.__call__ = self.constant
        return self.__call__()

    def constant(self):
        return self.mid_point

    def variable(self):
        return self.rand_int(self.mini, self.maxi)


def prepare_uniform_walk(graph, weight=None):
    """
    Prepare data structures for a uniform random walk.

    Works for undirected as well as directed graphs. For multi-graphs simply
    provide a suitable edge weight.

    Arguments
    ---------
    graph: nx.(Di)Graph
        The underlying network.
    weight: hashable
        The keyword for edge data that should be used to weigh the propagation
        probability.
    """
    nodes = sorted(graph.nodes())
    if len(nodes) < 2:
        raise nx.NetworkXError("network is too small")
    indices = dict(itertools.izip(nodes, itertools.count()))
    probabilities = list()
    neighbours = list()
    for (i, node) in enumerate(nodes):
        adj = graph[node]
        out_deg = len(adj)
        if out_deg == 0:
            probabilities.append([])
            neighbours.append([])
            continue
        prob = 0.0
        probabilities.append(numpy.zeros(out_deg, dtype=float))
        neighbours.append(numpy.zeros(out_deg, dtype=int))
        for (j, (nhbr, data)) in enumerate(adj.iteritems()):
            neighbours[i][j] = indices[nhbr]
            prob += data.get(weight, 1.0)
            probabilities[i][j] = prob
        # prob is now the sum of all edge weights, normalise to unity
        probabilities[i] /= prob
    return (probabilities, neighbours)

def uniform_random_walker(in_queue, out_queue, probabilities, neighbours):
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
            nbrs = neighbours[node]
            if len(nbrs) == 0:
                break
            draw = smpl()
            # the nbrs list and probs list correspond to each other
            # we use a binary search to find the index to the left of the
            # probability and take that node
            node = nbrs[choose(probabilities[node], draw)]
            path.append(node)
        out_queue.put(path)

def queued_march(neighbours, probabilities, sources, num_walkers, time_points,
        steps, num_cpu=1):
    """
    Start a number of random walkers on the given network for given time points.
    """
    time_points = int(time_points)
    steps = int(steps)
    num_cpu = int(num_cpu)
    length = len(sources)
    rand_int = numpy.random.randint
    # compute a running mean and sd as per:
    # http://en.wikipedia.org/wiki/Standard_deviation#Rapid_calculation_methods
    visits = numpy.zeros(len(neighbours), dtype="int32")
    mean_fluxes = numpy.zeros(len(neighbours))
    subtraction = numpy.zeros(len(neighbours))
    std_fluxes = numpy.zeros(len(neighbours))
    # worker queues
    in_queue = multiprocessing.Queue()
    out_queue = multiprocessing.Queue()
    # start processes
    workers = [multiprocessing.Process(target=uniform_random_walker,
            args=(in_queue, out_queue, probabilities, neighbours))\
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
            in_queue.put((sources[rand_int(length)], steps), block=False)
        for i in xrange(curr_num):
            path = out_queue.get()
            for node in path:
                visits[node] += 1
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


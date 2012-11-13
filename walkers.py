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
    Prepare data structures for a directed uniform random walk.

    Arguments
    ---------
    graph: nx.DiGraph
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
        out_deg = graph.out_degree(node)
        if out_deg == 0:
            probabilities.append([])
            neighbours.append([])
            continue
        prob = 0.0
        probabilities.append(numpy.zeros(out_deg, dtype=float))
        neighbours.append(numpy.zeros(out_deg, dtype=int))
        for (j, (u, v, data)) in enumerate(graph.out_edges_iter(data=True)):
            neighbours[i][j] = indices[v]
            prob += data.get(weight, 1.0)
            probabilities[i][j] = prob
        # prob is now the sum of all edge weights, normalise to unity
        probabilities /= prob
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
            if not nbrs:
                out_queue.put(path)
                continue
            draw = smpl()
            # the nbrs list and probs list correspond to each other
            # we use a binary search to find the index to the left of the
            # probability and take that node
            node = nbrs[choose(probabilities[node], draw)]
            path.append(node)
        out_queue.put(path)

def queued_march(neighbours, probabilities, indices, num_walkers, time_points,
        steps, num_cpu=1):
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


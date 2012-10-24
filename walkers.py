#!/usr/bin/env python
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
import numpy
import networkx as nx


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


def uniform_random_walk((graph, node, steps)):
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
        attr = graph.node[node]
        if len(attr["nbrs"]) == 0:
            return path
        draw = smpl()
        node = attr["nbrs"][choose(attr["probs"], draw)]
        path.append(node)
    return path

def prepare_uniform_walk_graph(graph, weight=None):
    for (node, attr) in graph.nodes_iter(data=True):
        attr["nbrs"] = list()
        attr["probs"] = list()
        if graph.out_degree(node) == 0:
            continue
        factor = 1 / float(graph.out_degree(node))
        prob = 0.0
        for (u, v, data) in graph.out_edges_iter(data=True):
            attr["nbrs"].append(v)
            prob += data.get(weight, 1.0) * factor
            attr["probs"].append(prob)

def walks(graph, num_walkers, time_points, steps, weight=None):
    """
    Start a number of random walkers on the given network for given time points.
    """
    nodes = sorted(graph.nodes())
    length = len(nodes)
    if length < 2:
        raise nx.NetworkXError("network is too small")
    rand_int = numpy.random.randint
    visits = numpy.zeros(shape=(length, time_points), dtype="int32")
    indices = dict(itertools.izip(nodes, itertools.count()))
    for t in xrange(time_points):
        print "\rtime", t,
# this step lends itself to a multiprocessing result iterator
# in that case we can iteratively compute the mean and sd of the flux and save
# memory space
        visited = map(uniform_random_walk,
                [(graph, nodes[rand_int(length)], steps)\
                for i in xrange(num_walkers())])
        for path in visited:
            for node in path:
                visits[indices[node], t] += 1
    print
    return visits

def main(argv):
    net = nx.scale_free_graph(1E04)
    prepare_uniform_walk_graph(net)
    print walks(net, UniformInterval(1E04, 20), 1E02, 1E03)


if __name__ == "__main__":
    argc = len(sys.argv)
    if argc < 2 or argc > 3:
        print("Usage:\npython %s" % sys.argv[0])
        sys.exit(2)
    main(sys.argv[1:])


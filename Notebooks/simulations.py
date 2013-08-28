# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # Random Walk Statistics

# <codecell>

import os
import sys
import uuid

import numpy
import networkx as nx

# <codecell>

sys.path.insert(0, "..")
import foggy

# <codecell>

base_dir = "Data"
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

# <codecell>

filename = os.path.join(base_dir, "network.pkl")
if not os.path.exists(filename):
    network = nx.barabasi_albert_graph(int(1E03), 3)
#    network = nx.scale_free_graph(int(1E03))
#    network = nx.fast_gnp_random_graph(int(1E03), 0.01)
    nx.write_gpickle(network, filename)
else:
    network = nx.read_gpickle(filename)

if network.is_directed():
    print "directed network with:"
else:
    print "undirected network with:"
print "\t", len(network), "nodes"
print "\t", network.size(), "links"

# <codecell>

filename = os.path.join(base_dir, "node2id.pkl")
if not os.path.exists(filename):
    (probs, nbrs, indices) = foggy.prepare_uniform_walk(network)
    nx.write_gpickle(indices, filename)
else:
    indices = nx.read_gpickle(filename)
    (probs, nbrs, indices) = foggy.prepare_uniform_walk(network, node2id=indices)

# <codecell>

from IPython.parallel import Client

# <codecell>

rc = Client()

# <codecell>

dv = rc.direct_view()
lv = rc.load_balanced_view()

# <codecell>

dv.execute("import sys", block=True);
dv.execute("sys.path.insert(0, '..')", block=True);
dv.execute("import foggy", block=True);
dv.execute("import numpy", block=True);

# <codecell>

num_walkers = len(network)
num_steps = num_walkers * 3
source_nodes = range(len(network))
time_points = 100

## <markdowncell>
#
## First random walk with a constant number of walkers, that is, one for each node in the network and over 100 time steps. The walkers perform ten times the number of nodes steps.
#
## <codecell>
#
#filename = os.path.join(base_dir, "uniform_random_walk.npy")
#if not os.path.exists(filename):
#    activity = foggy.parallel_march(dv, nbrs, probs, source_nodes, foggy.UniformInterval(num_walkers),
#            time_points, num_steps, lb_view=lv)
#    numpy.save(filename, activity)
#
## <codecell>
#
#filename = os.path.join(base_dir, "uniform_random_walk_cut_transient.npy")
#if not os.path.exists(filename):
#    activity = foggy.parallel_march(dv, nbrs, probs, source_nodes, foggy.UniformInterval(num_walkers),
#            time_points, num_steps, transient=num_steps / 10, lb_view=lv)
#    numpy.save(filename, activity)
#
## <markdowncell>
#
## Second random walk with a significant variation of the number of walkers in each time step, i.e., the variation is twice the mean.
#
## <codecell>
#
#filename = os.path.join(base_dir, "varied_uniform_random_walk.npy")
#if not os.path.exists(filename):
#    activity = foggy.parallel_march(dv, nbrs, probs, source_nodes, foggy.UniformInterval(num_walkers, num_walkers * 2),
#            time_points, num_steps, lb_view=lv)
#    numpy.save(filename, activity)
#
## <codecell>
#
#filename = os.path.join(base_dir, "varied_uniform_random_walk_cut_transient.npy")
#if not os.path.exists(filename):
#    activity = foggy.parallel_march(dv, nbrs, probs, source_nodes, foggy.UniformInterval(num_walkers, num_walkers * 2),
#            time_points, num_steps, transient=num_steps / 10, lb_view=lv)
#    numpy.save(filename, activity)
#
## <markdowncell>
#
## Third random walk with no variation of the number of walkers in each time step but with a degree-dependent value for each node that should lead to a power-law scaling with $\alpha = 0.65$.
#
## <codecell>
#
#filename = os.path.join(base_dir, "uniform_random_walk_mu.npy")
#if not os.path.exists(filename):
#    activity = foggy.parallel_march(dv, nbrs, probs, source_nodes, foggy.UniformInterval(num_walkers),
#            time_points, num_steps, assessor=foggy.DegreeDependentValue(network, indices, mu=foggy.compute_mu(0.65)), lb_view=lv)
#    numpy.save(filename, activity)
#
## <codecell>
#
#filename = os.path.join(base_dir, "uniform_random_walk_mu_cut_transient.npy")
#if not os.path.exists(filename):
#    activity = foggy.parallel_march(dv, nbrs, probs, source_nodes, foggy.UniformInterval(num_walkers),
#            time_points, num_steps, assessor=foggy.DegreeDependentValue(network, indices, mu=foggy.compute_mu(0.65)),
#            transient=num_steps / 10, lb_view=lv)
#    numpy.save(filename, activity)
#
## <codecell>
#
#filename = os.path.join(base_dir, "varied_uniform_random_walk_mu.npy")
#if not os.path.exists(filename):
#    activity = foggy.parallel_march(dv, nbrs, probs, source_nodes, foggy.UniformInterval(num_walkers, num_walkers * 2),
#            time_points, num_steps, assessor=foggy.DegreeDependentValue(network, indices, mu=foggy.compute_mu(0.65)), lb_view=lv)
#    numpy.save(filename, activity)
#
## <codecell>
#
#filename = os.path.join(base_dir, "varied_uniform_random_walk_mu_cut_transient.npy")
#if not os.path.exists(filename):
#    activity = foggy.parallel_march(dv, nbrs, probs, source_nodes, foggy.UniformInterval(num_walkers, num_walkers * 2),
#            time_points, num_steps, assessor=foggy.DegreeDependentValue(network, indices, mu=foggy.compute_mu(0.65)),
#            transient=num_steps / 10, lb_view=lv)
#    numpy.save(filename, activity)

# <codecell>

unique_run = str(uuid.uuid1())

# <codecell>

capacity = numpy.zeros(len(network), dtype=float)
capacity += float(num_walkers * num_steps) / float(len(network))

# <codecell>

capacity_factors = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]

# <codecell>

print "deletory_uniform_random_walk_uniform_capacity"
for k in capacity_factors:
    dynamic = capacity * k
    print dynamic.sum()
    filename = os.path.join(base_dir,
            "deletory_uniform_random_walk_uniform_capacity_%d_%s.npz" %\
            (int(dynamic.sum()), unique_run))
    if not os.path.exists(filename):
        # adjustment for interesting observations
        (activity, removed) = foggy.deletory_parallel_march(dv, nbrs, probs, source_nodes,
                foggy.UniformInterval(num_walkers), time_points, num_steps, dynamic, lb_view=lv)
        numpy.savez(filename, activity=activity, hits=removed, capacity=dynamic)

# <codecell>

print "deletory_varied_uniform_random_walk_uniform_capacity"
for k in capacity_factors:
    dynamic = capacity * k
    print dynamic.sum()
    filename = os.path.join(base_dir,
            "deletory_varied_uniform_random_walk_uniform_capacity_%d_%s.npz" %\
            (int(dynamic.sum()), unique_run))
    if not os.path.exists(filename):
        # adjustment for interesting observations
        (activity, removed) = foggy.deletory_parallel_march(dv, nbrs, probs, source_nodes,
                foggy.UniformInterval(num_walkers, 2 * num_walkers), time_points, num_steps,
                dynamic, lb_view=lv)
        numpy.savez(filename, activity=activity, hits=removed, capacity=dynamic)

# <codecell>

print "buffered_uniform_random_walk_uniform_capacity"
for k in capacity_factors:
    dynamic = capacity * k
    print dynamic.sum()
    filename = os.path.join(base_dir,
            "buffered_uniform_random_walk_uniform_capacity_%d_%s.npz" %\
            (int(dynamic.sum()), unique_run))
    if not os.path.exists(filename):
        # adjustment for interesting observations
        (activity, backlog) = foggy.buffered_parallel_march(dv, nbrs, probs, source_nodes,
                foggy.UniformInterval(num_walkers), time_points, num_steps, dynamic, lb_view=lv)
        numpy.savez(filename, activity=activity, hits=backlog, capacity=dynamic)

# <codecell>

print "buffered_varied_uniform_random_walk_uniform_capacity"
for k in capacity_factors:
    dynamic = capacity * k
    print dynamic.sum()
    filename = os.path.join(base_dir,
            "buffered_varied_uniform_random_walk_uniform_capacity_%d_%s.npz" %\
            (int(dynamic.sum()), unique_run))
    if not os.path.exists(filename):
        (activity, backlog) = foggy.buffered_parallel_march(dv, nbrs, probs, source_nodes,
                foggy.UniformInterval(num_walkers, 2 * num_walkers), time_points, num_steps,
                dynamic, lb_view=lv)
        numpy.savez(filename, activity=activity, hits=backlog, capacity=dynamic)

# <codecell>

capacity.fill(0.0) # not strictly necessary
for (node, deg) in network.degree_iter():
    capacity[indices[node]] = float(deg) * 100.0

# <codecell>

capacity_factors = [0.01, 0.1, 1.0, 10.0, 100.0]

# <codecell>

print "deletory_uniform_random_walk_degree_capacity"
for k in capacity_factors:
    dynamic = capacity * k
    print dynamic.sum()
    filename = os.path.join(base_dir,
            "deletory_uniform_random_walk_degree_capacity_%d_%s.npz" %\
            (int(dynamic.sum()), unique_run))
    if not os.path.exists(filename):
        (activity, removed) = foggy.deletory_parallel_march(dv, nbrs, probs, source_nodes,
                foggy.UniformInterval(num_walkers), time_points, num_steps, dynamic, lb_view=lv)
        numpy.savez(filename, activity=activity, hits=removed, capacity=dynamic)

# <codecell>

print "deletory_varied_uniform_random_walk_degree_capacity"
for k in capacity_factors:
    dynamic = capacity * k
    print dynamic.sum()
    filename = os.path.join(base_dir,
            "deletory_varied_uniform_random_walk_degree_capacity_%d_%s.npz" %\
            (int(dynamic.sum()), unique_run))
    if not os.path.exists(filename):
        (activity, removed) = foggy.deletory_parallel_march(dv, nbrs, probs, source_nodes,
                foggy.UniformInterval(num_walkers, 2 * num_walkers), time_points, num_steps,
                dynamic, lb_view=lv)
        numpy.savez(filename, activity=activity, hits=removed, capacity=dynamic)

# <codecell>

print "buffered_uniform_random_walk_degree_capacity"
for k in capacity_factors:
    dynamic = capacity * k
    print dynamic.sum()
    filename = os.path.join(base_dir,
            "buffered_uniform_random_walk_degree_capacity_%d_%s.npz" %\
            (int(dynamic.sum()), unique_run))
    if not os.path.exists(filename):
        (activity, backlog) = foggy.buffered_parallel_march(dv, nbrs, probs, source_nodes,
                foggy.UniformInterval(num_walkers), time_points, num_steps, dynamic, lb_view=lv)
        numpy.savez(filename, activity=activity, hits=backlog, capacity=dynamic)

# <codecell>

print "buffered_varied_uniform_random_walk_degree_capacity"
for k in capacity_factors:
    dynamic = capacity * k
    print dynamic.sum()
    filename = os.path.join(base_dir,
            "buffered_varied_uniform_random_walk_degree_capacity_%d_%s.npz" %\
            (int(dynamic.sum()), unique_run))
    if not os.path.exists(filename):
        (activity, backlog) = foggy.buffered_parallel_march(dv, nbrs, probs, source_nodes,
                foggy.UniformInterval(num_walkers, 2 * num_walkers), time_points, num_steps,
                dynamic, lb_view=lv)
        numpy.savez(filename, activity=activity, hits=backlog, capacity=dynamic)


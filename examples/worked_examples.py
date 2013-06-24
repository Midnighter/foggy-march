# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # Random Walk Statistics

# <codecell>

import os
import numpy
import networkx as nx

# <codecell>

import walkers

# <codecell>

base_dir = "results"
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

filename = os.path.join(base_dir, "network.pkl")
if not os.path.exists(filename):
    network = nx.barabasi_albert_graph(int(1E03), 3)
#    network = nx.scale_free_graph(int(1E03))
#    network = nx.fast_gnp_random_graph(int(1E03), 0.01)
    nx.write_gpickle(network, filename)
else:
    network = nx.write_gpickle(filename)

if network.is_directed():
    print "directed network with:"
else:
    print "undirected network with:"
print "\t", len(network), "nodes"
print "\t", network.size(), "links"

# <codecell>

# TODO: give prepare_uniform_walk an argument to supply a map
(probs, nbrs, indices) = walkers.prepare_uniform_walk(network)
filename = os.path.join(base_dir, "node2id.pkl")
if not os.path.exists(filename):
    nx.write_gpickle(indices, filename)

# <codecell>

from IPython.parallel import Client

# <codecell>

rc = Client()

# <codecell>

dv = rc.direct_view()
lv = rc.load_balanced_view()

# <codecell>

dv.execute("import walkers", block=True);
dv.execute("import numpy", block=True);

# <codecell>


# <markdowncell>

# First random walk with a constant number of walkers, that is, one for each node in the network and over 100 time steps. The walkers perform ten times the number of nodes steps.

# <codecell>

filename = os.path.join(base_dir, "uniform_random_walk.npy")
if not os.path.exists(filename):
    activity = walkers.parallel_march(dv, nbrs, probs, range(len(nbrs)), walkers.UniformInterval(len(network)),
            100, len(network) * 10, lb_view=lv)
    numpy.save(filename, activity)

# <codecell>

filename = os.path.join(base_dir, "uniform_random_walk_cut_transient.npy")
if not os.path.exists(filename):
    activity = walkers.parallel_march(dv, nbrs, probs, range(len(nbrs)), walkers.UniformInterval(len(network)),
            100, len(network) * 10, transient=1000, lb_view=lv)
    numpy.save(filename, activity)

# <markdowncell>

# Second random walk with a significant variation of the number of walkers in each time step, i.e., the variation is twice the mean.

# <codecell>

filename = os.path.join(base_dir, "varied_uniform_random_walk.npy")
if not os.path.exists(filename):
    activity = walkers.parallel_march(dv, nbrs, probs, range(len(nbrs)), walkers.UniformInterval(len(network), len(network) * 2),
            100, len(network) * 10, lb_view=lv)
    numpy.save(filename, activity)

# <codecell>

filename = os.path.join(base_dir, "varied_uniform_random_walk_cut_transient.npy")
if not os.path.exists(filename):
    activity = walkers.parallel_march(dv, nbrs, probs, range(len(nbrs)), walkers.UniformInterval(len(network), len(network) * 2),
            100, len(network) * 10, transient=1000, lb_view=lv)
    numpy.save(filename, activity)

# <markdowncell>

# Third random walk with no variation of the number of walkers in each time step but with a degree-dependent value for each node that should lead to a power-law scaling with $\alpha = 0.65$.

# <codecell>

filename = os.path.join(base_dir, "uniform_random_walk_mu.npy")
if not os.path.exists(filename):
    activity = walkers.parallel_march(dv, nbrs, probs, range(len(nbrs)), walkers.UniformInterval(len(network)),
            100, len(network) * 10, assessor=walkers.DegreeDependentValue(network, indices, mu=walkers.compute_mu(0.65)), lb_view=lv)
    numpy.save(filename, activity)

# <codecell>

filename = os.path.join(base_dir, "uniform_random_walk_mu_cut_transient.npy")
if not os.path.exists(filename):
    activity = walkers.parallel_march(dv, nbrs, probs, range(len(nbrs)), walkers.UniformInterval(len(network)),
            100, len(network) * 10, assessor=walkers.DegreeDependentValue(network, indices, mu=walkers.compute_mu(0.65)),
            transient=1000, lb_view=lv)
    numpy.save(filename, activity)

# <codecell>

filename = os.path.join(base_dir, "varied_uniform_random_walk_mu.npy")
if not os.path.exists(filename):
    activity = walkers.parallel_march(dv, nbrs, probs, range(len(nbrs)), walkers.UniformInterval(len(network), len(network) * 2),
            100, len(network) * 10, assessor=walkers.DegreeDependentValue(network, indices, mu=walkers.compute_mu(0.65)), lb_view=lv)
    numpy.save(filename, activity)

# <codecell>

filename = os.path.join(base_dir, "varied_uniform_random_walk_mu_cut_transient.npy")
if not os.path.exists(filename):
    activity = walkers.parallel_march(dv, nbrs, probs, range(len(nbrs)), walkers.UniformInterval(len(network), len(network) * 2),
            100, len(network) * 10, assessor=walkers.DegreeDependentValue(network, indices, mu=walkers.compute_mu(0.65)),
            transient=1000, lb_view=lv)
    numpy.save(filename, activity)


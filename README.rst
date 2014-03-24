===========
Foggy March
===========


Outline
-------

A module for different types of random walks on any directed or undirected network.
See the contained notebook for an example use. It implements random walker
models presented in [\ 1_ - 4_] using IPython's parallel-processing. The module
also provides functions to evaluate internal dynamics vs external fluctuations
as defined in [\ 2_].

Requirements
------------

* networkx_
* numpy_

.. _networkx: http://networkx.github.com/
.. _numpy: http://www.numpy.org/

Optional
~~~~~~~~

* IPython_ and 0MQ for parallel-processing. An older version that uses local
  ``multiprocessing`` is available, too.
* matplotlib_ for plotting
* tables_ for storing results

.. _IPython: http://ipython.org/
.. _matplotlib: http://matplotlib.org/
.. _tables: http://www.pytables.org/

Also take a look at the ``requirements.txt`` and ``opt-requirements.txt`` files
that you can use with ``pip`` to install the necessary packages.

    pip install -r <file>

Authors
-------

* Beber, Moritz Emanuel

References
----------
.. [1] De Menezes, M. A., and A.-L. Barabási.
       “Fluctuations in Network Dynamics.”
       *Phys. Rev. Lett.* 92.2 (2004): 028701.
.. [2] De Menezes, M. A., and A.-L. Barabási.
       “Separating Internal and External Dynamics of Complex Systems.”
       *Phys. Rev. Lett.* 93.6 (2004): 068701.
.. [3] Eisler, Z. et al.
       “Multiscaling and Non-universality in Fluctuations of Driven Complex Systems.”
       *EPL (Europhysics Letters)* 69.4 (2005): 664. Print.
.. [4] Eisler, Zoltán, and János Kertész.
       “Random Walks on Complex Networks with Inhomogeneous Impact.”
       *Phys. Rev. E* 71.5 (2005): 057104.


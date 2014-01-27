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


__all__ = ["compute_mu", "internal_dynamics_external_fluctuations"]


import numpy


def compute_mu(alpha, nu=1.0):
    """
    In [\ 1_] the power-law exponent $\alpha$ is determined by the values of $\mu$
    and $\nu$. This function computes $\mu$ such that a given exponent $\alpha$
    can be recovered.

    $\alpha$ is determined in the following way:
    \begin{equation}
        \alpha = \dfrac{1}{2} \left( 1 + \dfrac{\dfrac{\mu}{\nu}}{\dfrac{\mu}{\nu} + 1} \right).
    \end{equation}

    According to Mathematica, the solution for $\mu$ is:
    \begin{equation}
        \mu = \dfrac{\nu - 2 \alpha \nu}{2 \left( \alpha - 1 \right)}.
    \end{equation}

    References
    ----------
    .. [1] Eisler, Z., and J. Kertész.
           “Random Walks on Complex Networks with Inhomogeneous Impact.”
           *Phys. Rev. E* 71, no. 5 (May 2005): 057104. doi:10.1103/PhysRevE.71.057104.
    """
    alpha = float(alpha)
    nu = float(nu)
    return (nu - (2.0 * alpha * nu)) / (2.0 * (alpha - 1.0))

def internal_dynamics_external_fluctuations(activity):
    """
    Assess the internal dynamics and external fluctuations of a complex system.

    Parameters
    ----------
    activity: numpy.array
        Two dimensional array, where the first dimension corresponds to system
        elements and the second to observations of their activity.

    Returns
    -------
    Two arrays for the standard deviation of the internal and external
    fluctuations of components, respectively.

    References
    ----------
    """
    internal = numpy.zeros(activity.shape, dtype=float)
    external = numpy.zeros(activity.shape, dtype=float)
    sum_time = activity.sum(axis=1)
    sum_elem = activity.sum(axis=0)
    # equation (2)
    fraction = sum_time / activity.sum()
    # equation (3) & (4)
    for i in xrange(activity.shape[0]):
        for t in xrange(activity.shape[1]):
            external[i, t] = fraction[i] * sum_elem[t]
            internal[i, t] = activity[i, t] - external[i, t]
    return (internal.std(axis=1, ddof=1), external.std(axis=1, ddof=1))


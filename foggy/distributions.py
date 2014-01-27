# -*- coding: utf-8 -*-


"""
========================
Random Walks on Networks
========================

:Author:
    Moritz Emanuel Beber
:Date:
    2014-01-27
:Copyright:
    Copyright |c| 2014, Jacobs University Bremen gGmbH, all rights reserved.
:File:
    walkers.py

.. |c| unicode:: U+A9
"""


__all__ = ["UniformInterval"]


import numpy


class UniformInterval(object):
    """
    Instances of UniformInterval can be called without argument to yield a
    natural number from a uniform random distribution on a pre-specified
    interval (cut off at zero).
    """

    def __init__(self, mid_point, variation=0, **kw_args):
        """
        At instantiation the mean of the interval and and the uniform variation
        around that mean are determined.

        Parameters
        ----------
        mid_point: int
            The mean of the uniform random variable.
        variation: int (optional)
            Determines the interval, it is from mid_point - variation or zero to
            mid_point + variation.
        """
        super(UniformInterval, self).__init__(**kw_args)
        self.rand_int = numpy.random.random_integers
        self.mid_point = int(mid_point)
        assert self.mid_point >= 0
        self.variation = int(variation)
        assert self.variation >= 0
        self.mini = self.mid_point - self.variation
        # This definition leads to a potential accumulation of zero values and
        # thus a non-uniform probability density function.
        # A uniform PDF over the interval is guaranteed by:
#        self.mini = max(self.mid_point - self.variation, 0)
        # but with a changed mean and variance
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
        return max(self.rand_int(self.mini, self.maxi), 0)


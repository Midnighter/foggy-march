================================
Foggy Cluster Queue Instructions
================================


You need at least 5 terminal windows, so using ``tmux`` or ``screen`` is
recommended.

1. Start the beanstalkd queue, e.g., ``beanstalkd -l 127.0.0.1 -V``.
2. Start the job supplier ``python simulations.py supply``.
3. Start an IPython cluster ``ipcluster start``.
4. Start the job consumers ``python simulations.py consume``.
5. Start the results handler ``python simulations.py handle``.
6. Use ``python simulations.py info`` for some basic queue statistics.

For each command first run it with ``-h`` to see appropriate command line flags.

Enjoy!


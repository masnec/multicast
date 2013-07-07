from threading import Timer
from topo import Topo
import time

topo = Topo()
topo.load_topo("../mininet/topo.json")
topo.cplex_dump_topo("cplex.in")


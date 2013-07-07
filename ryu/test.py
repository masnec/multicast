from threading import Timer
from topo import Topo
import time

topo = Topo()
# Load network topology
topo.load_topo("../mininet/topo.json")

# Update flow info using JSON format
topo.update_flow("flow.json")
print topo.sw_outport

# -- For CPLEX -->

# Generate CPLEX input
topo.cplex_generate_input("cplex.in")

# Read CPLEX output and update flow info
topo.cplex_read_output("cplex.out")

# <--

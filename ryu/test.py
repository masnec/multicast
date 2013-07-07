from threading import Timer
from topo import Topo
import time

topo = Topo()

# Set Camera descriptor K
topo.K = 2

# Load network topology
topo.load_topo("../mininet/topo.json")

# Update flow info using JSON format
topo.update_flow("flow.json")
## check result
print "Check flow info from JSON format"
print topo.flow

# -- For CPLEX -->

# Generate CPLEX input
topo.cplex_generate_input("cplex.in")

# Read CPLEX output and update flow info
topo.cplex_read_output("cplex.out")
## check result
print "Check flow info from cplex output"
print topo.flow
# Update flow with current flow data (ex: after read from cplex)
topo.update_flow()
# <--

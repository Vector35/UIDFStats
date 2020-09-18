#!/usr/bin/env python3

from binaryninja import *
import matplotlib.pyplot as plt
import copy

# filenames = ["/Users/peterl/CHESS/testbed_release/ta3_examples/bryant/challenge_bin/build/bryant.bin"]
# # "/Users/peterl/CHESS/testbed_release/ta3_examples/bryant/challenge_bin/build/bryant.bin", "/Users/peterl/CHESS/testbed_release/ta3_examples/bryant/challenge_bin/build/nevins.bndb", "/Users/peterl/CHESS/testbed_release/ta3_examples/bryant/challenge_bin/build/adams.bin", "/Users/peterl/CHESS/testbed_release/ta3_examples/bryant/challenge_bin/build/jackson.bin"]
filenames = ["/Users/peterl/CHESS/testbed_release/ta3_examples/bryant/challenge_bin/build/bryant.bin",
    "/Users/peterl/CHESS/testbed_release/ta3_examples/nevins/challenge_bin/build/nevins.bndb",
    "/Users/peterl/CHESS/testbed_release/ta3_examples/adams/challenge_bin/build/adams.bin",
    "/Users/peterl/CHESS/testbed_release/ta3_examples/jackson/challenge_bin/build/jackson.bin"
]
def get_counts(func):
    # remove nodes with one incoming and one outgoing edge
    toremove = []
    for node in func.basic_blocks:
        if len(node.incoming_edges) == 1 and len(node.outgoing_edges) == 1:
            toremove.append(node)
    edges = set()
    for node in func.basic_blocks:
        if node not in toremove:
            edges.update(node.outgoing_edges)

    return sum(1 for i in func.instructions), len(func.basic_blocks) - len(toremove), len(edges)

def set_values(func):
    for i in [i for i in func.mlil.instructions if i.operation == MediumLevelILOperation.MLIL_IF]:
        vars_read = i.vars_read
        if len(vars_read) < 1:
            continue
        var = vars_read[0]
        defs = func.mlil.get_var_definitions(var)
        if len(defs) < 1:
            continue
        def_site = defs[0].address
        func.set_user_var_value(var, def_site, PossibleValueSet.constant(0))
    bv.update_analysis_and_wait()

def stats(bv, inst_threshold=100, node_threshold=2):
    instruction_count = [0, 0, 0, 0, 0]
    node_count = [0, 0, 0, 0, 0]
    edge_count = [0, 0, 0, 0, 0]
    funcs = [func for func in bv.functions if sum(1 for i in func.instructions) >= inst_threshold and len(func.basic_blocks) >= node_threshold]
    func_count = len(funcs)

    for func in funcs:
        func_types = [func, func.llil, func.mlil, func.hlil, None]
        for i, func_type in enumerate(func_types):
            if func_type is None:
                set_values(func)
                func_type = func.hlil

            insts, nodes, edges = get_counts(func_type)
            instruction_count[i] += insts
            node_count[i] += nodes
            edge_count[i] += edges

    return (func_count, instruction_count, node_count, edge_count)

total_func_count = 0
average_instruction_count = [0, 0, 0, 0, 0]
average_node_count = [0, 0, 0, 0, 0]
average_edge_count = [0, 0, 0, 0, 0]

for filename in filenames:
    with open_view(filename) as bv:
        func_count, instruction_count, node_count, edge_count = stats(bv)
        total_func_count += func_count
        for i in range(len(average_instruction_count)):
            average_instruction_count[i] += instruction_count[i]
            average_node_count[i] += node_count[i]
            average_edge_count[i] += edge_count[i]

for i in range(len(average_instruction_count)):
    average_instruction_count[i] /= total_func_count
    average_node_count[i] /= total_func_count
    average_edge_count[i] /= total_func_count

average_complexity = []

average_node = copy.copy(average_node_count)
average_edge = copy.copy(average_edge_count)
average_instruction = copy.copy(average_instruction_count)

for i in range(len(average_instruction)):
    average_complexity.append(average_edge[i] - average_node[i] + 2)

# Now calculate the percentage drop of complexity from Assembly
for i in range(len(average_instruction) - 1, -1, -1):
    average_instruction[i] = round(average_instruction[i] / average_instruction[0], 2)
    average_complexity[i] = round(average_complexity[i] / average_complexity[0], 2)
    average_node[i] = round(average_node[i] / average_node[0], 2)
    average_edge[i] = round(average_edge[i] / average_edge[0], 2)
print(f"Percentage Reduction in average edge complexity:        {average_edge}" )
print(f"Percentage Reduction in average node complexity:        {average_node}" )
print(f"Percentage Reduction in average instruction complexity: {average_instruction}" )
print(f"Percentage Reduction in average cyclomatic complexity:  {average_complexity}" )

x = ["Assembly", "LowLevelIL", "MediumLevelIL", "HighLevelIL", "  HighLevelIL w/ UIDF . "]
plt.plot(x, average_instruction, label="Instruction Count")
plt.plot(x, average_node, label="Node Count")
plt.plot(x, average_edge, label="Edge Count")
plt.plot(x, average_complexity, label="Cyclomatic Complexity")
plt.xticks(rotation=30)
plt.title('Reduction in complexity of')

plt.legend()

plt.show()
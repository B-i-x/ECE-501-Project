import re
import sys

# Usage: python dbml_to_dot.py docs/ERD.dbml > docs/ERD.dot

dbml_path = sys.argv[1]

tables = {}
edges = []

table_re = re.compile(r"Table\s+(\w+)\s*{")
col_re = re.compile(r"(\w+)\s+[\w\(\)]+.*")
fk_re  = re.compile(r"ref:\s*>\s*(\w+)\.(\w+)")

current = None

with open(dbml_path) as f:
    for line in f:
        line_strip = line.strip()

        m = table_re.match(line_strip)
        if m:
            current = m.group(1)
            tables[current] = []
            continue

        if current:
            # foreign keys
            m2 = fk_re.search(line_strip)
            if m2:
                ref_table = m2.group(1)
                edges.append((current, ref_table))

            # columns (optional: for completeness)
            m3 = col_re.match(line_strip)
            if m3:
                col = m3.group(1)
                tables[current].append(col)

            if line_strip == "}":
                current = None

# Emit GraphViz
print("digraph G {")
print('  graph [overlap=false, splines=true];')
print('  node  [shape=box, style="rounded,filled", fillcolor=white];')

# nodes
for t in tables:
    print(f'  "{t}";')

# edges
for src, dst in edges:
    print(f'  "{src}" -> "{dst}";')

print("}")

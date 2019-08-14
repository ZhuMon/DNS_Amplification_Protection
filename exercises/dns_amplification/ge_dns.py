import random
import sys

# N = raw_input()
N = int(sys.argv[1])
print(N)
only_query = [847,862,863,866,1302,1303,1447,1462]

for i in range(0, int(N)):
    out = random.randint(0,1471)
    while out in only_query:
        out = random.randint(0,1471)
    wait = random.uniform(0,1) if float(sys.argv[2]) == -1 else float(sys.argv[2])
    print wait
    print out

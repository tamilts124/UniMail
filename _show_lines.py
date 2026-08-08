import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
start = int(sys.argv[1]) - 1
end   = int(sys.argv[2])
lines = open(sys.argv[3], encoding='utf-8').readlines()
for i, l in enumerate(lines[start:end], start+1):
    print(f"{i} {l}", end='')

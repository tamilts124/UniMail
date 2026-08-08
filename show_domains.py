lines = open('domains_list.txt', encoding='utf-8').readlines()
for i in range(195, 240):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")

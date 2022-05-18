import dis

division = len(dis.opname) // 2
for i in range(division):
    print('{}: {} '.format(str(i).rjust(3), dis.opname[i]).ljust(30) + '{}: {} '.format(str(i + division).rjust(3), dis.opname[i + division]))
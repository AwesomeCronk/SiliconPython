import dis

division = len(dis.opname) // 2
for i in range(division):
    print('{} ({}): {} '.format(str(i).rjust(3), hex(i)[2:], dis.opname[i]).ljust(35) + '{} ({}): {} '.format(str(i + division).rjust(3), hex(i + division)[2:], dis.opname[i + division]))
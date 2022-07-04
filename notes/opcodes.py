import dis


for i in range(len(dis.opname)):
    print('{} ({}): {} '.format(str(i).rjust(3), hex(i)[2:], dis.opname[i]).ljust(35))
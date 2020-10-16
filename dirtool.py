import sys, os, hashlib


def usage():
    print('Usage (1): python3 dirtool.py compare folder1 folder2', file=sys.stderr)
    print('Usage (2): python3 dirtool.py hash folder [>output.txt]', file=sys.stderr)
    print('Usage (2a): python3 dirtool.py hash folder -o output.txt  # output is UTF-8 encoded', file=sys.stderr)
    print('Usage (3): python3 dirtool.py dupfind folder', file=sys.stderr)
    print('Usage (4): python3 dirtool.py hash-compare out1.txt out2.txt', file=sys.stderr)
    print('Usage (4a): python3 dirtool.py hash-compare out1.txt out2.txt -o output.txt  # output is UTF-8 encoded', file=sys.stderr)


def check_argv(min):
    if len(sys.argv) < min:
        usage()
        sys.exit(1)


def addentry(d, fname, checksum):
    if checksum in d.keys():
        d[checksum].append(fname)
    else:
        d[checksum] = [fname]


def traverse(folder, d):
    for root, subdirs, files in os.walk(folder):
        if root.endswith('/@eaDir'):  # Synology DSM creates folders with derived data
            continue
        for f in files:
            if f == '.DS_Store':  # macOS creates hidden files
                continue
            fullname = os.path.join(root, f)
            m = hashlib.sha256()
            if os.path.islink(fullname):
                m.update(os.readlink(fullname).encode('utf-8'))
            else:
                with open(fullname, 'rb') as fdata:
                    while True:
                        buf = fdata.read(1048576)
                        if not buf:
                            break
                        m.update(buf)
            checksum = m.hexdigest()

            addentry(d, fullname, checksum)


def compare(d1, d2):
    print('Comparing {0} and {1} records'.format(len(d1), len(d2)))
    found, notfound = 0, 0
    for k1 in d1.keys():
        if k1 in d2.keys():
            found += 1
        else:
            notfound += 1

    k2notfound = 0
    notfoundlist = []
    for k2 in d2.keys():
        if k2 not in d1.keys():
            k2notfound += 1
            elem = d2[k2][0]
            if elem[-1:] == '\n':
                elem = elem[:-1]
            notfoundlist += [elem]

    print('{0} found, {1} d1 keys not found in d2'.format(found, notfound))
    print('{0} keys in d2 not found in d1'.format(k2notfound))
    print('\n'.join(notfoundlist))


# same as compare but outputs to a file
# under Windows redirecting output to a file may result in encoding error
# even if we change code page to 65001 (`chcp 65001`) the error persists
# feel free to refactor with compare if u have some time
def compare2(d1, d2, fname):
    f = open(fname, 'w', encoding='utf-8')
    f.write('Comparing {0} and {1} records'.format(len(d1), len(d2)))
    found, notfound = 0, 0
    for k1 in d1.keys():
        if k1 in d2.keys():
            found += 1
        else:
            notfound += 1

    k2notfound = 0
    notfoundlist = []
    for k2 in d2.keys():
        if k2 not in d1.keys():
            k2notfound += 1
            elem = d2[k2][0]
            if elem[-1:] == '\n':
                elem = elem[:-1]
            notfoundlist += [elem]

    f.write('{0} found, {1} d1 keys not found in d2\n'.format(found, notfound))
    f.write('{0} keys in d2 not found in d1\n'.format(k2notfound))
    f.write('\n'.join(notfoundlist))
    f.write('\n')
    f.close()


def dupfind(d):
    for k in d.keys():
        if len(d[k]) > 1:
            for e in d[k]:
                print(k, e)


def output(d):
    for k in d.keys():
        for e in d[k]:
            print(k, e)


# see comment in compare2
def output2(d, fname):
    fout = open(fname, 'w', encoding='utf-8')
    for k in d.keys():
        for e in d[k]:
            fout.write(k)
            fout.write(' ')
            fout.write(e)
            fout.write('\n')
    fout.close()


def load(fname):
    d = {}
    with open(fname, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for l in lines:
        pos = l.find(' ')
        checksum = l[:pos]
        name = l[pos + 1:]
        addentry(d, name, checksum)
    return d


check_argv(2)

cmd = sys.argv[1]
if cmd == 'compare':
    check_argv(4)
    folder1, folder2 = sys.argv[2], sys.argv[3]
    dict1, dict2 = {}, {}
    traverse(folder1, dict1)
    traverse(folder2, dict2)
    compare(dict1, dict2)
elif cmd == 'hash':
    check_argv(3)
    folder = sys.argv[2]
    dictf = {}
    traverse(folder, dictf)
    if len(sys.argv) >= 5 and sys.argv[3] == '-o':
        output2(dictf, sys.argv[4])
    else:
        output(dictf)
elif cmd == 'dupfind':
    check_argv(3)
    folder = sys.argv[2]
    dictf = {}
    traverse(folder, dictf)
    dupfind(dictf)
elif cmd == 'hash-compare':
    check_argv(4)
    file1, file2 = sys.argv[2], sys.argv[3]
    dict1 = load(file1)
    dict2 = load(file2)
    if len(sys.argv) >= 6 and sys.argv[4] == '-o':
        compare2(dict1, dict2, sys.argv[5])
    else:
        compare(dict1, dict2)
else:
    usage()
    sys.exit(1)



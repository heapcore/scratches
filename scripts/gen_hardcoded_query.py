#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

def sql_split(text):
    flag = True
    res = []
    m = 0
    brk = 0
    n = len(text)
    for i in range(m, n):
        if text[i] == '\'':
            flag = not flag
        elif text[i] == '(' and flag:
            brk += 1
        elif text[i] == ')' and flag:
            brk -= 1
        elif text[i] == ',' and flag and brk == 0:
            res.append(text[m:i])
            m = i + 1
    res.append(text[m:n])
    return res

def main():
    if len(sys.argv) >= 2:
        argc = len(sys.argv)
        fname = sys.argv[1]
        cnt = 0
        n = 0
        res = []

        f = open(fname, 'r')
        lines = f.readlines()
        lines = [l for l in lines if "values" in l]
        f.close()

        names_add = []
        values_add = []
        if argc > 2:
            for i in range(2, argc):
                names_add.append(sys.argv[i].split(':')[0])
                values_add.append(sys.argv[i].split(':')[1])

        for l in lines:
            if cnt == 0:
                s = l.split("values")[0]
                names = s[s.find("(")+1:s.rfind(")")]
                names = sql_split(names) + names_add
                n = len(names)

            s = l.split("values")[1]
            values = s[s.find("(")+1:s.rfind(")")]
            values = sql_split(values) + values_add
            s = 'SELECT '
            if cnt == 0:
                for i in range(n):
                    s = s + '{0} AS {1}, '.format(values[i], names[i])
            else:
                for i in range(n):
                    print i
                    print l
                    print values
                    s = s + '{0}, '.format(values[i])

            s = s[:-2]
            s = s + ' FROM dual'
            res.append(s)

            cnt += 1

        res = '\nUNION ALL\n'.join(res)

        if fname.endswith(".sql"):
            fname = fname[0:len(fname)-4] + '_output.sql'
        else:
            fname = fname + '.sql'

        f = open(fname, 'w')
        f.write(res)
        f.close()

    else:
        print "Too less arguments"

if __name__ == '__main__':
    main()

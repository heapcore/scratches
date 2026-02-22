def lists_merge(a, b):
    res = []
    n, i = len(a), 0
    m, j = len(b), 0
    while i < n and j < m:
        if a[i] < b[j]:
            res.append(a[i])
            i += 1
        else:
            res.append(b[j])
            j += 1

    if i < n:
        res.extend(a[i:n])
    if j < m:
        res.extend(b[j:m])

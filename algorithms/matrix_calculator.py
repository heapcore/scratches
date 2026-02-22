from decimal import Decimal
from functools import partial


def matrix_determinant(a, n=None):
    n = n or len(a)
    if n == 1:
        return a[0][0]
    if n == 2:
        return a[0][0] * a[1][1] - a[0][1] * a[1][0]
    else:
        return sum(a[0][j] * matrix_cofactor(a, 0, j) for j in range(n))


def matrix_minor(a, i, j):
    result = [
        [elem for idx2, elem in enumerate(row) if idx2 != j]
        for idx1, row in enumerate(a)
        if idx1 != i
    ]
    return matrix_determinant(result)


def matrix_cofactor(a, i, j):
    return matrix_minor(a, i, j) * (-1) ** (i + j)


def matrix_inverse(a, n=None):
    det = matrix_determinant(a)
    if det == 0:
        return None
    else:
        n = n or len(a)
        cofactors = [[matrix_cofactor(a, i, j) for j in range(n)] for i in range(n)]
        cofactors = matrix_transpose(cofactors, 1)
        return [[elem / det for elem in row] for row in cofactors]


def matrix_sum(a, b, n=None, m=None):
    n = n or len(a)
    m = m or len(a[0])
    result = [[0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            result[i][j] = a[i][j] + b[i][j]
    return result


def matrix_mul_const(a, c, n=None, m=None):
    n = n or len(a)
    m = m or len(a[0])
    result = [[0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            result[i][j] = c * a[i][j]
    return result


def matrix_mul(a, b, n=None, m=None, p=None):
    n = n or len(a)
    m = m or len(a[0])
    p = p or len(b[0])
    result = [[0] * p for _ in range(n)]
    for i in range(n):
        for j in range(p):
            for k in range(m):
                result[i][j] += a[i][k] * b[k][j]
    return result


def matrix_transpose(a, t, n=None, m=None):
    n = n or len(a)
    m = m or len(a[0])
    result = []
    if t == 1:
        result = [[0] * n for _ in range(m)]
        for i in range(n):
            for j in range(m):
                result[i][j] = a[j][i]
    elif t == 2:
        result = [[0] * n for _ in range(m)]
        for i in range(n):
            for j in range(m):
                result[i][j] = a[m - 1 - j][n - 1 - i]
    elif t == 3:
        result = [list(reversed(row)) for row in a]
    elif t == 4:
        result = [row.copy() for row in reversed(a)]

    return result


def num(n):
    return Decimal(n)


def num_to_str(n, precision=None):
    if precision:
        format_str = "{0:." + str(precision) + "f}"
        s = format_str.format(n)
    else:
        s = str(n)
    s = s.rstrip("0").rstrip(".") if "." in s else s
    s = s if s != "-0" else "0"
    return s


def matrix_read():
    print("Enter size of matrix:")
    n, m = map(int, input().split())
    matrix = []
    print("Enter matrix elements:")
    for _ in range(n):
        matrix.append(list(map(num, input().split()[:m])))
    return n, m, matrix


def multiplier_read():
    print("Enter multiplier:")
    return num(input())


def matrix_write(matrix, precision=None):
    print("The result is:")
    for row in matrix:
        if precision:
            num_to_str_local = partial(num_to_str, precision=precision)
        else:
            num_to_str_local = num_to_str
        print(" ".join(map(num_to_str_local, row)))


def matrix_calculator():
    while True:
        print(
            "1. Add matrices\n"
            "2. Multiply matrix to a constant\n"
            "3. Multiply matrices\n"
            "4. Transpose matrix\n"
            "5. Calculate a determinant\n"
            "6. Inverse matrix\n"
            "0. Exit\n"
        )
        i = int(input())
        print(f"Your choice: {i}")
        if i == 0:
            break
        elif i == 1:
            n1, m1, a = matrix_read()
            n2, m2, b = matrix_read()
            if n1 == n2 and m1 == m2:
                result = matrix_sum(a, b)
                matrix_write(result)
            else:
                print("ERROR")
        elif i == 2:
            n, m, a = matrix_read()
            c = multiplier_read()
            result = matrix_mul_const(a, c)
            matrix_write(result)
        elif i == 3:
            n, m1, a = matrix_read()
            m2, k, b = matrix_read()
            if m1 == m2:
                result = matrix_mul(a, b)
                matrix_write(result)
            else:
                print("ERROR")
        elif i == 4:
            print(
                "1. Main diagonal\n"
                "2. Side diagonal\n"
                "3. Vertical line\n"
                "4. Horizontal line\n"
            )
            t = int(input())
            print(f"Your choice: {t}")
            n, m, a = matrix_read()
            result = matrix_transpose(a, t)
            matrix_write(result)
        elif i == 5:
            n, m, a = matrix_read()
            if m == n:
                result = matrix_determinant(a)
                print(result)
            else:
                print("ERROR")
        elif i == 6:
            n, m, a = matrix_read()
            success = True
            if m == n:
                result = matrix_inverse(a)
                if result:
                    matrix_write(result, precision=4)
                else:
                    success = False
            else:
                success = False

            if not success:
                print("ERROR")


if __name__ == "__main__":
    matrix_calculator()

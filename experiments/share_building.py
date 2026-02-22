def read_data():
    n = int(input())
    parts = []

    for i in range(n):
        a = float(input())
        parts.append(a)

    return parts


def process_parts(parts):
    parts_sum = 0
    percentages = []
    for part in parts:
        parts_sum += part

    for part in parts:
        percentages.append(round(part / parts_sum, 3))

    return percentages


def write_data(parts):
    for part in parts:
        print("{0:.3f}".format(part))


def main():
    parts = read_data()
    percentages = process_parts(parts)
    write_data(percentages)


if __name__ == "__main__":
    main()

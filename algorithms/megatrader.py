from collections import namedtuple


def read_data():
    numbers = input().split()
    n = int(numbers[0])
    m = int(numbers[1])
    total_money = int(numbers[2])

    bonds = []
    weights = []
    values = []

    Bond = namedtuple("Bond", ["day", "name", "price", "amount"])

    standard_profit = 1030

    while True:
        bond = input()
        if not bond:
            break
        data = bond.split()
        bond = Bond(
            day=int(data[0]), name=data[1], price=float(data[2]), amount=int(data[3])
        )
        weight = int(bond.price * bond.amount * 10)
        value = (n - bond.day + standard_profit) * bond.amount - weight
        bonds.append(bond)
        weights.append(weight)
        values.append(value)

    return bonds, weights, values, total_money


def solve_knapsack(bonds_count, weights, values, total_money):
    knapsack_matrix = [[0] * (total_money + 1) for _ in range(bonds_count + 1)]

    for i in range(1, bonds_count + 1):
        for w in range(1, total_money + 1):
            if weights[i - 1] <= w:
                knapsack_matrix[i][w] = max(
                    values[i - 1] + knapsack_matrix[i - 1][w - weights[i - 1]],
                    knapsack_matrix[i - 1][w],
                )
            else:
                knapsack_matrix[i][w] = knapsack_matrix[i - 1][w]

    max_value = knapsack_matrix[bonds_count][total_money]

    bonds_sum = max_value
    bonds_indexes = []
    for i in range(bonds_count, 0, -1):
        if bonds_sum != knapsack_matrix[i - 1][total_money]:
            bonds_indexes.append(i - 1)

            bonds_sum = bonds_sum - values[i - 1]
            if bonds_sum <= 0:
                break
            total_money = total_money - weights[i - 1]

    return bonds_indexes, max_value


def write_data(bonds, bonds_indexes, max_value):
    print(max_value)
    for idx in reversed(bonds_indexes):
        print(" ".join(map(str, bonds[idx])))
    print("")


def main():
    bonds, weights, values, total_money = read_data()
    bonds_count = len(bonds)
    bonds_indexes, max_value = solve_knapsack(bonds_count, weights, values, total_money)
    write_data(bonds, bonds_indexes, max_value)


if __name__ == "__main__":
    main()

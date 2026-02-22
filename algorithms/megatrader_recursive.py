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
    def knapsack(bonds_count, weights, values, total_money):
        if bonds_count == 0 or total_money == 0:
            return 0

        if weights[bonds_count - 1] > total_money:
            return knapsack(bonds_count - 1, weights, values, total_money)
        else:
            return max(
                values[bonds_count - 1]
                + knapsack(
                    bonds_count - 1,
                    weights,
                    values,
                    total_money - weights[bonds_count - 1],
                ),
                knapsack(bonds_count - 1, weights, values, total_money),
            )

    return knapsack(bonds_count, weights, values, total_money)


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

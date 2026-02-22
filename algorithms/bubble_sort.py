def bubble(numbers):
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] > numbers[j]:
                numbers[i], numbers[j] = numbers[j], numbers[i]
    return numbers


if __name__ == "__main__":
    numbers = [1, 5, 7, 56, 1, 5, 11, 4, 5, 1, 7, 956, -15]
    res = bubble(numbers)
    print(res)
    print(id(res))
    print(numbers)
    print(id(numbers))

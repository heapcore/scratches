def shaker(numbers):
    left = 0
    right = len(numbers) - 1

    while left <= right:
        for i in range(left, right):
            if numbers[i] > numbers[i + 1]:
                numbers[i], numbers[i + 1] = numbers[i + 1], numbers[i]

        right -= 1

        for i in range(right, left, -1):
            if numbers[i - 1] > numbers[i]:
                numbers[i], numbers[i - 1] = numbers[i - 1], numbers[i]

        left += 1


if __name__ == "__main__":
    numbers = [1, 5, 7, 56, 1, 5, 11, 4, 5, 1, 7, 956, -15]
    shaker(numbers)
    print(numbers)

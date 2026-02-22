import requests


def f1(n):
    for i in range(n):
        print("network request", i)
        response = requests.get("https://example.com/some_big_file")


def f2(n):
    for i in range(n):
        print("read file", i)
        with open("some_big_file", "rb") as fl:
            fl.read()


f1(10)
f2(10)

# time time python3.7 single_thread.py
# real  0m34,378s
# user  0m0,818s
# sys   0m9,224s

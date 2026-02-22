from threading import Thread
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


t1 = Thread(target=f1, args=(10,))
t1.start()
t2 = Thread(target=f2, args=(10,))
t2.start()
t1.join()
t2.join()

# time time python3.7 multithread.py
# real  0m25,987s
# user  0m0,769s
# sys   0m9,014s

from multiprocessing import Process
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


p1 = Process(target=f1, args=(10,))
p1.start()
p2 = Process(target=f2, args=(10,))
p2.start()
p1.join()
p2.join()

# time time python3.7 multiprocess.py
# real  0m26,315s
# user  0m1,076s
# sys   0m8,741s

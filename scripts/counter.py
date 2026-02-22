import re
from collections import Counter


def count(file):
    f = open(file, "r")
    cnt = Counter()
    for line in f.readlines():
        words = line.split(" ")
        for word in words:
            word = re.sub("[^A-Za-z0-9]+", "", word).lower()
            cnt[word] += 1
    f.close()
    total_word_count = sum(cnt.values())
    for word, count in cnt.most_common(1000):
        print("{: < 6} {:<7.2%} {}".format(count, count / total_word_count, word))


count("test.txt")

# coding:utf-8
# 第23课 你真的懂python GIL吗？


import time
from threading import Thread
import sys
import threading


# 单线程版
def CountDown(n):
    while n > 0:
        n -= 1


if __name__ == "__main__":
    n = 100000000

    # start_time = time.perf_counter()
    # CountDown(n)
    # end_time = time.perf_counter()
    # print("n = {}，单线程版耗时{}".format(n, end_time - start_time))

    # 多线程版
    # start_time = time.perf_counter()
    # t1 = Thread(target=CountDown, args=[n // 4])
    # t2 = Thread(target=CountDown, args=[n // 4])
    # t3 = Thread(target=CountDown, args=[n // 4])
    # t4 = Thread(target=CountDown, args=[n // 4])
    # t1.start()
    # t2.start()
    # t3.start()
    # t4.start()
    # t1.join()
    # t2.join()
    # t3.join()
    # t4.join()
    # end_time = time.perf_counter()
    # print("n = {}，多线程版耗时{}".format(n, end_time - start_time))

    # 对象引用计数
    # a = []
    # b = a
    # print(sys.getrefcount(a))

    # 线程安全
    n = 0

    lock = threading.Lock()


    def foo():
        global n
        with lock:
            n += 1


    threads = []
    for i in range(100):
        t = threading.Thread(target=foo)
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print(n)

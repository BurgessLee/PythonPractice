# coding:utf-8
# 第29课 资源上下文，with

from contextlib import contextmanager


# 基于类的上下文管理器
class FileManager:
    def __init__(self, name, mode):
        print("__init__")
        self.name = name
        self.mode = mode

    def __enter__(self):
        print("__enter__")
        self.file = open(self.name, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("__exit__")
        if self.file:
            self.file.close()


class Foo:
    def __init__(self):
        print('__init__ called')

    def __enter__(self):
        print('__enter__ called')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('__exit__ called')
        if exc_type:
            print(f'exc_type: {exc_type}')
            print(f'exc_value: {exc_val}')
            print(f'exc_traceback: {exc_tb}')
            print('exception handled')
        return True


if __name__ == "__main__":
    # for x in range(10000000):
    #     f = open("test.txt", "w")
    #     f.write('hello')

    # for i in range(10000):
    #     with open("test.txt", "w") as f:
    #         f.write("hello")

    # with FileManager("text.txt", "w") as f:
    #     print("准备写文件")
    #     f.write("hello 2")

    # with Foo() as obj:
    #     raise Exception('exception raised').with_traceback(None)

    @contextmanager
    def file_manager(name, mode):
        try:
            f = open(name, mode)
            yield f
        finally:
            f.close()


    with file_manager('test.txt', 'w') as f:
        f.write('hello python')

    exit()

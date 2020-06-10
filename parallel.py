from multiprocessing import Pool
from time import sleep

def f(x):
    return x*x

##################################################

from threading import Thread
from queue import Queue
class BackgroundGenerator(Thread):
    "Transform a generator into a prefetched background thread."
    # https://github.com/justheuristic/prefetch_generator
    def __init__(self, generator, max_prefetch:int=1):
        """
        - generator: generator to wrap and prefetch in background
        - max_prefetch: How many items are prefetch at any moment of time.
        If max_prefetch is <= 0, the queue size is infinite.
        """
        super().__init__()
        self.queue, self.generator, self.daemon = Queue(max_prefetch), generator, True
        self.start()
    def run(self):
        try:
            for item in self.generator: self.queue.put(item)
        except Exception as e:
            print('WARNING: Failed in BackgroundGenerator Thread!')
            raise e
        finally: self.queue.put(None)
    def __iter__(self): return self
    def __next__(self):
        next_item = self.queue.get()
        if next_item is None: raise StopIteration
        return next_item

class prefetch:
    "Decorator for making a BackgroundGenerator."
    # https://github.com/justheuristic/prefetch_generator
    def __init__(self, max_prefetch:int=1): self.max_prefetch = max_prefetch
    def __call__(self, gen):
        def wrapper(*args,**kwargs):
            return BackgroundGenerator(gen(*args,**kwargs), max_prefetch=self.max_prefetch)
        return wrapper
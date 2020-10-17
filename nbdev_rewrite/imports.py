import os,re,json,glob,collections,pickle,shutil,nbformat,inspect,yaml,tempfile,enum,stat,time,random
import importlib.util
from pdb import set_trace
from configparser import ConfigParser
from pathlib import Path
from textwrap import TextWrapper
from typing import Union,Optional
from nbformat.sign import NotebookNotary
from functools import partial,lru_cache
from base64 import b64decode,b64encode

def test_eq(a,b): assert a==b, f'{a}, {b}'

def save_config_file(file, d, **kwargs):
    "Write settings dict to a new config file, or overwrite the existing one."
    config = ConfigParser(**kwargs)
    config['DEFAULT'] = d
    config.write(open(file, 'w'))

def read_config_file(file, **kwargs):
    config = ConfigParser(**kwargs)
    config.read(file)
    return config

_defaults = {"host": "github", "doc_host": "https://%(user)s.github.io", "doc_baseurl": "/%(lib_name)s/"}

def add_new_defaults(cfg, file):
    for k,v in _defaults.items():
        if cfg.get(k, None) is None: 
            cfg[k] = v
            save_config_file(file, cfg)
            
def _add_new_defaults(cfg, file, **kwargs):
    for k,v in kwargs.items():
        if cfg.get(k, None) is None:
            cfg[k] = v
            save_config_file(file, cfg)

@lru_cache(maxsize=None)
class Config:
    "Store the basic information for nbdev to work"
    def __init__(self, cfg_name='settings.ini'):
        cfg_path = Path.cwd()
        while cfg_path != cfg_path.parent and not (cfg_path/cfg_name).exists(): cfg_path = cfg_path.parent
        self.config_path,self.config_file = cfg_path,cfg_path/cfg_name
        assert self.config_file.exists(), f"Could not find {cfg_name}"
        self.d = read_config_file(self.config_file)['DEFAULT']
        _add_new_defaults(self.d, self.config_file,
                         host="github", doc_host="https://%(user)s.github.io", doc_baseurl="/%(lib_name)s/")

    def __getattr__(self,k):
        if k.endswith('_path'): return self._path_to(k)
        try: return self.d[k]
        except KeyError: raise AttributeError(f"Config ({self.config_file.name}) has no attribute '{k}'") from None
    
    def _path_to(self,k,default=None):
        v = self.d.get(k, default)
        if v is None: raise AttributeError(f"Config ({self.config_file.name}) has no attribute '{k}'")
        return self.config_path/v
    
    def path_to(self,k,default=None):
        "Retrieve a path saved in Config relative to the folder the Config file is in."
        return self._path_to((k if k.endswith('_path') else k+'_path'), default)

    def get(self,k,default=None): return self.d.get(k, default)
    def __setitem__(self,k,v): self.d[k] = str(v)
    def __contains__(self,k):  return k in self.d
    def save(self): save_config_file(self.config_file,self.d)

def create_config(host, lib_name, user, path='.', cfg_name='settings.ini', branch='master',
               git_url="https://github.com/%(user)s/%(lib_name)s/tree/%(branch)s/", custom_sidebar=False,
               nbs_path='nbs', lib_path='%(lib_name)s', doc_path='docs', tst_flags='', version='0.0.1', **kwargs):
    "Creates a new config file for `lib_name` and `user` and saves it."
    g = locals()
    config = {o:g[o] for o in 'host lib_name user branch git_url lib_path nbs_path doc_path tst_flags version custom_sidebar'.split()}
    config = {**config, **kwargs}
    save_config_file(Path(path)/cfg_name, config)

###############################################################

def in_ipython():
    "Check if the code is running in the ipython environment (jupyter including)"
    program_name = os.path.basename(os.getenv('_', ''))
    if ('jupyter-notebook' in program_name or # jupyter-notebook
        'ipython'          in program_name or # ipython
        'JPY_PARENT_PID'   in os.environ):    # ipython-notebook
        return True
    else:
        return False

IN_IPYTHON = in_ipython()

def in_colab():
    "Check if the code is running in Google Colaboratory"
    try:
        from google import colab
        return True
    except: return False

IN_COLAB = in_colab()

def in_notebook():
    "Check if the code is running in a jupyter notebook"
    if in_colab(): return True
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell': return True   # Jupyter notebook, Spyder or qtconsole
        elif shell == 'TerminalInteractiveShell': return False  # Terminal running IPython
        else: return False  # Other type (?)
    except NameError: return False      # Probably standard Python interpreter

IN_NOTEBOOK = in_notebook()

###############################################################

import concurrent.futures

def num_cpus():
    "Get number of cpus"
    try:                   return len(os.sched_getaffinity(0))
    except AttributeError: return os.cpu_count()

class ProcessPoolExecutor(concurrent.futures.ProcessPoolExecutor):
    "Like `concurrent.futures.ProcessPoolExecutor` but handles 0 `max_workers`."
    def __init__(self, max_workers=None, on_exc=print, **kwargs):
        self.not_parallel = max_workers==0
        self.on_exc = on_exc
        if self.not_parallel: max_workers=1
        super().__init__(max_workers, **kwargs)

    def map(self, f, items, *args, **kwargs):
        g = partial(f, *args, **kwargs)
        if self.not_parallel: return map(g, items)
        try: return super().map(g, items)
        except Exception as e: self.on_exc(e)

def parallel(f, items, *args, n_workers=None, **kwargs):
    "Applies `func` in parallel to `items`, using `n_workers`"
    if n_workers is None: n_workers = min(16, num_cpus())
    with ProcessPoolExecutor(n_workers) as ex:
        r = ex.map(f,items, *args, **kwargs)
        return list(r)

###############################################################

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

###############################################################

class ReLibName():
    "Regex expression that's compiled at first use but not before since it needs `Config().lib_name`"
    def __init__(self, pat, flags=0): self._re,self.pat,self.flags = None,pat,flags
    @property
    def re(self):
        if not hasattr(Config(), 'lib_name'): raise Exception("Please fill in the library name in settings.ini.")
        self.pat = self.pat.replace('LIB_NAME', Config().lib_name)
        if self._re is None: self._re = re.compile(self.pat, self.flags)
        return self._re

###############################################################

def compose(*funcs, order=None):
    "Create a function that composes all functions in `funcs`, passing along remaining `*args` and `**kwargs` to all"
    if len(funcs)==0: return noop
    if len(funcs)==1: return funcs[0]
    def _inner(x, *args, **kwargs):
        for f in funcs: x = f(x, *args, **kwargs)
        return x
    return _inner

def last_index(x, o):
    "Finds the last index of occurence of `x` in `o` (returns -1 if no occurence)"
    try: return next(i for i in reversed(range(len(o))) if o[i] == x)
    except StopIteration: return -1
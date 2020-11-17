# AUTOGENERATED! DO NOT EDIT! File to edit: 00_export_v4.ipynb (unless otherwise specified).


__all__ = ['StackTrace', 'all_commands', 'cmd2func', 'crawl_directory', 'file_generator', 'find_names', 'init_config', 'init_lib', 'iter_comments', 'kw_default_exp', 'kw_export', 'load_and_parse_all', 'main', 'make_valid_path', 'module_to_path', 'parse_comment', 'parse_file', 'read_nb', 'register_command', 'relativify_imports', 'set_main_report_options', 'traced', 'write_file', 'write_out_all']


# Cell nr. 40
from collections import namedtuple, defaultdict
import os
import re
from .imports import *

from inspect import signature, currentframe, getfullargspec

import functools
from types import MethodType,FunctionType

import ast
from ast import iter_fields, AST
import _ast


# Cell nr. 41
# Only import if executing as a python file, because then argument_parsing is in a different file.
if (__name__ != '__main__') or ('parse_arguments' not in globals()):
    from .argument_parsing import *
assert 'parse_arguments' in globals(), "Missing the 'parse_arguments' function."


# Internal Cell nr. 45
main_REPORT_OPTIONAL_ERROR:bool = False


# Cell nr. 46
def set_main_report_options(report_optional_error:bool=False):
    "Set options for how the Main Module will behave on encountering errors or warnings.\n"\
    "report_optional_error prints the information and then continues."
    global main_REPORT_OPTIONAL_ERROR
    main_REPORT_OPTIONAL_ERROR = report_optional_error


# Cell nr. 47
class StackTrace: pass # only for :StackTrace annotations to work
class StackTrace:
    _up:StackTrace = None
    namespace:str = None
    lineno   :int = None
    _ext_file:dict = None
        
    def __init__(self, namespace:object=None, up:StackTrace=None):
        "`namespace` can be a function, a class, or None.\n"\
        "`up` is optional and can be another StackTrace instance."
        self.namespace = f'<{namespace.__qualname__}>()' if namespace else currentframe().f_back.f_code.co_name
        self._up, self.lineno, self._ext_file = up, currentframe().f_back.f_lineno, {}
    
    def ext(self, file:str=None, cellno:int=None, lineno:int=None, excerpt:str=None, span:(int, int)=None):
        "Set context information for reporting errors in external files e.g. notebooks."
        e = self._ext_file
        if file: e['file'] = file
        if cellno: e['cellno'] = cellno
        if lineno: e['lineno'] = lineno
        if excerpt: e['excerpt'] = excerpt
        if span   : e['span'   ] = span
    
    def to_list(self):
        "Creates list of the entire StackTrace (most recent last)."
        if self._up: return [*self._up.to_list(), self]
        else: return [self]
        
    def _reduce_ext(self):
        "Combines all `StackTrace._ext_file` dicts into one, prefering more recest settings over old ones."
        ext = [s._ext_file for s in self.to_list() if s._ext_file]
        if ext:
            e = ext[0]
            for d in ext[1:]: e.update(d)
            return e
        else: return {}
        
    def up(self, up:StackTrace):
        "Set this StackTraces `_up` reference and return `self`. Useful for chaining references."
        self._up=up
        return self
    
    def __repr__(self): return f"{__name__}.StackTrace(namespace={self.namespace},line={self.lineno})"
    
    def _repr(self):
        "Recursively create a string of all StackTraces for printing error messages."
        return f"{'' if self._up is None else self._up._repr()}"\
               f"<{__name__}>, line {self.lineno} in {self.namespace}\n"
    
    def _repr_ext(self, file:str=None, cellno:int=None, lineno:int=None, excerpt:str=None, span:(int, int)=None):
        "Create a string from the `StackTrace._ext_file` dict for printing error messages."
        s = f"<{file}>, cell {cellno}, line {lineno}\n"
        if excerpt:
            x = f"--->{' ' if ((lineno is None) or (0 <= lineno <= 9)) else ''}{lineno} "
            s += f"{x}{excerpt}\n"\
                 f"{(' ' * (len(x) + span[0]) + '^' * span[1]) if span else ''}\n"
        return s        
    
    def report_error(self, err:Exception,
                     file:str=None, cellno:int=None, lineno:int=None, excerpt:str=None, span:(int, int)=None,
                     success=False, _ln_of_callsite=True) -> bool:
        "Report the Error `err`.\nOther args are used for setting `_ext_file` and are optional.\n"\
        "Returns whatever is passes as `success`."
        if _ln_of_callsite: self.lineno = currentframe().f_back.f_lineno
        err_type = err.__class__.__name__
        s = f"{'-'*75}\n"\
            f"{err_type}{' '*(41-len(err_type))}Stacktrace (most recent call last)\n"\
            f"{self._repr()}\n"
        self.ext(file, cellno, lineno, excerpt, span)
        ext:dict = self._reduce_ext()
        if ext: s += f"{self._repr_ext(**ext)}\n"
        s += f"[{err_type}]: {err}"
        print(s)
        return success
    
    def report_optional_error(self, err:Exception,
                        file:str=None, cellno:int=None, lineno:int=None, excerpt:str=None, span:(int, int)=None):
        "Report the error if the global variable `main_REPORT_OPTIONAL_ERROR` is set."
        if main_REPORT_OPTIONAL_ERROR:
            self.lineno = currentframe().f_back.f_lineno
            self.report_error(err=err, _ln_of_callsite=False,
                              file=file, cellno=cellno, lineno=lineno, excerpt=excerpt, span=span)


# Cell nr. 48
def traced(f):
    "The Annotated function will have a StackTrace instance passed to it as the `st` keyword-argument.\n"\
    "That instance represents the annotated function, with a reference to the calling site."
    spec = getfullargspec(f)
    assert ('st' in spec.args) or ('st' in spec.kwonlyargs), "Traced functions have to take a 'st' argument."
    if 'st' in spec.annotations:
        assert spec.annotations['st'] == StackTrace, "A traced functions 'st' argument is reserved for "\
                                                     "a StackTrace. Other annotations are not allowed."
    else: f.__annotations__['st'] = StackTrace # This modifies the original function. Is that acceptable?
    
    _st = StackTrace(f)
    def _wrapper(*args, st:StackTrace=None, **kwargs):
        if not st:
            st = StackTrace(None)
            st.namespace = currentframe().f_back.f_code.co_name
        elif (st is _st): return f(*args, st=st, **kwargs) # prevent self referencing due to e.g. recursion.
        st.lineno = currentframe().f_back.f_lineno
        return f(*args, st=_st.up(st), **kwargs)
    
    functools.update_wrapper(_wrapper, f)
    return _wrapper


# Cell nr. 63
# TODO: Only look for 0 indent comments?
def iter_comments(src:str, pure_comments_only:bool=True, line_limit:int=None) -> (str, (int, int)):
    "Detect all comments in a piece of code, excluding those that are a part of a string."
    in_lstr = in_sstr = False
    count, quote = 1, ''
    for i, line in enumerate(src.splitlines()[:line_limit]):
        is_pure, escape, prev_c = True, False, '\n'
        for j, c in enumerate(line):
            # we can't break as soon as not is_pure, because we have to detect if a multiline string beginns
            if is_pure and (not (c.isspace() or c == '#')): is_pure = False
            if (in_sstr or in_lstr):
                # assert in_sstr ^ in_lstr # XOR
                if escape: count = 0
                else:
                    if (c == quote):
                        count = ((count + 1) if (c == prev_c) else 1)
                        if in_sstr: in_sstr = False
                        elif (in_lstr and (count == 3)): count, in_lstr = 0, False
                escape = False if escape else (c == '\\')
            else:                    
                if (c == '#'):
                    if (pure_comments_only and is_pure): yield (line, (i, j))
                    elif (not pure_comments_only):       yield (line[j:], (i, j))
                    break
                elif c == "'" or c == '"':
                    count = ((count + 1) if (c == prev_c) else 1)
                    if count == 1: in_sstr = True
                    elif count == 3: count, in_lstr = 0, True
                    else: assert False, 'If this code path happens, then the code keeping track of quotes is broken.'
                    quote = c
            prev_c = c


# Internal Cell nr. 67
# https://docs.python.org/3/library/re.html
re_match_comment = re.compile(r"""
        ^              # start of the string
        \s?            # 0 or 1 whitespace
        \#+\s?         # 1 or more literal "#", then 0 or 1 whitespace
        (.*)           # group of arbitrary symbols (except new line)
        $              # end of the string
        """,re.IGNORECASE | re.VERBOSE) # re.MULTILINE is not passed, since this regex is used on each line separately.


# Cell nr. 72
@traced
def parse_comment(all_commands:dict, comment:str, st:StackTrace) -> (bool, str, dict, dict):
    "Finds command names and arguments in comments and parses them with parse_arguments()"
    res = re_match_comment.search(comment)
    if not res:
        st.report_optional_error(SyntaxError('Not a valid comment syntax.'))
        return False, None, None, None
    
    all_args = res.groups()[0].split()
    if len(all_args) == 0:
        st.report_optional_error(SyntaxError(f"Need at least one argument in comment. Reveived: '{comment}'"))
        return False, None, None, None
    
    cmd, *args = all_args
    if cmd[0] != '+':
        st.report_optional_error(SyntaxError("The first argument (the command to execute) does not start with a '+'."\
                                            f"It was: '{cmd}'"), span=(1, 3))
        return False, None, None, None
    
    cmd = cmd[1:] # remove the '+'
    if cmd not in all_commands:
        st.report_optional_error(KeyError(f"'{cmd}' is not a recognized command. See 'all_commands'."))
        return False, None, None, None
    
    success, result, is_set = parse_arguments(all_commands[cmd], args)
    if not success: return False, None, None, None
    
    return True, cmd, result, is_set


# Internal Cell nr. 82
class Context:
    def __init__(self, cell_nr=None, export_nr=None):
        self.cell_nr   = cell_nr
        self.export_nr = export_nr
    def __repr__(self):
        return f'cell_nr: {self.cell_nr}, export_nr: {self.export_nr}'


# Internal Cell nr. 83
def lineno(node):
    "Format a string containing location information on ast nodes. Used for Debugging only."
    if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
        return f'line_nr: {node.lineno} col_offset: {node.col_offset}'
    else: return ''


# Internal Cell nr. 84
def info(context, node):
    "Format a string with available information on a ast node. Used for Debugging only."
    return f'\nLocation: {context} | {lineno(node)}'


# Internal Cell nr. 86
def unwrap_attr(node:_ast.Attribute) -> str:
    "Joins a sequance of Attribute accesses together in a single string. e.g. numpy.array"
    if isinstance(node.value, _ast.Attribute): return '.'.join((unwrap_attr(node.value), node.attr))
    else: return '.'.join((node.value.id, node.attr))


# Internal Cell nr. 87
def update_from_all_(node, names, c):
    "inplace, recursive update of set of names, by parsing the right side of a _all_ variable"
    if   isinstance(node, _ast.Str): names.add(node.s)
    elif isinstance(node, _ast.Name): names.add(node.id)
    elif isinstance(node, _ast.Attribute): names.add(unwrap_attr(node))
    elif isinstance(node, (_ast.List, _ast.Tuple, _ast.Set)):
        for x in node.elts: update_from_all_(x, names, c)
    elif isinstance(node, _ast.Subscript) :
        raise SyntaxError(f'Subscript expression not allowed in _all_. {info(c, node)}')
    elif isinstance(node, _ast.Starred):
        raise SyntaxError(f'Starred expression *{node.value.id} not allowed in _all_. {info(c, node)}')
    else: raise SyntaxError(f'Can\'t resolve {node} to name, unknown type. {info(c, node)}')


# Internal Cell nr. 88
def unwrap_assign(node, names, c):
    "inplace, recursive update of list of names"
    if   isinstance(node, _ast.Name)      : names.append(node.id)
    elif isinstance(node, _ast.Starred)   : names.append(node.value.id)
    elif isinstance(node, _ast.Attribute) : names.append(unwrap_attr(node))
    elif isinstance(node, _ast.Subscript) : pass # e.g. a[0] = 1
    elif isinstance(node, (_ast.List, _ast.Tuple)):
        for x in node.elts: unwrap_assign(x, names, c)
    elif isinstance(node, list):
        for x in node: unwrap_assign(x, names, c)
    else: raise SyntaxError(f'Can\'t resolve {node} to name, unknown type. {info(c, node)}')


# Internal Cell nr. 89
def not_private(name): return not (name.startswith('_') and (not name.startswith('__')))


# Internal Cell nr. 90
def add_names_A(node, names, c):
    "Handle Assignments to variables"
    tmp_names = list()
    if   isinstance(node, _ast.Assign):
        unwrap_assign(node.targets, tmp_names, c)
    elif isinstance(node, _ast.AnnAssign):
        unwrap_assign(node.target, tmp_names, c)
    else: assert False, 'add_names_A only accepts _ast.Assign or _ast.AnnAssign'
    for name in tmp_names:
        if not_private(name): names.add(name)
        # NOTE: special cases below can only use private variable names
        elif name == '_all_': # NOTE: _all_ is a keyword reserved by nbdev.
            if len(tmp_names) != 1:
                raise SyntaxError(f'Reserved keyword "_all_" can only be used in simple assignments. {info(c, node)}')
            update_from_all_(node.value, names, c)


# Internal Cell nr. 91
def decorators(node):
    yield from [(d.id if isinstance(d, _ast.Name) else d.func.id) for d in node.decorator_list]

def fastai_patch(cls, node, names, c):
    if   isinstance(cls, _ast.Name):
        if not_private(cls.id): names.add(f'{cls.id}.{node.name}')
    elif isinstance(cls, (_ast.List, _ast.Tuple, _ast.Set)):
            for x in cls.elts: fastai_patch(x, node, names, c)
    else: raise SyntaxError(f'Can\'t resolve {cls} to @patch annotation, unknown type. {info(c, node)}')

# ignoring `@typedispatch` might not even be neccesarry,
# since all names are added to a single set before being exported.
def add_names_FC(node, names, c, fastai_decorators=True):
    "Handle Function and Class Definitions"
    if fastai_decorators and ('patch' in decorators(node)):
        if not (len(node.args.args) >= 1): raise SyntaxError(f'fastai\'s @patch decorator requires at least one parameter. {info(c, node)}')
        cls = node.args.args[0].annotation
        if cls is None: raise SyntaxError(f'fastai\'s @patch decorator requires a type annotation on the first parameter. {info(c, node)}')
        fastai_patch(cls, node, names, c)
    elif fastai_decorators and ('typedispatch' in decorators(node)): return # ignore @typedispatch
    elif not_private(node.name): names.add(node.name)


# Cell nr. 92
def find_names(code:str, context:Context=None) -> list:
    "Find all function, class and variable names in the given source code."
    tree = ast.parse(code)
    names = set()
    for node in tree.body:
        if   isinstance(node, (_ast.Assign     , _ast.AnnAssign)): add_names_A (node, names, context)
        elif isinstance(node, (_ast.FunctionDef, _ast.ClassDef )): add_names_FC(node, names, context)
        else: pass
    return names


# Internal Cell nr. 98
def make_import_relative(p_from:Path, m_to:str)->str:
    "Convert a module `m_to` to a name relative to `p_from`."
    mods = m_to.split('.')
    splits = str(p_from).split(os.path.sep)
    if mods[0] not in splits: return m_to
    i=len(splits)-1
    while i>0 and splits[i] != mods[0]: i-=1
    splits = splits[i:]
    while len(mods)>0 and splits[0] == mods[0]: splits,mods = splits[1:],mods[1:]
    return '.' * len(splits) + '.'.join(mods)


# Internal Cell nr. 102
# https://docs.python.org/3/library/re.html
letter = 'a-zA-Z'
identifier = f'[{letter}_][{letter}0-9_]*'
re_import = ReLibName(fr"""
    ^                             # start of the string / line
    (\ *)                         # any amount of whitespace (indenting)
    from(\ +)                     # 'from', followed by at least one whitespace
    (LIB_NAME(?:\.{identifier})*) # Name of the library, possibly followed by dot separated submodules
    \ +import(.+)                 # whitespace, then 'import', followed by arbitrary symbols except new line
    $                             # end of the string / line
    """, re.VERBOSE | re.MULTILINE)


# Cell nr. 103
def relativify_imports(origin:Path, code:str)->str:
    "Transform an absolute 'from LIB_NAME import module' into a relative import of 'module' wrt the library."
    def repl(match):
        sp1,sp2,module,names = match.groups()
        return f'{sp1}from{sp2}{make_import_relative(origin, m_to=module)} import{names}'
    return re_import.re.sub(repl,code)


# Cell nr. 107
def init_config(lib_name='nbdev_rewrite', user='flpeters', nbs_path='.'):
    "create a config file, if it doesn't already exist"
    if not Config().config_file.exists(): create_config(lib_name=lib_name, user=user, nbs_path=nbs_path)
init_config()


# Cell nr. 108
def init_lib():
    "initialize the module folder, if it's not initialized already"
    C = Config()
    if (not C.lib_path.exists()) or (not (C.lib_path/'__init__.py').exists()):
        C.lib_path.mkdir(parents=True, exist_ok=True)
        with (C.lib_path/'__init__.py').open('w') as f:
            f.write(f'__version__ = "{C.version}"\n')
    else: pass # module *should* already exists
init_lib()


# Cell nr. 110
_reserved_dirs = (Config().lib_path, Config().nbs_path, Config().doc_path)
def crawl_directory(path:Path, recurse:bool=True) -> list:
    "finds a list of ipynb files to convert"
    # TODO: Handle symlinks?
    if isinstance(path, (list, tuple)):
        for p in path: yield from crawl_directory(p, recurse)
    elif path.is_file(): yield path
    else:
        for p in path.iterdir():
            f = p.name
            if f.startswith('.') or f.startswith('_'): continue
            if p.is_file():
                if f.endswith('.ipynb'): yield p
                else: continue
            elif p.is_dir() and recurse:
                if p in _reserved_dirs: continue
                else: yield from crawl_directory(p, recurse)
            else: continue
list(crawl_directory(Config().nbs_path))


# Cell nr. 111
def read_nb(fname:Path) -> dict:
    "Read the notebook in `fname`."
    with open(Path(fname),'r', encoding='utf8') as f: return dict(nbformat.reads(f.read(), as_version=4))


# Cell nr. 113
@prefetch(max_prefetch=4)
def file_generator(path:Path=Config().nbs_path) -> (Path, dict):
    for file_path in crawl_directory(path): yield (file_path, read_nb(file_path))


# Internal Cell nr. 121
# https://docs.python.org/3/library/re.html
letter = 'a-zA-Z'
identifier = f'[{letter}_][{letter}0-9_]*'
module = fr'(?:{identifier}\.)*{identifier}'
module


# Internal Cell nr. 122
# https://docs.python.org/3/library/re.html
re_match_module = re.compile(fr"""
        ^              # start of the string
        {module}       # definition for matching a module 
        $              # end of the string
        """, re.VERBOSE)


# Cell nr. 124
@traced
def module_to_path(m:str, st:StackTrace)->(bool, Path):
    "Turn a module name into a path such that the exported file can be imported from the library "\
    "using the same expression."
    if re_match_module.search(m) is not None:
        if m.endswith('.py'):
            return st.report_error(ValueError(f"The module name '{m}' is not valid, because ending on '.py' "\
                                f"would produce a file called 'py.py' in the folder '{m.split('.')[-2]}', "\
                                 "which is most likely not what was intended.\nTo name a file 'py.py', use the "\
                                 "'-to_path' argument instead of '-to'.")), None
        return True, Config().path_to('lib')/f"{os.path.sep.join(m.split('.'))}.py"
    else: return st.report_error(ValueError(f"'{m}' is not a valid module name.")), None


# Internal Cell nr. 133
def commonpath(*paths)->Path:
    "Given a sequence of path names, returns the longest common sub-path."
    return Path(os.path.commonpath(paths))


# Internal Cell nr. 135
def in_directory(p:Path, d:Path)->bool:
    "Tests if `p` is pointing to something in the directory `d`.\n"\
    "Expects both `p` and `d` to be fully resolved and absolute paths."
    return p.as_posix().startswith(d.as_posix())


# Cell nr. 138
@traced
def make_valid_path(s:str, st:StackTrace)->(bool, Path):
    "Turn a export path argument into a valid path, resolving relative paths and checking for mistakes."
    p, lib = Path(s), Config().path_to('lib')
    is_abs = p.is_absolute()
    p = (p if is_abs else (lib/p)).absolute().resolve()
    if (not is_abs) and (not in_directory(p, lib)):
        return st.report_error(ValueError("Relative export path beyond top level directory of library"\
                                          "is not allowed by default. Use an absolute path, "\
                                          f"or set <NOT IMPLEMENTED YET> flag on the command. ('{s}')")), None
    if not p.suffix:
        return st.report_error(ValueError(f"The path '{s}' is missing a file type suffix like '.py'.")), None
    if p.suffix == '.py': return True, p
    else: return st.report_error(ValueError(f"Expected '.py' file ending, but got '{p.suffix}'. ('{s}')")), None


# Cell nr. 150
def register_command(cmd, args, active=True):
    "Store mapping from command name to args, and command name to reference to the decorated function in globals."
    if not active: return lambda f: f
    all_commands[cmd] = args
    def _reg(f):
        cmd2func[cmd] = f
        return f
    return _reg


# Cell nr. 151
all_commands = {}
cmd2func     = {}


# Cell nr. 153
@register_command(cmd='default_exp', # allow custom scope name that can be referenced in export?
                  args={'to': '', 'to_path': '', 'scoped': False})
@traced
def kw_default_exp(file_info, cell_info, result, is_set, st:StackTrace) -> bool:
    "Set the default file that cells of this notebook will be exported to."
    success:bool = True
    if not (is_set['to'] ^ is_set['to_path']): # NOTE: XOR
        return st.report_error(ValueError("The `default_exp` command expects exactly one of the arguments "\
                               f"'-to' or '-to_path' to be set, but recieved was: {result}"))
    # NOTE: use this cells indentation level, or the default tuple([0]) as key to identify scope
    scope:tuple     = cell_info['scope'] if result['scoped'] else tuple([0])
    old_target:Path = file_info['export_scopes'].get(scope, None)
    conv_success, new_target = (module_to_path(result['to'], st=st)
                                if is_set['to'] else
                                make_valid_path(result['to_path'], st=st))
    if not conv_success: return False
    if old_target is not None:
        return st.report_error(ValueError(f"Overwriting an existing export target is not allowed."\
                               f"\n\twas: '{old_target}'\n\tnew: '{new_target}'"))
    file_info['export_scopes'][scope] = new_target
    return success


# Cell nr. 155
@register_command(cmd='export',
                  args={'internal': False, 'to': '', 'to_path':'', 'ignore_scope':False,
                        'cell_nr': 0, 'prepend': False, 'append': False})
@traced
def kw_export(file_info, cell_info, result, is_set, st:StackTrace) -> bool:
    "This cell will be exported from the notebook to a .py file."
    success:bool = True
    if (is_set['to'] and is_set['to_path']):
        return st.report_error(ValueError("The `export` command does not accept the '-to' and '-to_path' "\
                               f"argument at the same time. They are mutually exclusive. Received: {result}"))
    cell_info['export_to_py'] = True # Using this command implicitly means to export this cell
    if is_set['cell_nr']: cell_info['cell_nr'] = result['cell_nr'] # overwrite the cell_nr of this cell
    is_internal = cell_info['is_internal'] = result['internal']
    if is_internal: pass # no contained names will be added to __all__ for importing
    else: cell_info['names'] = find_names(cell_info['original_source_code'])
    conv_success, export_target = True, None
    if is_set['to'     ]: conv_success, export_target = module_to_path (result['to'], st=st)
    if is_set['to_path']: conv_success, export_target = make_valid_path(result['to_path'], st=st)
    if not conv_success: return False
    if export_target is not None:
        if is_set['ignore_scope']:
            return st.report_error(ValueError("Setting 'ignore_scope' is not allowed when exporting to "\
                                   f"a custom target using 'to' or 'to_path'."))
        cell_info['export_to'].append(export_target) # Set a new export target just for this cell.
    else:
        if result['ignore_scope']: cell_info['export_to_default'] += 1
        else:                      cell_info['export_to_scope']   += 1
    return success


# Internal Cell nr. 166
# https://docs.python.org/3/library/re.html
re_match_heading = re.compile(r"""
        ^              # start of the string
        (\#+)\s+       # 1 or more literal "#", then 1 or more whitespace
        (.*)           # group of arbitrary symbols (including new line)
        $              # end of the string
        """,re.IGNORECASE | re.VERBOSE | re.DOTALL)


# Cell nr. 168
@traced
def parse_file(file_path:Path, file:dict, st:StackTrace) -> (bool, dict):
    success = True
    pure_comments_only = True
    nb_version:(int, int) = (file['nbformat'], file['nbformat_minor'])
    metadata  :dict       =  file['metadata']
        
    file_info = {
        'origin_file': file_path,
        'relative_origin': os.path.relpath(file_path, Config().config_file.parent).replace('\\', '/'),
        'nb_version': nb_version,
        'export_scopes': {
            tuple([0]): None, # This is the default for an entire file.
        },
        'cells': list()
    }
    scope_count :[int] = [0]
    scope_level :int   = 0
    
    cells:list = file_info['cells']
    
    st.ext(file=file_info['relative_origin'])
    
    for i, cell in enumerate(file['cells']):
        cell_type   = cell['cell_type']
        cell_source = cell['source']
        cell_info = {
            'cell_nr' : i,
            'cell_type' : cell_type,
            'original_source_code' : cell_source,
            'processed_source_code': cell_source,
            'scope' : tuple(scope_count),
            'export_to_py' : False,
            'export_to_scope' : 0,
            'export_to_default' : 0,
            'is_internal' : None,
            'export_to' : [],
            'names' : None,
            'comments' : []
        }
        if cell_type == 'code':
            st.ext(cellno = i)
            comments_to_remove = []
            for comment, (lineno, charno) in iter_comments(cell_source, pure_comments_only, line_limit=None):
                st.ext(lineno = lineno + 1) # zero counting offset
                st.ext(excerpt = comment)
                parsing_success, cmd, result, is_set = parse_comment(all_commands,comment,st=st)
                if not parsing_success: continue
                print(f'Found: {cmd} @ ({i}, {lineno}, {charno}) with args: {result}')
                if cmd in cmd2func:
                    cmd_success = cmd2func[cmd](file_info, cell_info, result, is_set, st=st)
                    if not cmd_success: return False, file_info # TODO: Stop at first error or continue?
                else: raise ValueError(f"The command '{cmd}' in cell number {i} is recognized, "\
                                        "but is missing a corresponding action mapping in cmd2func.")
                cell_info['comments'].append(comment)
                comments_to_remove.append((lineno, charno))
            if len(comments_to_remove) > 0:
                lines = cell_source.splitlines()
                if pure_comments_only:
                    for lineno, charno in comments_to_remove[::-1]: lines.pop(lineno)
                else:
                    for lineno, charno in comments_to_remove[::-1]: lines[lineno] = lines[lineno][:charno]
                cell_info['processed_source_code'] = '\n'.join(lines)
            
        elif cell_type == 'markdown':
            res = re_match_heading.search(cell_source)
            if not (res is None): # this cell contains a heading
                heading_level, heading_name = res.groups()
                new_scope_level = len(heading_level) # number of '#' in the heading
                if new_scope_level > scope_level:
                    scope_count += ([0] * (new_scope_level - (len(scope_count)))) # extend list if necessary
                elif new_scope_level < scope_level:
                    scope_count = scope_count[:new_scope_level] # reset lower values
                scope_count[new_scope_level - 1] += 1
                scope_level = new_scope_level
            else: pass # this cell is regular markdown
        elif cell_type == 'raw': pass
        else: raise ValueError(f"Unknown cell_type '{cell_type}' in cell number {i}."\
                                "Should be 'code', 'markdown', or 'raw'.")
        cells.append(cell_info)
    return success, file_info


# Cell nr. 169
@traced
def load_and_parse_all(origin_path:Path, output_path:Path, recurse:bool, st:StackTrace) -> (bool, dict):
    "Loads all .ipynb files in the origin_path directory, and passes them one at a time to parse_file."
    success:bool = True
    # TODO: replace these two lines with a call to file_generator() defined above.
    file_paths:list = crawl_directory(Config().nbs_path)
    
    # TODO: fine tune, or even pass an argument from the user on how many thread to use for prefetching files.
    #       num_cpus() from nbdev.imports can be used here
    file_generator = BackgroundGenerator(((file_path, read_nb(file_path)) for file_path in file_paths), max_prefetch=4)
    
    parsed_files = {
        # Add flags and settings variables above this line
        'files': list()
    }
    
    # TODO: use multithreading / multiprocessing per file / per bunch of cells
    for file_path, file in file_generator:
        # if file_path.name != THIS_FILE: continue # For Debugging
        parse_success, file = parse_file(file_path, file, st=st)
        if not parse_success:
            success = False # TODO: Stop at first error or continue?
        # TODO: before returning, give any meta programm a chance to run.
        # maybe have parse_file return some additional information about any meta programm
        parsed_files['files'].append(file)
        
    return success, parsed_files


# Cell nr. 178
@traced
def write_file(to:Path, orig:str, names:set, code:list, st:StackTrace) -> bool:
    sep:str = '\n\n\n'
    if orig is None:
        warning = f'# AUTOGENERATED! DO NOT EDIT! View info comment on each cell for file to edit.'
    else:
        warning = f'# AUTOGENERATED! DO NOT EDIT! File to edit: {orig} (unless otherwise specified).'
    if len(names) > 0:
        # TODO: add line breaks at regular intervals
        comma = "', '"
        names:str = f"{sep}__all__ = ['{comma.join(sorted(names))}']"
    else: names:str = f'{sep}__all__ = []'
    code :str = sep + sep.join(code)
    file_content:str = f'{warning}{names}{code}'
    # print('-'*70)
    # print(to)
    # print(file_content)
    to.parent.mkdir(parents=True, exist_ok=True)
    with open(to, 'w', encoding='utf8') as f: f.write(file_content)


# Cell nr. 179
@traced
def write_out_all(parsed_files, st:StackTrace) -> bool:
    # TODO: write one file at a time to disk, to the correct directory,
    # initialize a python module, if it doesn't already exists,
    # Handle mergers between multiple parsed_files. <-----------------
    success:bool = True
    config    = Config()
    lib_path  = config.lib_path
    nbs_path  = config.nbs_path
    proj_path = config.config_file.parent
    zero_tuple = tuple([0])
    
    export_files = defaultdict(lambda: {'names': set(), 'code': [], 'orig': None})
    
    for file_info in parsed_files['files']:
        rel_orig:str = file_info['relative_origin']
        scopes:dict  = file_info['export_scopes']
        assert zero_tuple in scopes, 'No default in export Scopes.'
        scopes_available:bool = (len(scopes) > 1)
        default_export:Path = scopes[zero_tuple]
        # NOTE: Having no default is ok, as long as all cells still have a valid export target
        none_default  :bool = (default_export is None)
            
        if not none_default:
            default_state = export_files[default_export]
            if (default_state['orig'] is None): default_state['orig'] = rel_orig
            else: raise ValueError(f'Multiple files have {default_export} as the default export target. '\
                                   f'(old: {default_state["orig"]} | new: {rel_orig})')
                
        for cell in file_info['cells']:
            if not cell['export_to_py']: continue
            info_string = f"# {'Internal ' if cell['is_internal'] else ''}Cell nr. {cell['cell_nr']}"
            info_string_src = f"{info_string}; Comes from '{rel_orig}'"
            
            if len(cell['export_to']) > 0:
                for to in cell['export_to']:
                    state:dict = export_files[to]
                    if not cell['is_internal']: state['names'].update(cell['names'])
                    # TODO: implement code appending / prepending here
                    state['code'].append(f"{info_string_src}\n{relativify_imports(to, cell['processed_source_code'])}")
            
            if scopes_available:
                if cell['export_to_scope'] > 0:
                    # Do scope matching
                    cell_scope:tuple = cell['scope']
                    best_fit = zero_tuple
                    best_fit_len = 0
                    # NOTE: The number of scopes should usually be relatively small
                    for k in scopes.keys(): # TODO: can this go faster with sorting, binary search, quit early?
                        if ((len(k) > best_fit_len) # Trying to find the tightest fit
                            and (k == cell_scope[:len(k)])): # iff cell is part of this scope
                            best_fit, best_fit_len = k, len(k)
                    to:Path = scopes[best_fit]
                    if (best_fit == zero_tuple) or (to == default_export):
                        cell['export_to_default'] += cell['export_to_scope']
                        pass
                    else:
                        state:dict = export_files[to]
                        if not cell['is_internal']: state['names'].update(cell['names'])
                        for _ in range(cell['export_to_scope']):
                            # TODO: implement code appending / prepending here
                            state['code'].append(f"{info_string_src}\n{relativify_imports(to, cell['processed_source_code'])}")
            else: cell['export_to_default'] += cell['export_to_scope']
                
            if cell['export_to_default'] > 0:
                if none_default:
                    raise ValueError(f'Export Target of cell {cell["cell_nr"]} is None. '\
                                     'Did you forget to add a default target using `default_exp`?')
                to = default_export
                state:dict = export_files[to]
                if not cell['is_internal']: state['names'].update(cell['names'])
                for _ in range(cell['export_to_default']):
                    # TODO: implement code appending / prepending here
                    state['code'].append(f"{info_string}\n{relativify_imports(to, cell['processed_source_code'])}")
        # NOTE: Files can't be written at this point, since there might be other notebooks exporting to the same file.
    
    # print(dict(export_files))
    for to, state in export_files.items():
        write_file(to=to, orig=state['orig'], names=state['names'], code=state['code'], st=st)
    return success


# Cell nr. 181
@traced
def main(origin_path:str=None, output_path:str=None, recurse:bool=True, st:StackTrace=None) -> bool:
    success:bool = True
    origin_path:Path = Config().nbs_path if origin_path is None else Path(origin_path).resolve()
    output_path:Path = Config().lib_path if output_path is None else Path(output_path).resolve()
    
    parse_success, parsed_files = load_and_parse_all(origin_path, output_path, recurse, st=st)
    if not parse_success:
        st.report_error(Exception('At least one Error has occured during parsing. '\
                                  'No files have been modified. Exiting.'))
        return False, parsed_files
    # NOTE: At this point all files are completely parsed, and any meta programm has run.
    
    write_success = write_out_all(parsed_files, st=st)
    if not write_success:
        st.report_error(Exception('At least one Error has occured during exporting. '\
                                  'Some files might have been written to disk and others not, '\
                                  'however no partial files have been written. Exiting.'))
        return False, parsed_files
    return success, parsed_files


# Cell nr. 183
set_arg_parse_report_options(report_error=False)
set_main_report_options(report_optional_error=False)
# AUTOGENERATED! DO NOT EDIT! View info comment on each cell for file to edit.


__all__ = ['REPORT_ERROR, REPORT_WARNING, parse_arguments, report_error, report_warning']


# Cell nr. 2; Comes from '00_export_v4.ipynb'
REPORT_ERROR:bool   = True
REPORT_WARNING:bool = True


# Cell nr. 4; Comes from '00_export_v4.ipynb'
def report_error(err:Exception):
    if REPORT_ERROR:
        err_type = err.__class__.__name__
        print(f'[{err_type}]: {err}')


# Cell nr. 5; Comes from '00_export_v4.ipynb'
def report_warning(warn:str):
    if REPORT_WARNING: print(f'[Warning]: {warn}')


# Internal Cell nr. 8; Comes from '00_export_v4.ipynb'
def get_next_argument(args:list, name:str, cursor:int, suppress_error:bool=False) -> (bool, int, str):
    "Gets the next argument from the list.\nReturns success, the cursor, and the next argument"
    cursor_1 = cursor + 1
    try: return True, cursor_1, args[cursor_1]
    except IndexError:
        if not suppress_error:
            report_error(SyntaxError(f"End of arguments reached. Missing a value for argument '{name}' at position {cursor_1}"))
        return False, cursor, ''


# Internal Cell nr. 15; Comes from '00_export_v4.ipynb'
def to_integer(value:str) -> (bool, int, float):
    "Try converting a str to int.\nReturn success, the value, and possibly a float remainder."
    try:
        f_value = float(value)
        int_value = int(f_value)
        remainder = f_value - int_value
    except: return False, value, None
    return True, int_value, remainder


# Internal Cell nr. 17; Comes from '00_export_v4.ipynb'
def to_float(value:str) -> (bool, float):
    "Try converting a str to float.\nReturn success, and the value."
    # TODO: check if 'inf', 'nan', ...?
    try   : return True , float(value)
    except: return False, value


# Internal Cell nr. 19; Comes from '00_export_v4.ipynb'
def to_bool(value:str) -> (bool, bool):
    """Try converting a str to bool.
    'True' and 'False' are recognized, otherwise the value is cast to float, and then to bool.
    Return success, and the value."""
    if value == 'True' : return True, True
    if value == 'False': return True, False
    try   : return True , bool(float(value))
    except: return False, value


# Internal Cell nr. 21; Comes from '00_export_v4.ipynb'
def to_unbounded_array(args:list, cursor:int) -> (bool, int, list):
    """Consume any number of values until either reaching the end of args,
    or until finding a value starting with '-', denoting the beginning of a new argument.
    Return success, the cursor, and the list of values.
    Currently this can't actually fail... don't use unbounded lists kids."""
    values = []
    while True:
        string_success, cursor, value = get_next_argument(args, None, cursor, suppress_error=True)
        if string_success:
            if value[0] != '-': values.append(value)
            else: # value starting with '-' means it's the next command
                cursor -= 1
                break
        else: break
    return True, cursor, values


# Internal Cell nr. 23; Comes from '00_export_v4.ipynb'
def typify(type_or_value:object) -> (type, object):
    """Takes a type or a value.
    Returns a tuple of the type (or type of the value) and value (or None)"""
    return (type_or_value, None) if isinstance(type_or_value, type) else (type(type_or_value), type_or_value)


# Cell nr. 26; Comes from '00_export_v4.ipynb'
def parse_arguments(command:dict, comment:str) -> (bool, dict, dict):
    "Finds, casts, and returns values from command, in the given comment."    
    members = command.keys()
    result  = command.copy() # copy needed?
    args    = comment.split()
    # TODO: check that the type of all commands is supported ahead of time?
    # TODO: handle quoted arguments?
    
    is_set = {member : False for member in members}
    
    state = {'args': args, 'name': '', 'cursor': 0,
             'inside_array': False,}
    
    success = True
    while state['cursor'] < len(args): # for arg in args:
        arg = args[state['cursor']]
        if arg[0] != '-':
            report_error(SyntaxError(f"Argument {state['cursor']} does not start with a '-'."))
            return False, result, is_set
        arg = arg[1:] # remove '-'
        state['name'] = arg # TODO: check that len(arg) > 0?
        
        for key in members: # loop over keys of command (the things we're supposed to find)
            if key != arg: continue    
            if is_set[key]: # TODO: improve error msg. maybe: "this is the second time this argument was given"?
                report_error(SyntaxError(f"Argument {state['cursor']} ('{arg}') was given multiple times."))
                success = False
            else:
                arg_type, arg_default = typify(command[key])
                member_success = handle_one_argument(result, state, arg_type, arg_default)
                if member_success: is_set[key] = True
                else: success = False
            break # once we have found the correct struct member, stop!
        else: # TODO: improve this msg. maybe: "is not part of the command"?
            report_error(SyntaxError(f"Argument {state['cursor']} ('{arg}') is not valid."))
            success = False
        if not success: break # stop at first error
        state['cursor'] += 1
        
    if success: success = check_is_set(result, is_set)
    return success, result, is_set


# Internal Cell nr. 27; Comes from '00_export_v4.ipynb'
def handle_one_argument(result:dict, state:dict, arg_type:type, arg_default:object) -> bool:
    "Parse the input args based on arg_type, and set arg_name in result to that value."
    # NOTE: state and result are modified from here and essentially treated as pointers
    args     = state['args']
    arg_name = state['name']
    success  = True
    if arg_type == str:
        # get the next argument, advance cursor, set success
        string_success, state['cursor'], value = get_next_argument(args, arg_name, state['cursor'])
        # TODO: how to handle strings that start with a '-'
        if string_success: result[arg_name] = value
        else: success = False

    elif arg_type == bool:
        if state['inside_array']:
            string_success, state['cursor'], value = get_next_argument(args, arg_name, state['cursor'])
            if string_success:
                bool_success, value = to_bool(value)
                if bool_success: result[arg_name] = value
                else:
                    report_error(ValueError(f"Value of argument {state['cursor']-1} ('{arg_name}') \
                    was not convertable to bool. Please use 'True', 'False', '0', or '1'. (It was '{value}')"))
                    success = False
            else: success = False
        # special case where supplying the argument means True and not supplying it means use the default (False)
        else: result[arg_name] = True

    elif arg_type == int:
        # get the next argument, cast to int, check for remainder, advance cursor, set success
        string_success, state['cursor'], value = get_next_argument(args, arg_name, state['cursor'])
        if not string_success: return False
        int_success, value, remainder = to_integer(value)
        if int_success:
            result[arg_name] = value
            if remainder:
                report_warning(f"Junk on the end of the value for int argument \
                               {state['cursor']-1} ('{arg_name}'): {remainder}")
        else:
            report_error(ValueError(f"Value of argument {state['cursor']-1} ('{arg_name}') \
                                    was not an int. (It was '{value}')"))
            success = False

    elif arg_type == float:
        # get the next argument, cast to float, advance cursor, set success
        string_success, state['cursor'], value = get_next_argument(args, arg_name, state['cursor'])
        if not string_success: return False
        float_success, value = to_float(value)
        if float_success: result[arg_name] = value
        else:
            report_error(ValueError(f"Value of argument {state['cursor']-1} ('{arg_name}') \
                                    was not a float. (It was '{value}')"))
            success = False

    elif arg_type == list or arg_type == tuple:
        if arg_default is None: # unbounded list / tuple
            if state['inside_array']:
                report_error(SyntaxError(f"Using an unbounded list or tuple inside an array is not supported."))
                return False
            
            array_success, state['cursor'], value = to_unbounded_array(args, state['cursor'])
            if array_success: # NOTE: currently this can't actually fail... don't use unbounded lists kids.
                result[arg_name] = arg_type(value)
            else: success = False
            
        else: # predefined list
            s = {'args': args, 'name': 'v', 'cursor': state['cursor'],
                 'inside_array': True}
            value = []
            for i, x in enumerate(arg_default):
                t, d = typify(x)
                n = f'{arg_name}[{i}]'
                s['name'] = n
                r = {n:d}
                member_success = handle_one_argument(r, s, t, d)
                if member_success: value.append(r[n])
                else: # TODO: Improve error message
                    # report_error(SyntaxError(f"Array argument {state['cursor']} ('{arg_name}') was not passed correctly."))
                    return False
            state['cursor'] = s['cursor']
            result[arg_name] = arg_type(value)

    else:
        report_error(TypeError(f"Argument {state['cursor']} ('{arg_name}') is of unsupported type {arg_type}."))
        success = False
        
    return success


# Internal Cell nr. 28; Comes from '00_export_v4.ipynb'
def check_is_set(result:dict, is_set:dict) -> bool:
    "Check if any required values (those without defaults), haven't been set yet"
    success = True
    for member, v_is_set in is_set.items():
        if v_is_set: continue
        arg_type, arg_default = typify(result[member])
        if arg_default is None: 
            if arg_type == bool: # NOTE: Special case, not setting a boolean means it's False.
                result[member] = False # TODO: set is_set as well? what's the use-case here?
                continue
            report_error(ValueError(f"Argument '{member}' has not been set, and no default value was given."))
            success = False
        elif (arg_type == list) or (arg_type == tuple): # this is a bounded list
            name = [f'{member}[{i}]' for i in range(len(arg_default))]
            r = {n:x for n, x in zip(name, arg_default)}
            s = {n:False for n in r}
            is_set_success = check_is_set(r, s)
            if is_set_success: # re-set result
                result[member] = arg_type([r[n] for n in name])
                continue
            else: success = False
    return success
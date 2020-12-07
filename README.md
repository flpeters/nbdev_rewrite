# Nbdev:rewrite
From the ground up rewrite of [fastai nbdev](https://github.com/fastai/nbdev) with the goal of more flexibility and reliability.  

> This is a personal project / programming exercise, and in no way affiliated with the original nbdev project.  
> For reference and the purpose of having to do less initial work, small parts have been copied from the original project.  

## How to Install

Currently only an editable pip install is supported.  
Navigate to the root directory of this repo to install or uninstall.    
To install, use:

    pip install -e .

To uninstall, use:

    pip uninstall <package-name>

or:

    python setup.py develop -u

## How to use

`nbdev_rewrite` expects a certain directory structure.  
The top level directory of your project should contain a `settings.ini`.  
You can easily create this file by runnnig:
```python
from nbdev_rewrite.main import create_config
create_config(lib_name='MY_LIB_NAME')
```
This function has many settings and is well documented.  
After running it, verify that the `settings.ini` file was created in the correct directory, and double check that the `lib_name`, `lib_path`, `nbs_path`, and `doc_path` are set correctly.  
You can also take a look at the `settings.ini` in this repo to get started.  

All the notebooks you want to have converted need to be in the `nbs_path` folder.  
The resulting .py files will be written to the `lib_path` folder.  
`doc_path` exists for compatibility with the original nbdev project. It is where generated documentation is written to.  

### How to run the conversion

After installing the `nbdev_rewrite` package via the steps above, and having created a `settings.ini` file, you can copy and paste the following lines in your main jupyter notebook.  
The package layout and names will change in the future, for now however this works.

```python
from nbdev_rewrite.main import main as convert2py, set_main_report_options

set_main_report_options(report_optional_error = False,
                        report_command_found  = False,
                        report_run_statistics = True,)

success, parsed_files, merged_files = convert2py()
```  
Running the code above will look for a `settings.ini` file in the working directory or it's parents, then recursively look for notebook files in the `nbs_path` folder and convert them to .py files, which are then written to the `lib_path` folder.  

### How to tell `nbdev_rewrite` what to export to where

`nbdev_rewrite` uses special command comments which are parsed when you run the conversion to determine which cells to export in what way, to which .py files.  

#### The command Syntax:

zero or one whitespace,  
followed by one or more literal '#',  
then again zero or one whitespace,  
then one literal '+',  
followed by the command name,  
optionally followed by space seperated arguments,  
each argument starting with a literal '-',  
then the name of that argument,  
then optionally one space, and the value of the argument.  

The following examples are syntactically valid:  
```python
#+example
# +example
##+example
 # +example
### +example

# +example -arg1 -arg2 val2
# +example -arg1 value1 -arg2 value2 -arg3 valueA valueB
```
The following examples are syntactically invalid:
```python
# example
#  +example
  #+example
# # +example

# +example +arg1
# -example -arg1
# +example -arg1 -arg1
```

#### The Commands:

Currently there are two commands: `export` and `default_exp`.  

`export`: This cell will be exported from the notebook to a .py file.  
Args:  
- `internal`: The variable, function and class names of this cell will not be added to `__all__` in the exported file, making them hidden from any `import *`.
- `to`: Instead of exporting to the notebook or scope wide default file, this cell is exported to the file specified in this argument. File is written in python module form.
- `to_path`: The same as `to`, but this argument is written as a path.
- `ignore_scope`: This cell ignores any export targets set for the scope it resides in, and instead always uses the default for the entire notebook. This argument is incompatible with `to` and `to_path`.  

`default_exp`: Set the default file that cells of this notebook will be exported to.    
Args:
- `to`: The target file written in a python module form. 
- `to_path`: The target file as a relative or absolute path.
- `scoped`: Flag for setting the export target only for the scope that the command has been invoked from. Scopes are implicitly set by markdown cells with different levels of headings.
- `no_dunder_all` : The target file will not have a `__all__` defined.  



### How to convert a `nbdev` project to `nbdev_rewrite`

To use `nbdev_rewrite` you only need to fix the comment syntax, and switch to the conversion code above. If you only use the basic exporting functionality of `nbdev`, then you won't have a problem.  

The following changes are minimally necessary:

`# export` -> `# +export`  
`# exporti` -> `# +export -internal`  
`# default_exp my_module.main` -> `# +default_exp -to my_module.main`

All `nbdev` style comment are ignored, and `nbdev` doesn't respond to `nbdev_rewrite` comments, so technically you can also use both libraries at the same time. This might be useful for the `nbdev` documentation feature, because that is not yet supported by `nbdev_rewrite`. Please note that this has not been tested, and is not actively maintained.

## Messages from the Author

> Message from Nov 07, 2020:  

The project is fairly far along at this point and has reached a state where it can easily export itself, and still work when re-imported.  
The goal of flexibility has come a long way. Program parts are clearly seperated, and something like adding an argument to a command is little more than a one line change.  
To improve reliability, a lot of effort has been and will be put into delivering high quality error messages, and logging in general. The goal here is that no error should ever pass silently. To that end, among other things, acceptable values have been clearly and rigorously defined, and those definitions are enforced as soon as possible.  
With regards to feature parity, most things in the export-to-py-part of nbdev also work here. Some things like argument parsing have, in my opinion, been greatly improved compared to the original project, and features like scoped exports don't exist in the original at all. That being said, not every feature has been brought over yet, and other parts of nbdev like the automatic testing, and creation of documentation, haven't even been looked at here.  
Next steps will be the continuous refinement of existing code, further improvement of error messages and context passing, better file management, and implementing a meta programming system.

> Message from Mar 25, 2020:  
This is not ready for production by any means, and is mainly used as a playground to test out new ideas. The target for now is to experiment with different technologies, and in the long run, to achieve feature parity, with greatly improved flexibility and reliability.  
Also, this is a personal project / programming exercise, and in no way affiliated with the original nbdev project.

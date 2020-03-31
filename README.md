# nbdev_rewrite
From the ground up rewrite of nbdev (https://github.com/fastai/nbdev) with the goal of more flexibility and reliability.

This is not ready for production by any means, and is mainly used as a playground to test out new ideas. The target for now is to experiment with different technologies, and in the long run, to achieve feature parity, with greatly improved flexibility and reliability.  
Also, this is a personal project / programming exercise.

For the purpose of having to do less work, some components are copied over from the original project.


| Feature                                                                              	| working 	| finished 	| rewritten 	|
|--------------------------------------------------------------------------------------	|:-------:	|:--------:	|:---------:	|
| __CONFIG__                                                                           	|    X    	|     X    	|     0     	|
| Config loading + parsing                                                             	|    X    	|     X    	|     0     	|
| Config generating                                                                    	|    X    	|     X    	|     0     	|
| Notebook loading                                                                     	|    X    	|     X    	|     0     	|
| __KEYWORD PARSING__                                                                  	|    X    	|     0    	|     X     	|
| Finding comments                                                                     	|    X    	|     0    	|     X     	|
| Finding specific keywords<br>in comments                                             	|    X    	|     X    	|     X     	|
| support for custom export targets                                                    	|    X    	|     0    	|     X     	|
| __KEYWORDS__                                                                         	|    X    	|     0    	|     X     	|
| `# export`                                                                           	|    X    	|     0    	|     X     	|
| `# export`options parsing (internal and export target)                               	|    X    	|     0    	|     X     	|
| `# hide`                                                                             	|    X    	|     X    	|     X     	|
| `# default_exp`                                                                      	|    0    	|          	|           	|
| __FORMATTING / CLEANUP__                                                             	|    X    	|     0    	|     X     	|
| removing special comments in output                                                  	|    X    	|     X    	|     X     	|
| change inter-project imports to<br>relative imports after the export                 	|    X    	|     0    	|     0     	|
| __`__all__` NAME PARSING__                                                           	|    X    	|     X    	|     X     	|
| finding all variable, class, and function names<br>that should be added to `__all__` 	|    X    	|     X    	|     X     	|
| ignore private names (start with one "\_", and not "\_\_")<br>and internal cells     	|    X    	|     X    	|     X     	|
| find `_all_` variables in code and<br>add content of assignment to `__all__`         	|    X    	|     X    	|     X     	|
| support for fastai added python functionality: `@patch`                              	|    X    	|     X    	|     X     	|
| support for fastai added python functionality: `@typedispatch`                       	|    X    	|     X    	|     X     	|
| __CAN GENERATE WORKING OUTPUT__                                                      	|    X    	|     0    	|     X     	|
| export from a single file to a single file                                           	|    X    	|     0    	|     X     	|
| export from a single file to multiple files                                          	|    0    	|          	|           	|
| export all files in a folder                                                         	|    0    	|          	|           	|
| export a directory recursively                                                       	|    0    	|          	|           	|
>X = yes; 0 = no
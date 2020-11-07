# Nbdev:rewrite
From the ground up rewrite of [fastai nbdev](https://github.com/fastai/nbdev) with the goal of more flexibility and reliability.  

> This is a personal project / programming exercise, and in no way affiliated with the original nbdev project.  
> For reference and the purpose of having to do less initial work, small parts have been copied from the original project.  

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

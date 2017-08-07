ipython profile create default

del %HOME%\.ipython\profile_default\startup\startup.ipy 
mklink /h %HOME%\.ipython\profile_default\startup\startup.ipy .\startup.ipy

jupyter notebook --config=config.py


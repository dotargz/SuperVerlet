# SuperVerlet
a simple verlet implementaion in somewhat of a game form

## how to run
go to the [releases](https://github.com/dotargz/SuperVerlet/releases) and donwload the exe, or clone the repo and run superverlet.py

## command line arguments
basic usage: superverlet.py [-h] [-w WIDTH] [-l HEIGHT] [-d] [-f FPS] [-g GRAVITY] [-s] [-r RADIUS] [-t DELTATIME] [--use-experimental-rendering]
```
-h, --help: show help message and exit 
-w WIDTH, --width WIDTH: Width of the window 
-l HEIGHT, --height HEIGHT: Height of the window 
-d, --debug: Enable debug mode on startup 
-f FPS, --fps FPS: Frames per second 
-g GRAVITY, --gravity GRAVITY: Amount of gravity applied to the each object 
-s, --sound: Enable sound 
-r RADIUS, --radius RADIUS: Radius of all the circles
-t DELTATIME, --deltatime DELTATIME: Delta time for the simulation
--use-experimental-rendering: Use experimental rendering
```
*my favorite combo is ``superverlet.py --gravity 10 --sound --debug --use-experimental-rendering``*

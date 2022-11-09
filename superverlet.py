import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from pygame import gfxdraw
import sys
import argparse
import uuid
import math
import numpy as np

parser = argparse.ArgumentParser("superverlet.py")
parser.add_argument("-w", "--width", type=int, default=852,
                    help="Width of the window")
parser.add_argument("-l", "--height", type=int,
                    default=480, help="Height of the window")
parser.add_argument("-d", "--debug", action="store_true",
                    help="Enable debug mode on startup")
parser.add_argument("-f", "--fps", type=int, default=60,
                    help="Frames per second")
parser.add_argument("-g", "--gravity", type=float, default=9.81,
                    help="Amount of gravity applied to the each object")
parser.add_argument("-s", "--sound", action="store_true",
                    help="Enable sound")
parser.add_argument("-r", "--radius", type=int, default=16,
                    help="Radius of all the circles")
parser.add_argument("-t", "--deltatime", type=float, default=(1/60),
                    help="Delta time for the simulation")
parser.add_argument("--use-experimental-rendering", action="store_true",
                    help="Use experimental rendering")
ARGS = parser.parse_args()
print("Launching SuperVerlet with the following arguments:")
for k, v in parser.parse_args().__dict__.items():
    print('%s: %s' % (k, v))

pygame.init()


# Compilation Setup
def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Window setup
DISPLAYSURF = pygame.display.set_mode(
    (ARGS.width, ARGS.height), pygame.RESIZABLE)
SCREEN_WIDTH, SCREEN_HEIGHT = DISPLAYSURF.get_size()

try:
    logo = pygame.image.load(resource_path("assets/img/logo.png"))
    pygame.display.set_icon(logo)
except:
    pass

pygame.display.set_caption("SuperVerlet v1.3.0 (beta)")

# Initial FPS setup
FPS = ARGS.fps
FramePerSec = pygame.time.Clock()

# Global variables
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

try:
    FONT = pygame.font.Font(resource_path(
        'assets/fonts/UbuntuMono-Bold.ttf'), 32)
except:
    FONT = pygame.font.SysFont('Monospace', 32)

DEBUG = ARGS.debug

# UI Setup
# Render on the top left corner, and account for rectangle size

Objcounter = FONT.render('Objects:', True, BLACK, WHITE)
ObjcounterRect = Objcounter.get_rect()
ObjcounterRect.center = ((ObjcounterRect.width/2)+4, ObjcounterRect.height/2)

fpsCounter = FONT.render('FPS:', True, BLACK, WHITE)
fpsCounterRect = fpsCounter.get_rect()
fpsCounterRect.center = ((fpsCounterRect.width/2)+4,
                         (fpsCounterRect.height/2)+ObjcounterRect.height)

dtCounter = FONT.render('dt:', True, BLACK, WHITE)
dtCounterRect = dtCounter.get_rect()
dtCounterRect.center = ((dtCounterRect.width/2)+4,
                        (dtCounterRect.height/2)+fpsCounterRect.height+ObjcounterRect.height)


# Sound Setup
try:
    if ARGS.sound:
        spawn_sound = pygame.mixer.Sound(
            resource_path('assets/sounds/spawn.wav'))
        spawn_sound.set_volume(0.05)
except:
    pass


# Function setup
def totuple(a):
    try:
        return tuple(totuple(i) for i in a)
    except TypeError:
        return a


def draw_circle(surface, x, y, radius, color):
    if ARGS.use_experimental_rendering:
        gfxdraw.aacircle(surface, int(x), int(y), int(radius), color)
        gfxdraw.filled_circle(surface, int(x), int(y), int(radius), color)
    else:
        pygame.draw.circle(surface, color, (x, y), radius)

# Circle (Physics object)


class Circle(pygame.sprite.Sprite):
    def __init__(self, starting_pos=[SCREEN_WIDTH/2, SCREEN_HEIGHT/2]):
        super().__init__()
        self.radius = ARGS.radius
        self.starting_pos = starting_pos
        self.position_current = np.array(starting_pos)
        self.position_old = np.array(starting_pos)
        self.acceleration = np.array(starting_pos)

    def updatePosition(self, dt):
        velocity = self.position_current - self.position_old
        # save current position
        self.position_old = self.position_current
        # perform verlet
        self.position_current = self.position_current + \
            velocity + self.acceleration * dt * dt

        # reset acceleration
        self.acceleration = np.array([0, 0])

    def accelerate(self, acc):
        self.acceleration = self.acceleration + acc

    def draw(self, surface):
        draw_circle(
            surface, self.position_current[0], self.position_current[1], self.radius, WHITE)
        if DEBUG:
            self.drawvelocity(surface, 3, RED)

    def drawvelocity(self, surface, multiplier=1, color=RED):
        pygame.draw.line(surface, color, self.position_current, totuple(
            self.position_current + (self.position_current*multiplier - self.position_old*multiplier)), 2)

# Physics Solver


class Solver():
    def __init__(self, gravity):
        self.gravity = np.array(gravity)

    def update(self, dt):
        self.applyGravity()
        self.applyConstraint()
        self.solveCollisions()
        self.updatePositions(dt)

    def getInstances(self, of_class=None):
        instances = []
        for obj in objects:
            instances.append(objects[obj])
        return instances

    def applyGravity(self):
        for obj in self.getInstances():
            obj.accelerate(self.gravity)

    def updatePositions(self, dt):
        for obj in self.getInstances():
            obj.updatePosition(dt)

    def applyConstraint(self):
        position = np.array([SCREEN_WIDTH/2, SCREEN_HEIGHT/2])
        radius = SCREEN_HEIGHT/2.4
        for obj in self.getInstances():
            to_obj = obj.position_current - position
            dist = np.sqrt((to_obj[0]*to_obj[0])+(to_obj[1]*to_obj[1]))
            # 32 is default radius
            if (dist > radius - ARGS.radius):
                n = to_obj / dist
                obj.position_current = position + n * (radius - ARGS.radius)

    # very inefficient collision detection, but it works
    # we also add a small offset to the radius to prevent objects from overlapping a little when using experimental rendering
    def solveCollisions(self):
        object_container = self.getInstances()
        object_count = len(object_container)
        for i in range(object_count):
            for k in range(i+1, object_count):
                collision_axis = object_container[i].position_current - \
                    object_container[k].position_current
                dist = np.sqrt(
                    (collision_axis[0]*collision_axis[0])+(collision_axis[1]*collision_axis[1]))
                if dist < ARGS.radius*2+ERO:
                    n = collision_axis / dist
                    delta = ARGS.radius*2+ERO - dist
                    object_container[i].position_current = object_container[i].position_current + 0.25 * delta * n
                    object_container[k].position_current = object_container[k].position_current - 0.25 * delta * n


# Runtime Settings
dt = ARGS.deltatime
Running = True

# experimental rendering offset
ERO = 0.1
if ARGS.use_experimental_rendering:
    ERO = 1

# Definitions
objects = {}
SOLVER = Solver(gravity=[0, ARGS.gravity*100])

while Running:
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                pos = pygame.mouse.get_pos()
                pos = np.asarray(pos)
                objects[uuid.uuid4()] = Circle(pos)
                if ARGS.sound:
                    pygame.mixer.Sound.play(spawn_sound)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_r:
                objects = {}
            if event.key == pygame.K_d:
                DEBUG = not DEBUG
        if event.type == pygame.QUIT:
            Running = False

    SCREEN_WIDTH, SCREEN_HEIGHT = DISPLAYSURF.get_size()

    SOLVER.update(dt)

    DISPLAYSURF.fill(WHITE)

    draw_circle(DISPLAYSURF, SCREEN_WIDTH/2, SCREEN_HEIGHT/2,
                SCREEN_HEIGHT/2.4, BLACK)

    if DEBUG:

        Objcounter = FONT.render(
            f'Objects: {len(objects)}', True, BLACK, WHITE)
        DISPLAYSURF.blit(Objcounter, ObjcounterRect)

        fpsCounter = FONT.render(
            f'FPS: {int(FramePerSec.get_fps())}', True, BLACK, WHITE)
        DISPLAYSURF.blit(fpsCounter, fpsCounterRect)

        dtCounter = FONT.render(f'DT: {round(dt, 5)}', True, BLACK, WHITE)
        DISPLAYSURF.blit(dtCounter, dtCounterRect)

    # cursor (hollow circle)
    draw_circle(DISPLAYSURF, *pygame.mouse.get_pos(), ARGS.radius, WHITE)
    gfxdraw.aacircle(DISPLAYSURF, *pygame.mouse.get_pos(),
                     ARGS.radius+1, BLACK)

    for obj in SOLVER.getInstances():
        obj.draw(DISPLAYSURF)

    pygame.display.update()
    FramePerSec.tick(FPS)

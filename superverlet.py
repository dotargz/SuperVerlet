import pygame
import sys
import argparse
import uuid
import math
import os
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
ARGS = parser.parse_args()
print("Launching SuperVerlet with the following arguments:")
for k,v in parser.parse_args().__dict__.items():
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
logo = pygame.image.load(resource_path("assets/img/logo.png"))
pygame.display.set_icon(logo)
pygame.display.set_caption("SuperVerlet v1.2.1 (beta)")

# Initial FPS setup
FPS = ARGS.fps
FramePerSec = pygame.time.Clock()

# Global variables
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FONT = pygame.font.Font(resource_path('assets/fonts/UbuntuMono-Bold.ttf'), 32)
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

# Cursor setup
cursor = pygame.sprite.Sprite()
cursor.image = pygame.image.load(resource_path("assets/img/cursor.png"))
cursor.rect = cursor.image.get_rect()
cursor.rect.center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)


# Sound Setup
spawn_sound = pygame.mixer.Sound(resource_path('assets/sounds/spawn.wav'))


# Function setup
def totuple(a):
    try:
        return tuple(totuple(i) for i in a)
    except TypeError:
        return a

# Circle (Physics object)


class Circle(pygame.sprite.Sprite):
    def __init__(self, starting_pos=[SCREEN_WIDTH/2, SCREEN_HEIGHT/2]):
        super().__init__()
        self.image = pygame.image.load(resource_path("assets/img/circle.png"))
        self.rect = self.image.get_rect()
        self.starting_pos = starting_pos
        self.rect.center = totuple(starting_pos)
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

        self.rect.center = totuple(self.position_current)

        # reset acceleration
        self.acceleration = np.array([0, 0])

    def accelerate(self, acc):
        self.acceleration = self.acceleration + acc

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if DEBUG:
            self.drawvelocity(surface, 2, RED)

    def drawvelocity(self, surface, multiplier=1, color=RED):
        pygame.draw.line(surface, color, self.rect.center, totuple(
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
            if (dist > radius - 16):
                n = to_obj / dist
                obj.position_current = position + n * (radius - 16)

    # very inefficient collision detection
    def solveCollisions(self):
        object_container = self.getInstances()
        object_count = len(object_container)
        for i in range(object_count):
            for k in range(i+1, object_count):
                collision_axis = object_container[i].position_current - \
                    object_container[k].position_current
                dist = np.sqrt(
                    (collision_axis[0]*collision_axis[0])+(collision_axis[1]*collision_axis[1]))
                if dist < 32:
                    n = collision_axis / dist
                    delta = 32 - dist
                    object_container[i].position_current = object_container[i].position_current + 0.25 * delta * n
                    object_container[k].position_current = object_container[k].position_current - 0.25 * delta * n


# Runtime Settings
dt = 1/60
Running = True

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

    pygame.draw.circle(DISPLAYSURF, BLACK, (SCREEN_WIDTH/2,
                       SCREEN_HEIGHT/2), SCREEN_HEIGHT/2.4)

    if DEBUG:

        Objcounter = FONT.render(
            f'Objects: {len(objects)}', True, BLACK, WHITE)
        DISPLAYSURF.blit(Objcounter, ObjcounterRect)

        fpsCounter = FONT.render(
            f'FPS: {int(FramePerSec.get_fps())}', True, BLACK, WHITE)
        DISPLAYSURF.blit(fpsCounter, fpsCounterRect)

        dtCounter = FONT.render(f'DT: {round(dt, 5)}', True, BLACK, WHITE)
        DISPLAYSURF.blit(dtCounter, dtCounterRect)

    cursor.rect.center = pygame.mouse.get_pos()
    DISPLAYSURF.blit(cursor.image, cursor.rect)

    for obj in SOLVER.getInstances():
        obj.draw(DISPLAYSURF)

    pygame.display.update()
    FramePerSec.tick(FPS)

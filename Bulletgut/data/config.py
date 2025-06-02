# CONFIG VARIABLES FOR THE GAME
import math

# General settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 64

# Player settings
PLAYER_SPEED = 450
MOUSE_SENSITIVITY = 0.025
MOUSE_SENSITIVITY_MULTIPLIER = 1.0
MOUSE_DEADZONE = 0.05
ROTATE_SPEED = MOUSE_SENSITIVITY * 60
FOV = math.pi / 3 # 60 degrees

# Level settings
WALL_HEIGHT_SCALE = 1.7
PLAYER_COLLISION_RADIUS = TILE_SIZE * 0.3  # 30% of tile size
PICKUP_SCALE = 0.8           # influence la taille en fonction de la distance


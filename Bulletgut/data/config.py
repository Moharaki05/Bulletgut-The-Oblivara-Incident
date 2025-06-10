# CONFIG VARIABLES FOR THE GAME
import math

# General settings
HUD_HEIGHT = 128
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720 + HUD_HEIGHT
FPS = 60
TILE_SIZE = 64

# Player settings
PLAYER_SPEED = 450

MOUSE_SENSITIVITY = 0.02  # Increased from 0.0098 but reasonable
MOUSE_SENSITIVITY_EXPONENT = 1.0  # Linear response (was 1.25)
MOUSE_DEADZONE = 0.5  # Reduced deadzone (was 1)

ROTATE_SPEED = MOUSE_SENSITIVITY * 60
FOV = math.pi / 3

# Level settings
WALL_HEIGHT_SCALE = 1.7
PLAYER_COLLISION_RADIUS = TILE_SIZE * 0.3
PICKUP_SCALE = 0.8

# Gameplay settings
WEAPON_SLOTS = {
    "chainsaw": 0,
    "fists": 1,
    "pistol": 2,
    "shotgun": 3,
    "chaingun": 4,
    "rocketlauncher": 5,
    "plasmagun": 6,
    "bfg": 7
}

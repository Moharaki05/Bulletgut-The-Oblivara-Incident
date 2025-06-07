import os
import pygame
import re
from collections import defaultdict

_image_cache = {}
_sound_cache = {}

state_aliases = {
    "movement": "move",
    "idle": "idle",
    "attack": "attack",
    "hit": "hit",
    "death": "death"
}

def load_image(path):
    """Charge une image avec cache. Retourne une surface vide en cas d’erreur."""
    if path not in _image_cache:
        try:
            _image_cache[path] = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"[Erreur image] {path} : {e}")
            _image_cache[path] = pygame.Surface((16, 16), pygame.SRCALPHA)  # fallback vide
    return _image_cache[path]

def load_sound(path):
    """Charge un son avec cache. Retourne None en cas d’erreur."""
    if path not in _sound_cache:
        try:
            _sound_cache[path] = pygame.mixer.Sound(path)
        except Exception as e:
            print(f"[Erreur son] {path} : {e}")
            _sound_cache[path] = None
    return _sound_cache[path]

def load_images(folder_path):
    """Charge toutes les images d’un dossier, triées par nom."""
    images = []
    if not os.path.isdir(folder_path):
        print(f"[Erreur dossier images] Inexistant : {folder_path}")
        return images

    files = sorted(os.listdir(folder_path))
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.bmp')):
            full_path = os.path.join(folder_path, file)
            images.append(load_image(full_path))

    if not images:
        print(f"[Avertissement] Aucune image dans : {folder_path}")
    return images

def load_animation_set(folder):
    from collections import defaultdict
    animations = defaultdict(lambda: defaultdict(list))

    direction_map = {
        "Front": 0,
        "FrontRight": 1,
        "Right": 2,
        "BackRight": 3,
        "Back": 4,
        "BackLeft": 5,
        "Left": 6,
        "FrontLeft": 7
    }

    # print(f"[DEBUG] → load_animation_set appelé avec {folder}")

    for root, _, files in os.walk(folder):
        for filename in sorted(files):
            if not filename.endswith(".png"):
                continue

            full_path = os.path.join(root, filename)
            print(f"[DEBUG] Analyse de {full_path}")
            image = load_image(full_path)

            # 1. Death_RegularX.png, Death_BerserkX.png
            match_death = re.match(r"Death_(Regular|Berserk)(\d+)\.png", filename, re.IGNORECASE)
            if match_death:
                subtype, frame = match_death.groups()
                if subtype.lower() == "regular":
                    animations["death"][-1].append(image)
                continue

            # 2. Move_Front1.png etc.
            match_move = re.match(r"(\w+)_([A-Za-z]+)(\d+)\.png", filename)
            if match_move:
                state, direction_str, frame_num = match_move.groups()
                direction = direction_map.get(direction_str)
                if direction is not None:
                    animations[state.lower()][direction].append(image)
                continue

            # 3. Idle_Front.png etc.
            match_static = re.match(r"(\w+)_([A-Za-z]+)\.png", filename)
            if match_static:
                state, direction_str = match_static.groups()
                direction = direction_map.get(direction_str)
                if direction is not None:
                    animations[state.lower()][direction].append(image)
                continue

    return animations

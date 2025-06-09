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
    """Charge une image avec cache. Retourne une surface vide en cas d'erreur."""
    if path not in _image_cache:
        try:
            # FIXED: Load and convert properly without changing size
            loaded_image = pygame.image.load(path)
            original_size = loaded_image.get_size()

            # Convert to proper format for better performance
            converted_image = loaded_image.convert_alpha()

            # CRITICAL CHECK: Ensure conversion didn't change size
            if converted_image.get_size() != original_size:
                print(f"[ERROR] Size mismatch after conversion for {path}")
                print(f"  Original: {original_size}, Converted: {converted_image.get_size()}")
                # Use original if size changed
                _image_cache[path] = loaded_image
            else:
                _image_cache[path] = converted_image

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

    for root, _, files in os.walk(folder):
        for filename in sorted(files):
            if not filename.endswith(".png"):
                continue

            full_path = os.path.join(root, filename)
            print(f"[DEBUG] Analyse de {full_path}")

            # FIXED: Load image without any modifications
            image = load_image(full_path)

            # CRITICAL FIX: Ensure the image is properly converted and not scaled
            # Make sure we're working with the original sprite dimensions
            if image:
                # Convert to display format but preserve original size
                original_size = image.get_size()
                image = image.convert_alpha()
                # Verify size wasn't changed during conversion
                if image.get_size() != original_size:
                    print(f"[WARNING] Image size changed during conversion: {filename}")
                    print(f"  Original: {original_size}, New: {image.get_size()}")

            # 1. Death_RegularX.png, Death_BerserkX.png
            match_death = re.match(r"Death_(Regular|Berserk)(\d+)\.png", filename, re.IGNORECASE)
            if match_death:
                subtype, frame = match_death.groups()
                if subtype.lower() == "regular":
                    # FIXED: Store death frames with frame number for proper ordering
                    frame_num = int(frame)
                    # Ensure we have enough slots in the list
                    while len(animations["death"][-1]) <= frame_num:
                        animations["death"][-1].append(None)
                    animations["death"][-1][frame_num] = image
                    print(f"[DEATH FRAME] Added frame {frame_num} for death animation")
                continue

            # 2. Move_Front1.png etc.
            match_move = re.match(r"(\w+)_([A-Za-z]+)(\d+)\.png", filename)
            if match_move:
                state, direction_str, frame_num = match_move.groups()
                direction = direction_map.get(direction_str)
                if direction is not None:
                    frame_idx = int(frame_num) - 1  # Convert to 0-based index
                    # Ensure we have enough slots
                    while len(animations[state.lower()][direction]) <= frame_idx:
                        animations[state.lower()][direction].append(None)
                    animations[state.lower()][direction][frame_idx] = image
                continue

            # 3. Idle_Front.png etc.
            match_static = re.match(r"(\w+)_([A-Za-z]+)\.png", filename)
            if match_static:
                state, direction_str = match_static.groups()
                direction = direction_map.get(direction_str)
                if direction is not None:
                    animations[state.lower()][direction].append(image)
                continue

    # CRITICAL FIX: Clean up death animation list by removing None entries
    if "death" in animations and -1 in animations["death"]:
        # Remove None entries and ensure proper ordering
        death_frames = [frame for frame in animations["death"][-1] if frame is not None]
        animations["death"][-1] = death_frames
        print(f"[DEATH CLEANUP] Final death frames count: {len(death_frames)}")

        # Debug: Print size of each death frame to detect scaling issues
        for i, frame in enumerate(death_frames):
            if frame:
                print(f"[DEATH FRAME {i}] Size: {frame.get_size()}")

    print("Frames HIT =", animations.get("hit"))
    return animations


def load_animation():
    return None
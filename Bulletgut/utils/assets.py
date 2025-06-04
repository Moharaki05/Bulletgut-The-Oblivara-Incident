import pygame
import os

_image_cache = {}
_sound_cache = {}

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

def load_animation_set(base_folder):
    """
    Charge toutes les animations d’un ennemi :
    - base_folder doit contenir des sous-dossiers nommés : idle/, move/, attack/, death/, etc.
    - Chaque sous-dossier contient des images triées automatiquement
    Retourne : { 'idle': [img1, img2...], 'attack': [...] }
    """
    animation_set = {}
    if not os.path.isdir(base_folder):
        print(f"[Erreur animations] Dossier manquant : {base_folder}")
        return animation_set

    for state in os.listdir(base_folder):
        state_folder = os.path.join(base_folder, state)
        if os.path.isdir(state_folder):
            animation_set[state] = load_images(state_folder)

    return animation_set

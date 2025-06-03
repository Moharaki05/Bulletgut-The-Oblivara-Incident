import pygame as pg
import os

class FaceManager:
    def __init__(self, base_path="assets/ui/faces"):
        self.standard_faces = {i: [] for i in range(1, 6)}  # 5 états
        self.hurt_faces = {}
        self.evil_faces = {}
        self.dead_face = None

        for filename in os.listdir(base_path):
            path = os.path.join(base_path, filename)
            if not filename.lower().endswith(".png"):
                continue

            if filename.startswith("face_dead"):
                self.dead_face = pg.image.load(path).convert_alpha()

            elif filename.startswith("face_hurt"):
                idx = int(filename.replace("face_hurt", "").replace(".png", ""))
                self.hurt_faces[idx] = pg.image.load(path).convert_alpha()

            elif filename.startswith("face_evil"):
                idx = int(filename.replace("face_evil", "").replace(".png", ""))
                self.evil_faces[idx] = pg.image.load(path).convert_alpha()

            elif filename.startswith("face"):
                idx = int(filename.replace("face", "").replace(".png", ""))
                state = (idx - 1) // 3 + 1  # 1 à 5
                self.standard_faces[state].append(pg.image.load(path).convert_alpha())

    def get_health_state(self, health):
        if health > 80:
            return 1
        elif health > 60:
            return 2
        elif health > 40:
            return 3
        elif health > 20:
            return 4
        else:
            return 5

    def get_face(self, player):
        now = pg.time.get_ticks()
        health = player.health
        state = self.get_health_state(health)

        if health <= 0:
            return self.dead_face

        if (getattr(player, "was_hit_until", 0) or 0) > now:
            return self.hurt_faces.get(state)

        if (getattr(player, "got_weapon_until", 0) or 0) > now:
            return self.evil_faces.get(state)

        frame = (now // 250) % 3
        return self.standard_faces[state][frame]

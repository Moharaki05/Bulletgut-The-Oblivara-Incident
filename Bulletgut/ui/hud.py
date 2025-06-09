import pygame as pg
from ui.faces import FaceManager
from ui.messages import MessageManager

SCREEN_WIDTH = 1280
HUD_HEIGHT = 128
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

class HUD:
    def __init__(self, screen):
        self.screen = screen
        self.hud_image = pg.transform.scale(pg.image.load("assets/ui/StatsBar.png").convert(), (SCREEN_WIDTH, HUD_HEIGHT))
        self.doom_font_big = pg.font.SysFont("consolas", 60, bold=True)
        self.doom_font_small = pg.font.SysFont("consolas", 20, bold=True)
        self.face_manager = FaceManager()
        self.messages = MessageManager()
        self.last_rendered_surface = None
        KEY_ICON_SIZE = (28, 20)
        self.key_icons = {
            "red": pg.transform.scale(pg.image.load("assets/ui/keys/key_red_ui.png").convert_alpha(), KEY_ICON_SIZE),
            "blue": pg.transform.scale(pg.image.load("assets/ui/keys/key_blue_ui.png").convert_alpha(), KEY_ICON_SIZE),
            "yellow": pg.transform.scale(pg.image.load("assets/ui/keys/key_yellow_ui.png").convert_alpha(), KEY_ICON_SIZE)
        }

    @staticmethod
    def blit_centered_text(surf, text, rect):
        text_rect = text.get_rect(center=rect.center)
        surf.blit(text, text_rect)

    def render(self, player, game):
        self.screen.blit(self.hud_image, (0, 720))

        # Ammo, health, armor (grands chiffres)
        weapon = player.weapon
        ammo_type = weapon.ammo_type if weapon and hasattr(weapon, "ammo_type") else None
        ammo = player.ammo.get(ammo_type, 0) if ammo_type else 0
        max_ammo = player.max_ammo.get(ammo_type, 0) if ammo_type else 0

        health = int(player.health)
        armor = int(player.armor)

        zones = {
            "ammo": (ammo, pg.Rect(115, 720 + 33, 100, 40)),
            "health": (f"{health}%", pg.Rect(312, 720 + 33, 120, 40)),
            "armor": (f"{armor}%", pg.Rect(705, 720 + 33, 120, 40))
        }

        for key, (text_val, rect) in zones.items():
            text = self.doom_font_big.render(str(text_val), True, RED)
            self.blit_centered_text(self.screen, text, rect)

        # Visage
        face_img = self.face_manager.get_face(player)
        if face_img:
            scaled = pg.transform.scale(face_img, (84, 105))
            self.screen.blit(scaled, (530, 720 + 18))

        # Munitions par type (texte petit)
        ammo_display_y = {
            "bullets": 720 + 23,
            "shells": 720 + 48,
            "rockets": 720 + 73,
            "cells": 720 + 98,
        }

        for ammo_type, y in ammo_display_y.items():
            current = player.ammo.get(ammo_type, 0)
            maximum = player.max_ammo.get(ammo_type, 0)
            left = pg.Rect(1020, y, 70, 20)
            right = pg.Rect(1115, y, 70, 20)
            self.blit_centered_text(self.screen, self.doom_font_small.render(str(current), True, YELLOW), left)
            self.blit_centered_text(self.screen, self.doom_font_small.render(str(maximum), True, YELLOW), right)

        if not game.player.alive:
            self.last_rendered_surface = self.screen.subsurface(pg.Rect(0, 720, 1280, 128)).copy()

        self.messages.render(self.screen)

        # Affichage des clés dans les emplacements DOOM
        base_x = 890  # ajuster selon ton image StatsBar
        base_y = 775  # 720 + 18 pour le centre du slot

        if "red" in player.keys:
            self.screen.blit(self.key_icons["red"], (base_x, base_y - 40))  # haut
        if "blue" in player.keys:
            self.screen.blit(self.key_icons["blue"], (base_x, base_y))  # milieu
        if "yellow" in player.keys:
            self.screen.blit(self.key_icons["yellow"], (base_x, base_y + 40))  # bas


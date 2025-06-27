import pygame as pg
import math
import random
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT


class LoadingScreen:
    def __init__(self):
        self.font_large = pg.font.Font("assets/fonts/DooM.ttf", 36)
        self.font_medium = pg.font.Font("assets/fonts/DooM.ttf", 24)
        self.font_small = pg.font.Font("assets/fonts/Born2bSportyFS.otf", 18)

        # Couleurs
        self.bg_color = (16, 16, 24)  # Bleu très foncé
        self.text_color = (255, 255, 255)
        self.accent_color = (255, 64, 64)  # Rouge
        self.bar_bg_color = (64, 64, 80)
        self.bar_fill_color = (255, 128, 128)

        # Charger le logo
        self.logo = None
        self.logo_scale = 1.0
        self.fallback_title = False

        try:
            # Essayer de charger le logo depuis le même chemin que le menu principal
            self.logo = pg.image.load("assets/ui/logo.png").convert_alpha()
            # Redimensionner le logo pour l'écran de chargement (un peu plus petit que dans le menu)
            logo_width = min(450, SCREEN_WIDTH - 100)  # Plus petit que dans le menu
            logo_height = int(self.logo.get_height() * (logo_width / self.logo.get_width()))
            self.logo = pg.transform.scale(self.logo, (logo_width, logo_height))

            # Position du logo (centré horizontalement)
            self.logo_x = SCREEN_WIDTH // 2 - self.logo.get_width() // 2
            self.logo_y = SCREEN_HEIGHT // 3 - self.logo.get_height() // 2

            print("[LOADING_SCREEN] Logo loaded successfully")
        except FileNotFoundError:
            # Fallback vers le texte si le logo n'existe pas
            self.fallback_title = True
            print("[LOADING_SCREEN] Logo not found, using text fallback")

        # Animation
        self.progress = 0.0
        self.target_progress = 0.0
        self.animation_time = 0.0
        self.dots_animation = 0.0
        self.pulse_animation = 0.0

        # États de chargement
        self.loading_steps = [
            "Initializing game engine...",
            "Loading textures...",
            "Building level geometry...",
            "Spawning entities...",
            "Loading audio...",
            "Finalizing..."
        ]
        self.current_step = 0
        self.step_duration = 0.3  # Durée de chaque étape en secondes
        self.step_timer = 0.0

        # Particules d'arrière-plan
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'x': pg.math.Vector2(
                    random.randint(0, SCREEN_WIDTH),
                    random.randint(0, SCREEN_HEIGHT)
                ),
                'velocity': pg.math.Vector2(
                    random.uniform(-20, 20),
                    random.uniform(-20, 20)
                ),
                'size': random.uniform(1, 3),
                'alpha': random.randint(30, 80)
            })

        self.is_complete = False
        self.fade_out_timer = 0.0
        self.fade_duration = 0.5

    def start_loading(self):
        """Démarre le processus de chargement"""
        self.progress = 0.0
        self.target_progress = 0.0
        self.current_step = 0
        self.step_timer = 0.0
        self.animation_time = 0.0
        self.is_complete = False
        self.fade_out_timer = 0.0

    def update(self, dt):
        """Met à jour l'animation de chargement"""
        self.animation_time += dt
        self.dots_animation += dt * 3
        self.pulse_animation += dt * 2

        # Mettre à jour les particules
        for particle in self.particles:
            particle['x'] += particle['velocity'] * dt

            # Wrap around screen
            if particle['x'].x < 0:
                particle['x'].x = SCREEN_WIDTH
            elif particle['x'].x > SCREEN_WIDTH:
                particle['x'].x = 0
            if particle['x'].y < 0:
                particle['x'].y = SCREEN_HEIGHT
            elif particle['x'].y > SCREEN_HEIGHT:
                particle['x'].y = 0

        # Progression automatique des étapes
        self.step_timer += dt
        if self.step_timer >= self.step_duration and self.current_step < len(self.loading_steps):
            self.step_timer = 0.0
            self.current_step += 1
            self.target_progress = self.current_step / len(self.loading_steps)

        # Animation fluide de la barre de progression
        if self.progress < self.target_progress:
            self.progress = min(self.target_progress, self.progress + dt * 2)

        # Démarrer le fade out quand le chargement est terminé
        if self.progress >= 1.0 and not self.is_complete:
            self.is_complete = True

        if self.is_complete:
            self.fade_out_timer += dt

    def is_finished(self):
        """Retourne True si le chargement et le fade out sont terminés"""
        return self.is_complete and self.fade_out_timer >= self.fade_duration

    def get_alpha(self):
        """Retourne l'alpha pour le fade out"""
        if not self.is_complete:
            return 255
        fade_progress = min(1.0, self.fade_out_timer / self.fade_duration)
        return int(255 * (1.0 - fade_progress))

    def render_logo_with_pulse(self, surface):
        """Affiche le logo avec effet de pulse"""
        if self.logo and not self.fallback_title:
            # Effet de pulse sur le logo
            pulse_scale = 1.0 + 0.03 * math.sin(self.pulse_animation)  # Pulse plus subtil pour le logo

            # Redimensionner temporairement le logo pour l'effet de pulse
            current_width = int(self.logo.get_width() * pulse_scale)
            current_height = int(self.logo.get_height() * pulse_scale)
            pulsed_logo = pg.transform.scale(self.logo, (current_width, current_height))

            # Recentrer le logo pulsé
            logo_x = SCREEN_WIDTH // 2 - current_width // 2
            logo_y = SCREEN_HEIGHT // 3 - current_height // 2

            surface.blit(pulsed_logo, (logo_x, logo_y))
        else:
            # Fallback vers le texte avec pulse
            pulse_scale = 1.0 + 0.05 * math.sin(self.pulse_animation)
            title_font = pg.font.Font("assets/fonts/DooM.ttf", int(48 * pulse_scale))
            title_text = title_font.render("BULLETGUT", True, self.accent_color)
            subtitle_text = self.font_medium.render("THE OBLIVARA INCIDENT", True, self.text_color)

            title_x = SCREEN_WIDTH // 2 - title_text.get_width() // 2
            title_y = SCREEN_HEIGHT // 3 - title_text.get_height() // 2

            subtitle_x = SCREEN_WIDTH // 2 - subtitle_text.get_width() // 2
            subtitle_y = title_y + title_text.get_height() + 10

            surface.blit(title_text, (title_x, title_y))
            surface.blit(subtitle_text, (subtitle_x, subtitle_y))

    def render(self, screen):
        """Affiche l'écran de chargement"""
        alpha = self.get_alpha()
        if alpha <= 0:
            return

        # Créer une surface temporaire pour l'alpha
        temp_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        temp_surface.fill(self.bg_color)

        # Particules d'arrière-plan
        for particle in self.particles:
            color = (*self.accent_color, particle['alpha'])
            pg.draw.circle(temp_surface, self.accent_color[:3],
                           (int(particle['x'].x), int(particle['x'].y)),
                           int(particle['size']))

        # Afficher le logo avec effet de pulse
        self.render_logo_with_pulse(temp_surface)

        # Barre de progression - ajustée pour être plus bas si on utilise le logo
        bar_y_offset = 150 if (self.logo and not self.fallback_title) else 100
        bar_width = 400
        bar_height = 20
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = SCREEN_HEIGHT // 2 + bar_y_offset

        # Fond de la barre
        pg.draw.rect(temp_surface, self.bar_bg_color,
                     (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        pg.draw.rect(temp_surface, (32, 32, 40),
                     (bar_x, bar_y, bar_width, bar_height))

        # Remplissage de la barre avec effet de brillance
        if self.progress > 0:
            fill_width = int(bar_width * self.progress)
            pg.draw.rect(temp_surface, self.bar_fill_color,
                         (bar_x, bar_y, fill_width, bar_height))

            # Effet de brillance qui se déplace
            shine_pos = (self.animation_time * 100) % (bar_width + 50) - 25
            if 0 <= shine_pos <= fill_width:
                shine_color = (255, 255, 255, 100)
                pg.draw.rect(temp_surface, (255, 255, 255),
                             (bar_x + shine_pos - 15, bar_y, 30, bar_height))

        # Pourcentage
        percentage = int(self.progress * 100)
        percent_text = self.font_medium.render(f"{percentage}%", True, self.text_color)
        percent_x = SCREEN_WIDTH // 2 - percent_text.get_width() // 2
        percent_y = bar_y + bar_height + 20
        temp_surface.blit(percent_text, (percent_x, percent_y))

        # Texte de l'étape actuelle avec points animés
        if self.current_step < len(self.loading_steps):
            step_text = self.loading_steps[self.current_step]
            dots_count = int(self.dots_animation) % 4
            step_text += "." * dots_count

            step_surface = self.font_small.render(step_text, True, self.text_color)
            step_x = SCREEN_WIDTH // 2 - step_surface.get_width() // 2
            step_y = percent_y + 60
            temp_surface.blit(step_surface, (step_x, step_y))

        # Instruction - ajustée pour être au bon endroit
        if not self.is_complete:
            instruction_text = self.font_small.render("Preparing your descent into hell...",
                                                      True, (200, 200, 200))
            instruction_x = SCREEN_WIDTH // 2 - instruction_text.get_width() // 2
            instruction_y = SCREEN_HEIGHT - 60
            temp_surface.blit(instruction_text, (instruction_x, instruction_y))

        # Instructions d'annulation
        cancel_text = self.font_small.render("[ESC] Cancel", True, (150, 150, 150))
        cancel_x = 20
        cancel_y = SCREEN_HEIGHT - 40
        temp_surface.blit(cancel_text, (cancel_x, cancel_y))

        # Appliquer l'alpha et blitter sur l'écran principal
        if alpha < 255:
            temp_surface.set_alpha(alpha)
        screen.blit(temp_surface, (0, 0))
import pygame as pg
import math

class Explosion:
    def __init__(self, x, y, frames, duration=0.3):
        self.x = x
        self.y = y
        self.frames = frames
        self.duration = duration
        self.start_time = pg.time.get_ticks() / 1000
        self.frame_count = len(frames)

    def update(self):
        current_time = pg.time.get_ticks() / 1000
        return (current_time - self.start_time) < self.duration

    def render(self, screen, raycaster, player):
        current_time = pg.time.get_ticks() / 1000
        elapsed = current_time - self.start_time
        index = min(int((elapsed / self.duration) * self.frame_count), self.frame_count - 1)
        sprite = self.frames[index]

        dx = self.x - player.x
        dy = self.y - player.y
        dist = math.hypot(dx, dy)
        rel_angle = math.atan2(dy, dx) - player.angle
        rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi

        if abs(rel_angle) > raycaster.fov / 2:
            return

        corrected_dist = dist * math.cos(rel_angle)
        screen_x = int((0.5 + rel_angle / raycaster.fov) * screen.get_width())

        if 0 <= screen_x < len(raycaster.z_buffer):
            wall_dist = raycaster.z_buffer[screen_x]
            depth_diff = corrected_dist - wall_dist
            print(
                f"[EXPLOSION] screen_x={screen_x}, corrected_dist={corrected_dist:.2f}, wall_dist={wall_dist:.2f}, Δdepth={depth_diff:.2f}")
            if depth_diff > 20:  # autorise une petite marge
                return
        else:
            return

        size = max(100, int(1000 / (corrected_dist + 0.0001)))
        screen_y = screen.get_height() // 2 - size // 2
        scaled_sprite = pg.transform.scale(sprite, (size, size))
        screen.blit(scaled_sprite, (screen_x - size // 2, screen_y))

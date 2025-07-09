import pygame

class SkeletonAnimation:
    def __init__(self, x, y, frames, messages, frame_delay=250, max_bubble_width=250):
        self.x = x
        self.initial_y = y + 100  # start below ground
        self.target_y = y
        self.y = self.initial_y
        self.rise_speed = 1.2
        self.fall_speed = 1.5

        self.frames = frames
        self.frame_delay = frame_delay
        self.frame_index = 0
        self.timer = 0

        self.active = True
        self.fading_out = False

        self.font = pygame.font.SysFont("consolas", 20)
        self.name_font = pygame.font.SysFont("consolas", 18, bold=True)

        self.name = "Whisper Jack"
        
        self.messages = messages.copy()  
        self.farewell_line = "Got candy? No? Then I'm ghostin'..."
        
        self.current_message_index = 0
        self.message_done = False

        self.max_bubble_width = max_bubble_width

    def wrap_text(self, text, font, max_width):
        """Wrap text to fit inside max_width. Returns a list of lines."""
        words = text.split(' ')
        lines = []
        current_line = ''
        for word in words:
            test_line = current_line + (' ' if current_line else '') + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    def update(self, dt):
        if not self.active:
            return

        # Rising animation (fade in)
        if not self.fading_out:
            if self.y > self.target_y:
                self.y -= self.rise_speed
                if self.y < self.target_y:
                    self.y = self.target_y

        # Falling animation (fade out)
        if self.fading_out:
            self.y += self.fall_speed
            screen_height = pygame.display.get_surface().get_height()
            if self.y > screen_height + 100:
                self.active = False

        # Loop idle animation
        self.timer += dt
        if self.timer >= self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.timer = 0

    def handle_event(self, event):
        if self.active and not self.fading_out and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.current_message_index += 1
                if self.current_message_index >= len(self.messages):
                    if not self.message_done:
                        self.message_done = True
                        self.messages.append(self.farewell_line)
                    else:
                        self.fading_out = True

    def draw(self, screen, camera_offset):
        if not self.active:
            return

        # Draw skeleton sprite
        if self.frame_index < len(self.frames):
            screen.blit(self.frames[self.frame_index], (self.x - camera_offset, self.y))

        # Draw speech bubble if there's a message to show
        if self.current_message_index < len(self.messages):
            message = self.messages[self.current_message_index]
            lines = self.wrap_text(message, self.font, self.max_bubble_width)
            name_surface = self.name_font.render(self.name, True, (20, 20, 20))

            padding = 10
            line_height = self.font.get_height()
            bubble_width = max([self.font.size(line)[0] for line in lines] + [name_surface.get_width()]) + padding * 2
            bubble_height = line_height * len(lines) + name_surface.get_height() + padding * 3

            bubble_x = self.x - camera_offset - bubble_width - 20  # bubble to left
            # Clamp bubble_x so it never goes beyond left edge of screen (10 px padding)
            if bubble_x < 10:
                bubble_x = 10
            bubble_y = self.y - bubble_height - 30  # Raise bubble up more

            bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
            pygame.draw.rect(screen, (255, 255, 255), bubble_rect, border_radius=8)
            pygame.draw.rect(screen, (0, 0, 0), bubble_rect, 2, border_radius=8)

            # Draw Whisper Jack's name at top of bubble
            screen.blit(name_surface, (bubble_x + padding, bubble_y + padding))

            # Draw wrapped message lines
            text_y = bubble_y + padding + name_surface.get_height() + 5
            for line in lines:
                line_surface = self.font.render(line, True, (0, 0, 0))
                screen.blit(line_surface, (bubble_x + padding, text_y))
                text_y += line_height

            # Draw [Press Space] hint only if not fading out
            if not self.fading_out:
                hint_surface = self.font.render("[Press Space]", True, (100, 100, 100))
                screen.blit(hint_surface, (bubble_x + padding, bubble_y + bubble_height))

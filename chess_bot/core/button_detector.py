import os
import cv2
import numpy as np
from typing import Optional, Dict, Tuple, List


class ButtonDetector:
    """
    Detector for UI buttons and popups using template matching.
    Supports multi-resolution matching by scaling templates.
    """

    # Button template names (hard-coded)
    BUTTON_TEMPLATES = [
        "game_over_popup",    # Popup hiển thị khi game over
        "end_game_button",    # Nút kết thúc/đóng popup
        "enter_game_button",  # Nút vào trò chơi
        "start_play_button",  # Nút bắt đầu chơi
    ]

    # Scale factors for multi-resolution matching
    SCALE_FACTORS = [0.8, 0.9, 1.0, 1.1, 1.2]

    def __init__(self, templates_path: str):
        self.templates_path = templates_path
        self.templates: Dict[str, np.ndarray] = {}
        self.threshold = 0.7
        self._load_templates()

    def _load_templates(self):
        """Load button templates from templates folder"""
        if not os.path.exists(self.templates_path):
            os.makedirs(self.templates_path, exist_ok=True)
            return

        for filename in os.listdir(self.templates_path):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                name = os.path.splitext(filename)[0]
                # Only load button templates
                if name in self.BUTTON_TEMPLATES:
                    filepath = os.path.join(self.templates_path, filename)
                    template = cv2.imread(filepath)
                    if template is not None:
                        self.templates[name] = template

    def reload_templates(self):
        """Reload templates from disk"""
        self.templates.clear()
        self._load_templates()

    def set_threshold(self, threshold: float):
        """Set detection threshold (0.0 - 1.0)"""
        self.threshold = threshold

    def get_available_templates(self) -> List[str]:
        """Get list of available (loaded) button templates"""
        return list(self.templates.keys())

    def get_missing_templates(self) -> List[str]:
        """Get list of button templates that are not yet captured"""
        return [name for name in self.BUTTON_TEMPLATES if name not in self.templates]

    def detect_buttons(self, screenshot: np.ndarray) -> Dict[str, Tuple[int, int, float]]:
        """
        Detect buttons in screenshot.

        Args:
            screenshot: BGR image from screen capture

        Returns:
            Dict mapping button_name -> (center_x, center_y, confidence)
        """
        if screenshot is None:
            return {}

        detected = {}

        for button_name, template in self.templates.items():
            result = self._find_template_multi_scale(screenshot, template)
            if result is not None:
                detected[button_name] = result

        return detected

    def detect_button(self, screenshot: np.ndarray, button_name: str) -> Optional[Tuple[int, int, float]]:
        """
        Detect a specific button in screenshot.

        Args:
            screenshot: BGR image from screen capture
            button_name: Name of the button template to find

        Returns:
            (center_x, center_y, confidence) or None if not found
        """
        if screenshot is None or button_name not in self.templates:
            return None

        template = self.templates[button_name]
        return self._find_template_multi_scale(screenshot, template)

    def _find_template_multi_scale(self, screenshot: np.ndarray,
                                    template: np.ndarray) -> Optional[Tuple[int, int, float]]:
        """
        Find template in screenshot using multi-scale matching.

        Args:
            screenshot: BGR image
            template: BGR template image

        Returns:
            (center_x, center_y, confidence) or None if not found
        """
        best_match = None
        best_confidence = 0.0
        best_scale = 1.0
        best_location = None

        for scale in self.SCALE_FACTORS:
            # Scale template
            scaled_template = self._scale_template(template, scale)
            if scaled_template is None:
                continue

            # Check if template fits in screenshot
            if (scaled_template.shape[0] > screenshot.shape[0] or
                scaled_template.shape[1] > screenshot.shape[1]):
                continue

            # Template matching
            result = cv2.matchTemplate(screenshot, scaled_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > best_confidence and max_val >= self.threshold:
                best_confidence = max_val
                best_scale = scale
                best_location = max_loc
                best_match = scaled_template

        if best_match is not None and best_location is not None:
            # Calculate center position
            center_x = best_location[0] + best_match.shape[1] // 2
            center_y = best_location[1] + best_match.shape[0] // 2
            return (center_x, center_y, best_confidence)

        return None

    def _scale_template(self, template: np.ndarray, scale: float) -> Optional[np.ndarray]:
        """Scale template by given factor"""
        if scale == 1.0:
            return template

        try:
            new_width = int(template.shape[1] * scale)
            new_height = int(template.shape[0] * scale)

            if new_width < 10 or new_height < 10:
                return None

            scaled = cv2.resize(template, (new_width, new_height),
                               interpolation=cv2.INTER_LINEAR)
            return scaled
        except Exception:
            return None

    def is_game_over_detected(self, screenshot: np.ndarray) -> bool:
        """
        Check if game over popup is detected.

        Args:
            screenshot: BGR image from screen capture

        Returns:
            True if game_over_popup template is found
        """
        if "game_over_popup" not in self.templates:
            return False

        result = self.detect_button(screenshot, "game_over_popup")
        return result is not None

    def get_click_sequence(self, screenshot: np.ndarray) -> List[Tuple[str, int, int]]:
        """
        Get sequence of buttons to click for new game.
        Returns buttons in priority order that are currently visible.

        Args:
            screenshot: BGR image

        Returns:
            List of (button_name, x, y) tuples for buttons that should be clicked
        """
        click_sequence = []

        # Priority order for clicking
        button_priority = [
            "end_game_button",
            "enter_game_button",
            "start_play_button",
        ]

        detected = self.detect_buttons(screenshot)

        for button_name in button_priority:
            if button_name in detected:
                x, y, _ = detected[button_name]
                click_sequence.append((button_name, x, y))

        return click_sequence

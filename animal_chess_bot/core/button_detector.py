import os
import cv2
import numpy as np
from typing import Optional, Dict, Tuple, List


class ButtonDetector:
    """
    Detector for UI buttons and popups using template matching.
    Supports multi-resolution matching by scaling templates.
    Dynamically loads all templates from templates folder.
    """

    SCALE_FACTORS = [0.8, 0.9, 1.0, 1.1, 1.2]

    def __init__(self, templates_path: str):
        self.templates_path = templates_path
        self.templates: Dict[str, np.ndarray] = {}
        self.threshold = 0.7
        self._load_templates()

    def _load_templates(self):
        if not os.path.exists(self.templates_path):
            os.makedirs(self.templates_path, exist_ok=True)
            return

        for filename in os.listdir(self.templates_path):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                name = os.path.splitext(filename)[0]
                filepath = os.path.join(self.templates_path, filename)
                template = cv2.imread(filepath)
                if template is not None:
                    self.templates[name] = template

    def reload_templates(self):
        self.templates.clear()
        self._load_templates()

    def set_threshold(self, threshold: float):
        self.threshold = threshold

    def get_available_templates(self) -> List[str]:
        return list(self.templates.keys())

    def has_template(self, template_name: str) -> bool:
        return template_name in self.templates

    def detect_buttons(self, screenshot: np.ndarray) -> Dict[str, Tuple[int, int, float]]:
        if screenshot is None:
            return {}

        detected = {}

        for button_name, template in self.templates.items():
            result = self._find_template_multi_scale(screenshot, template)
            if result is not None:
                detected[button_name] = result

        return detected

    def detect_button(self, screenshot: np.ndarray, button_name: str) -> Optional[Tuple[int, int, float]]:
        if screenshot is None or button_name not in self.templates:
            return None

        template = self.templates[button_name]
        return self._find_template_multi_scale(screenshot, template)

    def _find_template_multi_scale(self, screenshot: np.ndarray,
                                    template: np.ndarray) -> Optional[Tuple[int, int, float]]:
        best_match = None
        best_confidence = 0.0
        best_scale = 1.0
        best_location = None

        for scale in self.SCALE_FACTORS:
            scaled_template = self._scale_template(template, scale)
            if scaled_template is None:
                continue

            if (scaled_template.shape[0] > screenshot.shape[0] or
                scaled_template.shape[1] > screenshot.shape[1]):
                continue

            result = cv2.matchTemplate(screenshot, scaled_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > best_confidence and max_val >= self.threshold:
                best_confidence = max_val
                best_scale = scale
                best_location = max_loc
                best_match = scaled_template

        if best_match is not None and best_location is not None:
            center_x = best_location[0] + best_match.shape[1] // 2
            center_y = best_location[1] + best_match.shape[0] // 2
            return (center_x, center_y, best_confidence)

        return None

    def _scale_template(self, template: np.ndarray, scale: float) -> Optional[np.ndarray]:
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

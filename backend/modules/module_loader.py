import os
import importlib


# Explicit map: file module name -> class name.
# Auto-derivation breaks on names like youtube_module -> YouTubeModule.
CLASS_MAP = {
    "browser_module": "BrowserModule",
    "chart_module": "ChartModule",
    "chat_module": "ChatModule",
    "coding_module": "CodingModule",
    "computer_module": "ComputerModule",
    "pdf_module": "PdfModule",
    "youtube_module": "YouTubeModule",
}


class ModuleLoader:

    def __init__(self):
        self.modules = {}

    def load_modules(self):

        folder = os.path.dirname(__file__)

        for file in os.listdir(folder):

            if not file.endswith("_module.py"):
                continue

            module_name = file[:-3]

            try:
                module = importlib.import_module(f"modules.{module_name}")
            except Exception as exc:
                print(f"[module_loader] failed to import {module_name}: {exc}")
                continue

            class_name = CLASS_MAP.get(module_name)

            if class_name and hasattr(module, class_name):
                cls = getattr(module, class_name)
                self.modules[module_name] = cls()
            else:
                print(f"[module_loader] class {class_name} not found in {module_name}")

    def get(self, name):
        return self.modules.get(name)

    def all(self):
        return self.modules

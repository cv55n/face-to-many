import os
import shutil
import random
import json
from PIL import Image, ExifTags
from typing import List
from cog import BasePredictor, Input, Path

from helpers.comfyui import ComfyUI

OUTPUT_DIR = "/tmp/outputs"
INPUT_DIR = "/tmp/inputs"
COMFYUI_TEMP_OUTPUT_DIR = "ComfyUI/temp"

with open("face-to-many-api.json", "r") as file:
    workflow_json = file.read()

LORA_WEIGHTS_MAPPING = {
    "3D": "artificialguybr/3DRedmond-3DRenderStyle-3DRenderAF.safetensors",
    "Emoji": "fofr/emoji.safetensors",
    "Video game": "artificialguybr/PS1Redmond-PS1Game-Playstation1Graphics.safetensors",
    "Pixels": "artificialguybr/PixelArtRedmond-Lite64.safetensors",
    "Clay": "artificialguybr/ClayAnimationRedm.safetensors",
    "Toy": "artificialguybr/ToyRedmond-FnkRedmAF.safetensors"
}

LORA_TYPES = list(LORA_WEIGHTS_MAPPING.keys())

class Predictor(BasePredictor):
    def setup(self):
        self.comfyui = ComfyUI("127.0.0.1:8188")
        self.comfyUI.start_server(OUTPUT_DIR, INPUT_DIR)
        self.comfyUI.load_workflow(workflow_json, check_inputs=False)
        self.download_loras()

    def parse_custom_lora_url(self, url: str):
        if "pbxt.replicate" in url:
            parts_after_pbxt = url.split("/pbxt.replicate.delivery/")[1]
        else:
            parts_after_pbxt = url.split("/pbxt/")[1]

        return parts_after_pbxt.split("/trained_model.tar")[0]
    
    def add_to_lora_map(self, lora_url: str):
        uuid = self.parse_custom_lora_url(lora_url)

        self.comfyUI.weights_downloader.download_lora_from_replicate_url(uuid, lora_url)

    def download_loras(self):
        for weight in LORA_WEIGHTS_MAPPING.values():
            self.comfyUI.weights_downloader.download_weights(weight)
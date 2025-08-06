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

    def cleanup(self):
        self.comfyUI.clear_queue()

        for directory in [OUTPUT_DIR, INPUT_DIR, COMFYUI_TEMP_OUTPUT_DIR]:
            if os.path.exists(directory):
                shutil.rmtree(directory)

            os.makedirs(directory)

    def handle_input_file(self, input_file: Path):
        file_extension = os.path.splitext(input_file)[1].lower()

        if file_extension in [".png", ".webp", ".gif"]:
            filename = f"input{file_extension}"

            shutil.copy(input_file, os.path.join(INPUT_DIR, filename))
        else:
            # se o arquivo é um jpg, jpeg ou desconhecido, converter para png
            #
            # converte-se jpgs para remover os dados exif relacionados a imagens hdr
            #
            # alternativamente, caso não haja uma extensão de arquivo, como
            # uma imagem base64, tentar salvar como um png

            filename = "input.png"

            image = Image.open(input_file)

            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break

                exif = dict(image._getexif().items())

                if exif[orientation] == 3:
                    image = image.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    image = image.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    image = image.rotate(90, expand=True)
            except (KeyError, AttributeError):
                # dado exif não possui orientação

                # não rotacionar
                pass

            image.save(os.path.join(INPUT_DIR, filename))

        return filename
    
    def log_and_collect_files(self, directory, prefix=""):
        files = []

        for f in os.listdir(directory):
            if f == "__MACOSX":
                continue

            path = os.path.join(directory, f)

            if os.path.isfile(path):
                print(f"{prefix}{f}")

                files.append(Path(path))
            elif os.path.isdir(path):
                print(f"{prefix}{f}/")

                files.extend(self.log_and_collect_files(path, prefix=f"{prefix}{f}/"))

        return files
    
    def update_workflow(self, workflow, **kwargs):
        style = kwargs["style"]
        prompt = kwargs["prompt"]
        negative_prompt = kwargs["negative_prompt"]
        custom_style = kwargs["lora_url"]

        if custom_style:
            uuid = self.parse_custom_lora_url(custom_style)

            lora_name = f"{uuid}/{uuid}.safetensors"
        else:
            lora_name = LORA_WEIGHTS_MAPPING[style]

            prompt = self.style_to_prompt(style, prompt)
            negative_prompt = self.style_to_negative_prompt(style, negative_prompt)

        load_image = workflow["22"]["inputs"]
        load_image["image"] = kwargs["filename"]

        loader = workflow["2"]["inputs"]
        loader["positive"] = prompt
        loader["negative"] = negative_prompt

        controlnet = workflow["28"]["inputs"]
        controlnet["strength"] = kwargs["control_depth_strength"]

        lora_loader = workflow["3"]["inputs"]
        lora_loader["lora_name_1"] = lora_name
        lora_loader["lora_wt_1"] = kwargs["lora_scale"]

        instant_id = workflow["41"]["inputs"]
        instant_id["weight"] = kwargs["instant_id_strength"]

        sampler = workflow["4"]["inputs"]
        sampler["denoise"] = kwargs["denoising_strength"]
        sampler["seed"] = kwargs["seed"]
        sampler["cfg"] = kwargs["prompt_strength"]

    def style_to_prompt(self, style, prompt):
        style_prompts = {
            "3D": f"3D Render Style, 3DRenderAF, {prompt}",
            "Emoji": f"memoji, emoji, {prompt}, 3d render, sharp",
            "Video game": f"Playstation 1 Graphics, PS1 Game, {prompt}, Video game screenshot",
            "Pixels": f"Pixel Art, PixArFK, {prompt}",
            "Clay": f"Clay Animation, Clay, {prompt}",
            "Toy": f"FnkRedmAF, {prompt}, toy, miniature"
        }

        return style_prompts[style]
    
    def style_to_negative_prompt(self, style, negative_prompt=""):
        if negative_prompt:
            negative_prompt = f"{negative_prompt}, "

        start_base_negative = "nsfw, nude, oversaturated, "
        end_base_negative = "ugly, broken, watermark"

        specifics = {
            "3D": "photo, photography, ",
            "Emoji": "photo, photography, blurry, soft, ",
            "Video game": "text, photo, ",
            "Pixels": "photo, photography, ",
            "Clay": "",
            "Toy": ""
        }

        return f"{specifics[style]}{start_base_negative}{negative_prompt}{end_base_negative}"
    
    def predict(
        self,

        image: Path = Input(
            description="uma imagem de uma pessoa para ser convertida",
            default=None
        ),

        style: str = Input(
            default="3D",
            choices=LORA_TYPES,
            description="estilos para converter"
        ),

        prompt: str = Input(
            default="uma pessoa"
        ),

        negative_prompt: str = Input(
            default="",
            description="coisas que você não quer na imagem"
        ),

        denoising_strength: float = Input(
            default=0.65,
            ge=0,
            le=1,
            description="quanta parte da imagem original deve ser mantida. 1 é a destruição completa da imagem original, 0 é a imagem original"
        ),

        prompt_strength: float = Input(
            default=4.5,
            ge=0,
            le=20,
            description="força do prompt. esta é a escala cfg: números mais altos levam a um prompt mais forte, números mais baixos mantêm uma semelhança maior com o original."
        ),

        control_depth_strength: float = Input(
            default=0.8,
            ge=0,
            le=1,
            description="intensidade do controlnet de profundidade. quanto maior, mais o controlnet afeta a saída."
        ),

        instant_id_strength: float = Input(
            default=1,
            description="quão forte será o instantid.", ge=0, le=1
        ),

        seed: int = Input(
            default=None,
            description="corrige a seed aleatória para reprodutibilidade"
        ),

        custom_lora_url: str = Input(
            default=None,
            description="url para um lora personalizado replicado. deve estar no formato https://replicate.delivery/pbxt/[id]/trained_model.tar ou https://pbxt.replicate.delivery/[id]/trained_model.tar"
        ),

        lora_scale: float = Input(
            default=1,
            description="quão forte será a lora", ge=0, le=1
        )
    ) -> List[Path]:
        """executa uma única previsão no modelo"""

        self.cleanup()

        if image is None:
            raise ValueError("nenhuma imagem fornecida")
        
        filename = self.handle_input_file(image)

        if custom_lora_url is not None:
            if not (
                "https://replicate.delivery/pbxt/" in custom_lora_url
                or "https://pbxt.replicate.delivery/" in custom_lora_url
            ) or not custom_lora_url.endswith("/trained_model.tar"):
                raise ValueError(
                    "o formato do url personalizado do lora não é suportado. deve estar no formato https://replicate.delivery/pbxt/[id]/trained_model.tar ou https://pbxt.replicate.delivery/[id]/trained_model.tar"
                )
            
            self.add_to_lora_map(custom_lora_url)

        if seed is None:
            seed = random.randint(0, 2**32 - 1)

            print(f"seed aleatória setada em: {seed}")

        workflow = json.loads(workflow_json)

        self.update_workflow(
            workflow,
            filename=filename,
            style=style,
            denoising_strength=denoising_strength,
            seed=seed,
            prompt=prompt,
            negative_prompt=negative_prompt,
            prompt_strength=prompt_strength,
            instant_id_strength=instant_id_strength,
            lora_url=custom_lora_url,
            lora_scale=lora_scale,
            control_depth_strength=control_depth_strength
        )

        wf = self.comfyUI.load_workflow(workflow, check_weights=False)

        self.comfyUI.connect()
        self.comfyUI.run_workflow(wf)

        files = []

        output_directories = [OUTPUT_DIR]

        for directory in output_directories:
            print(f"conteúdos de {directory}:")

            files.extend(self.log_and_collect_files(directory))

        return files
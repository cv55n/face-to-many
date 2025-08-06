import subprocess
import time
import os

from weights_manifest import WeightsManifest

BASE_URL = "https://weights.replicate.delivery/default/comfy-ui"
BASE_PATH = "ComfyUI/models"

class WeightsDownloader:
    def __init__(self):
        self.weights_manifest = WeightsManifest()
        self.weights_map = self.weights_manifest.weights_map

    def download_weights(self, weight_str):
        if weight_str in self.weights_map:
            if self.weights_manifest.is_non_commercial_only(weight_str):
                print(
                    f"⚠️ {weight_str} é apenas para uso não comercial. a menos que você tenha obtido uma licença comercial.\ndetalhes: https://github.com/fofr/cog-comfyui/blob/main/weights_licenses.md"
                )

            self.download_if_not_exists(
                weight_str,

                self.weights_map[weight_str]["url"],
                self.weights_map[weight_str]["dest"]
            )
        else:
            raise ValueError(
                f"{weight_str} indisponível. veja a lista de pesos disponíveis: https://github.com/fofr/cog-comfyui/blob/main/supported_weights.md"
            )

    def download_lora_from_replicate_url(self, uuid, url):
        dest = f"{BASE_PATH}/loras"

        self.download_custom_lora(uuid, url, dest)

    def download_torch_checkpoints(self):
        self.download_if_not_exists(
            "mobilenet_v2-b0353104.pth",
            f"{BASE_URL}/custom_nodes/comfyui_controlnet_aux/mobilenet_v2-b0353104.pth.tar",
            "/root/.cache/torch/hub/checkpoints/"
        )

    def download_if_not_exists(self, weight_str, url, dest):
        if not os.path.exists(f"{dest}/{weight_str}"):
            self.download(weight_str, url, dest)

    def download(self, weight_str, url, dest):
        if "/" in weight_str:
            subfolder = weight_str.rsplit("/", 1)[0]
            dest = os.path.join(dest, subfolder)
            os.makedirs(dest, exist_ok=True)

        print(f"⏳ baixando {weight_str} em {dest}")

        start = time.time()

        subprocess.check_call(
            ["pget", "--log-level", "warn", "-xf", url, dest], close_fds=False
        )

        elapsed_time = time.time() - start
        downloaded_file_path = os.path.join(dest, os.path.basename(weight_str))

        try:
            file_size_bytes = os.path.getsize(downloaded_file_path)
            file_size_megabytes = file_size_bytes / (1024 * 1024)

            print(
                f"⌛️ completado em {elapsed_time:.2f}s, tamanho: {file_size_megabytes:.2f}mb"
            )
        except FileNotFoundError:
            print(f"⌛️ completado em {elapsed_time:.2f}s porém o arquivo não foi encontrado.")

    def download_custom_lora(self, uuid, url, dest):
        if not os.path.exists(f"{dest}/{uuid}"):
            dest_with_uuid = os.path.join(dest, uuid)

            os.makedirs(dest_with_uuid, exist_ok=True)

            print(f"⏳ baixando {uuid} em {dest_with_uuid}")

            start = time.time()

            subprocess.check_call(
                ["pget", "--log-level", "warn", "-xf", url, dest_with_uuid], close_fds=False
            )

            elapsed_time = time.time() - start

            self.handle_replicate_tar(uuid, dest_with_uuid)

            preserved_file_path = os.path.join(dest_with_uuid, f"{uuid}.safetensors")

            try:
                file_size_bytes = os.path.getsize(preserved_file_path)
                file_size_megabytes = file_size_bytes / (1024 * 1024)

                print(
                    f"⌛️ completado em {elapsed_time:.2f}s, tamanho: {file_size_megabytes:.2f}mb"
                )
            except FileNotFoundError:
                print(f"⌛️ completado em {elapsed_time:.2f}s porém o arquivo não foi encontrado.")
        else:
            print(f"✅ pasta lora {uuid} já existe.")

    def handle_replicate_tar(self, uuid, dest_with_uuid):
        extracted_lora_path = os.path.join(dest_with_uuid, "lora.safetensors")
        new_file_path = os.path.join(dest_with_uuid, f"{uuid}.safetensors")

        if os.path.exists(extracted_lora_path):
            os.rename(extracted_lora_path, new_file_path)

            print(
                f"✅ {uuid}.safetensors foi extraído e salvo em {new_file_path}"
            )
        else:
            raise FileNotFoundError(f"lora.safetensors não encontrado em {dest_with_uuid}.")

        # deleta os outros arquivos (embeddings.pti e special_params.json) caso eles existam
        for file_name in ["embeddings.pti", "special_params.json"]:
            file_path = os.path.join(dest_with_uuid, file_name)

            if os.path.exists(file_path):
                os.remove(file_path)

                print(f"🗑️ removendo {file_path}")
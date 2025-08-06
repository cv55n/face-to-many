import os

class ComfyUI_IPAdapter_plus:
    @staticmethod
    def prepare():
        # cria a pasta ipadapter em comfyui/models/ipadapter
        #
        # se não existir no momento da configuração, o plugin será transferido para o diretório base e não procurará nossos ipadapters que são baixados sob demanda
        if not os.path.exists("ComfyUI/models/ipadapter"):
            os.makedirs("ComfyUI/models/ipadapter")

    @staticmethod
    def add_weights(weights_to_download, node):
        if "class_type" in node and node["class_type"] in [
            "InsightFaceLoader",
        ]:
            weights_to_download.append("buffalo_l")
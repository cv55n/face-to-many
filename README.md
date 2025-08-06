# face-to-many

turn any face into 3d, pixel art, video game, claymation or toy.

run this model on replicate:

https://replicate.com/fofr/face-to-many

or run it in comfyui:

https://github.com/fofr/cog-face-to-many/blob/main/face-to-many-ui.json

you'll need these custom nodes:

- [comfyui controlnet aux](https://github.com/Fannovel16/comfyui_controlnet_aux/tree/6d6f63c)
- [comfyui instantid](https://github.com/cubiq/ComfyUI_InstantID/tree/0fcf494)
- [comfyui ipadapter plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus/tree/4e898fe)
- [comfyui essentials](https://github.com/cubiq/ComfyUI_essentials/tree/c9236fe)
- [efficiency nodes comfyui](https://github.com/jags111/efficiency-nodes-comfyui/tree/1ac5f18)

## loras

the 3d, video game, pixel art, claymation and toy loras are all made by artificialguybr. if you like them you can make a donation to their patreon or ko-fi:

- https://www.patreon.com/user?u=81570187
- https://ko-fi.com/artificialguybr

or follow him on twitter:

https://twitter.com/artificialguybr

## developing locally

clone this repository:

```
git clone --recurse-submodules https://github.com/cv55n/face-to-many.git && cd face-to-many/ComfyUI
```

create python venv and activate

```
python3 -m venv . && source bin/activate
```

install the required dependencies

```
pip install -r requirements.txt
```

download `albedobaseXL_v13.safetensors` to `models/checkpoints`

```
wget https://huggingface.co/frankjoshua/albedobaseXL_v13/resolve/main/albedobaseXL_v13.safetensors?download=true -O models/checkpoints/albedobaseXL_v13.safetensors
```

download `antelopev2``

```
git clone https://huggingface.co/DIAMONIK7777/antelopev2 models/insightface/models/antelopev2
```

download `instantid-ip-adapter.bin`

```
wget https://huggingface.co/Aitrepreneur/InstantID-Controlnet/resolve/main/checkpoints/ip-adapter.bin?download=true -O models/instantid/instantid-ip-adapter.bin
```

download `instantid-controlnet.safetensors`

```
wget https://huggingface.co/Aitrepreneur/InstantID-Controlnet/resolve/main/checkpoints/ControlNetModel/diffusion_pytorch_model.safetensors?download=true -O models/controlnet/instantid-controlnet.safetensors
```

run the [following script](https://github.com/fofr/cog-face-to-many/blob/main/scripts/clone_plugins.sh) to install all the custom nodes:

```
./scripts/clone_plugins.sh
```

finally, install it, run it and enjoy it

```
python3 main.py
```

### running the web ui from your cog container

1. **gpu machine**: start the cog container and expose port 8188:

```
sudo cog run -p 8188 bash
```

2. **inside cog container**: now that we have access to the cog container, we start the server, binding to all network interfaces:

```
cd ComfyUI/
python main.py --listen 0.0.0.0
```

3. **local machine**: access the server using the gpu machine's ip and the exposed port (8188): `http://<gpu-machines-ip>:8188`

when you goto `http://<gpu-machines-ip>:8188` you'll see the classic comfyui web form.

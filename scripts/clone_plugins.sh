#!/bin/bash

# esse script é utilizado pra clonar versões específicas de repositórios
#
# ele pega uma lista de repositórios e seus hashes de commit, os clona em um diretório
# específico e então faz check-out no commit especificado

# lista de repositórios e seus hashes de commit para clonar
#
# cada entrada na matriz é uma string contendo a url do repositório e a hash de
# confirmação separados por um espaço
repos=(
    "https://github.com/cubiq/ComfyUI_IPAdapter_plus 4e898fe"
    "https://github.com/Fannovel16/comfyui_controlnet_aux 6d6f63c"
    "https://github.com/jags111/efficiency-nodes-comfyui 60f8700"
    "https://github.com/ssitu/ComfyUI_UltimateSDUpscale bcefc5b"
    "https://github.com/cubiq/ComfyUI_InstantID 0fcf494"
    "https://github.com/ZHO-ZHO-ZHO/ComfyUI-BRIA_AI-RMBG 44a3f8f"
    "https://github.com/cubiq/ComfyUI_essentials c9236fe"
)

# diretório de destinação
#
# isso é onde os repositórios serão clonados
dest_dir="ComfyUI/custom_nodes/"

# faz um loop em cada repositório da lista
for repo in "${repos[@]}"; do
    # extrai a url do repositório e o hash do commit da string
    repo_url=$(echo $repo | cut -d' ' -f1)
    commit_hash=$(echo $repo | cut -d' ' -f2)

    # extrai o nome do repositório a partir da sua url removendo a extensão .git
    repo_name=$(basename "$repo_url" .git)

    # checa se o diretório do repositório já existe
    if [ ! -d "$dest_dir$repo_name" ]; then
        # clona o repositório no diretório de destinação
        echo "clonando $repo_url em $dest_dir$repo_name e checando para realizar o commit $commit_hash"

        git clone --recursive "$repo_url" "$dest_dir$repo_name"

        # utiliza um subshell para evitar de que o shell principal funcione no diretório
        #
        # dentro do subshell, altera o diretório do repositório e checa pelo commit especificado
        (
            cd "$dest_dir$repo_name" && git checkout "$commit_hash"

            rm -rf .git

            # recursivamente remove os diretórios .git dos sub-módulos
            find . -type d -name ".git" -exec rm -rf {} +

            # se o repositório é o efficiency-nodes-comfyui, remover também o diretório de imagens
            if [ "$repo_name" = "efficiency-nodes-comfyui" ]; then
                echo "removendo os diretórios de imagens e workflows de $repo_name"

                rm -rf images workflows
            fi
        )
    else
        echo "pulando clonagem de $repo_name, esse diretório já existe"
    fi
done
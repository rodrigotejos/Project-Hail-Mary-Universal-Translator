"""
Cloud training module using Modal.
"""
import os
import modal
import torch
from torch import nn
from torch import optim
import torch.nn.functional as F

from config import CLOUD_GPU_MOBILENET, CLOUD_GPU_AST, CLOUD_TIMEOUT

# 1. Configuração do ambiente remoto do Modal
app = modal.App("phm-universal-translator")

# Dynamically resolve local 'src' directory to mount it in the container
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Use official PyTorch image to avoid downloading large PyTorch binaries from scratch,
# saving build time and avoiding network timeouts.
docker_image = modal.Image.from_registry(
    "pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime"
).pip_install(
    "torchaudio",
    "torchvision",
    "librosa",
    "scipy",
    "transformers==4.41.2"
).env(
    {"PYTHONPATH": "/root/src"}
).add_local_dir(
    src_dir,
    remote_path="/root/src"
)

# 2. Definição da Função na Nuvem (Executada no Modal)
# A GPU e o timeout são configurados e injetados dinamicamente via .with_options() no orquestrador.
@app.function(image=docker_image)
def train_siamese_on_modal(in_memory_data, epochs=10, batch_size=8, anchor_lang='ingles', model_backbone="mobilenet"):
    """
    Função executada remotamente em uma GPU no Modal.
    Recebe os tensores de áudio em memória, treina a rede siamesa e retorna o state_dict.
    """
    # pylint: disable=too-many-locals, import-outside-toplevel
    import sys
    sys.path.insert(0, "/root/src")

    from torch.utils.data import DataLoader
    from engine.siamese_net import (
        UniversalTranslatorSiameseNet,
        AcousticTransformPipeline,
        InterspeciesTripletDataset
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[NUVEM] Iniciando treinamento no Modal. Acelerador ativo: {device}")
    print(f"[NUVEM] Backbone selecionado: {model_backbone}")

    transform_pipeline = AcousticTransformPipeline(model_backbone=model_backbone).to(device)
    transform_pipeline.eval()

    # Pré-computa características acústicas na nuvem para otimização de performance (evita CPU feature extraction por época)
    print("[NUVEM] Pré-computando características acústicas...")
    precomputed_data = {}
    with torch.no_grad():
        for word, langs in in_memory_data.items():
            precomputed_data[word] = {}
            for lang, waveforms in langs.items():
                precomputed_data[word][lang] = []
                for wave in waveforms:
                    feature = transform_pipeline(wave.to(device))
                    precomputed_data[word][lang].append(feature.squeeze(0).cpu())

    # Inicializa dataset passando os tensores pré-computados
    interspecies_dataset = InterspeciesTripletDataset(
        data_dict=precomputed_data,
        anchor_lang=anchor_lang,
        virtual_size=500
    )

    triplet_loader = DataLoader(
        interspecies_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )

    siamese_translator = UniversalTranslatorSiameseNet(
        embedding_dim=1024,
        model_backbone=model_backbone
    ).to(device)

    def cosine_distance_fn(x, y):
        return 1.0 - F.cosine_similarity(x, y) # pylint: disable=not-callable

    loss_function = nn.TripletMarginWithDistanceLoss(
        distance_function=cosine_distance_fn,
        margin=0.3,
        reduction='mean'
    )

    trainable_params = [p for p in siamese_translator.parameters() if p.requires_grad]
    optimizer = optim.AdamW(trainable_params, lr=2e-4, weight_decay=1e-3)

    siamese_translator.train()
    for epoch in range(epochs):
        cumulative_epoch_loss = 0.0
        for anchor_features, positive_features, negative_features in triplet_loader:
            optimizer.zero_grad()
            v_anchor, v_positive, v_negative = siamese_translator(
                anchor_features.to(device),
                positive_features.to(device),
                negative_features.to(device)
            )
            loss = loss_function(v_anchor, v_positive, v_negative)
            loss.backward()
            optimizer.step()

            cumulative_epoch_loss += loss.item()

        mean_loss = cumulative_epoch_loss / len(triplet_loader)
        print(f"[NUVEM] Época {epoch+1}/{epochs} | Loss: {mean_loss:.4f}")

    # Retorna o modelo treinado de volta para a máquina local do usuário
    return siamese_translator.state_dict()


# 3. Função Orquestradora Local
def run_cloud_training(data_dict, epochs=10, batch_size=8, anchor_lang='ingles', model_backbone="mobilenet", is_entrypoint=False):
    """
    Função executada localmente. Carrega os arquivos físicos de áudio da pasta local,
    converte em tensores de memória e envia para o Modal via chamada de API.
    """
    # pylint: disable=too-many-locals, import-outside-toplevel
    import librosa
    print("\n=== INICIANDO CONEXÃO E ENVIO PARA O MODAL ===")
    print(f"[LOCAL] Backbone solicitado para o Modal: {model_backbone}")
    print("[LOCAL] Carregando arquivos físicos em memória...")

    # Converte os caminhos locais em tensores de áudio antes de enviar
    in_memory_data = {}
    for word, langs in data_dict.items():
        in_memory_data[word] = {}
        for lang, filepaths in langs.items():
            in_memory_data[word][lang] = []
            for path in filepaths:
                # Carrega o áudio localmente em 16kHz
                waveform_np, _ = librosa.load(path, sr=16000, mono=True)
                waveform_tensor = torch.tensor(
                    waveform_np, dtype=torch.float32
                ).unsqueeze(0)
                in_memory_data[word][lang].append(waveform_tensor)

    gpu_type = CLOUD_GPU_AST if model_backbone == "ast" else CLOUD_GPU_MOBILENET
    timeout = CLOUD_TIMEOUT
    
    print(f"[LOCAL] Estabelecendo conexão com o Modal (GPU: {gpu_type}, Timeout: {timeout}s)...")

    # Executa a função na nuvem com configurações dinâmicas e espera pelo retorno do state_dict
    if is_entrypoint:
        state_dict = train_siamese_on_modal.with_options(
            gpu=gpu_type,
            timeout=timeout
        ).remote(
            in_memory_data=in_memory_data,
            epochs=epochs,
            batch_size=batch_size,
            anchor_lang=anchor_lang,
            model_backbone=model_backbone
        )
    else:
        with app.run():
            state_dict = train_siamese_on_modal.with_options(
                gpu=gpu_type,
                timeout=timeout
            ).remote(
                in_memory_data=in_memory_data,
                epochs=epochs,
                batch_size=batch_size,
                anchor_lang=anchor_lang,
                model_backbone=model_backbone
            )

    # Salva o arquivo de pesos recebido da nuvem localmente
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models'))
    os.makedirs(models_dir, exist_ok=True)
    
    model_filename = f'siamese_universal_translator_1024d_{model_backbone}.pth'
    model_path = os.path.join(models_dir, model_filename)

    torch.save(state_dict, model_path)
    print(f"\n[LOCAL] Modelo recebido da nuvem e salvo em: {model_path}")
    print("[LOCAL] Treinamento Remoto Concluído com Sucesso!")


@app.local_entrypoint()
def main():
    import sys
    # Garante que a pasta src está no path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from engine.siamese_net import build_dataset_dictionary
    from config import ACOUSTIC_MODEL_BACKBONE
    
    data_dict = build_dataset_dictionary()
    run_cloud_training(
        data_dict=data_dict,
        epochs=10,
        batch_size=8,
        anchor_lang='ingles',
        model_backbone=ACOUSTIC_MODEL_BACKBONE,
        is_entrypoint=True
    )

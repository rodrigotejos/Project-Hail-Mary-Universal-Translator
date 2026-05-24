import os
import modal
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader

# 1. Configuração do ambiente remoto do Modal
app = modal.App("phm-universal-translator")

# Imagem Docker com dependências otimizadas para GPU T4
docker_image = modal.Image.debian_slim().pip_install(
    "torch==2.5.1", 
    "torchvision==0.20.1", 
    "torchaudio==2.5.1", 
    "librosa", 
    "numpy", 
    "scipy"
)

# 2. Definição da Função na Nuvem (Executada no Modal)
@app.function(image=docker_image, gpu="T4", timeout=600)
def train_siamese_on_modal(in_memory_data, epochs=10, batch_size=8, anchor_lang='ingles'):
    """
    Função executada remotamente em uma GPU T4 no Modal.
    Recebe os tensores de áudio em memória, treina a rede siamesa e retorna o state_dict.
    """
    from engine.siamese_net import (
        UniversalTranslatorSiameseNet,
        MelSpectrogramPipeline,
        InterspeciesTripletDataset
    )
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[NUVEM] Iniciando treinamento no Modal. Acelerador ativo: {device}")

    # Inicializa dataset passando os tensores em memória enviados pelo cliente
    interspecies_dataset = InterspeciesTripletDataset(
        data_dict=in_memory_data,
        anchor_lang=anchor_lang,
        virtual_size=500
    )

    transform_pipeline = MelSpectrogramPipeline().to(device)
    triplet_loader = DataLoader(
        interspecies_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )
    
    siamese_translator = UniversalTranslatorSiameseNet(embedding_dim=1024).to(device)
    
    cosine_distance_fn = lambda x, y: 1.0 - F.cosine_similarity(x, y)
    loss_function = nn.TripletMarginWithDistanceLoss(
        distance_function=cosine_distance_fn,
        margin=0.3,
        reduction='mean'
    )
    
    optimizer = optim.AdamW(siamese_translator.parameters(), lr=2e-4, weight_decay=1e-3)
    
    siamese_translator.train()
    for epoch in range(epochs):
        cumulative_epoch_loss = 0.0
        for anchor_audio, positive_audio, negative_audio in triplet_loader:
            anchor_mel = transform_pipeline(anchor_audio.to(device))
            positive_mel = transform_pipeline(positive_audio.to(device))
            negative_mel = transform_pipeline(negative_audio.to(device))
            
            optimizer.zero_grad()
            v_anchor, v_positive, v_negative = siamese_translator(anchor_mel, positive_mel, negative_mel)
            loss = loss_function(v_anchor, v_positive, v_negative)
            loss.backward()
            optimizer.step()
            
            cumulative_epoch_loss += loss.item()
            
        mean_loss = cumulative_epoch_loss / len(triplet_loader)
        print(f"[NUVEM] Época {epoch+1}/{epochs} | Loss: {mean_loss:.4f}")

    # Retorna o modelo treinado de volta para a máquina local do usuário
    return siamese_translator.state_dict()


# 3. Função Orquestradora Local
def run_cloud_training(data_dict, epochs=10, batch_size=8, anchor_lang='ingles'):
    """
    Função executada localmente. Carrega os arquivos físicos de áudio da pasta local,
    converte em tensores de memória e envia para o Modal via chamada de API.
    """
    import librosa
    print("\n=== INICIANDO CONEXÃO E ENVIO PARA O MODAL (NUVEM COM GPU T4) ===")
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
                waveform_tensor = torch.tensor(waveform_np, dtype=torch.float32).unsqueeze(0)
                in_memory_data[word][lang].append(waveform_tensor)

    print("[LOCAL] Estabelecendo conexão com o Modal e enviando tensores...")
    
    # Executa a função na nuvem e espera pelo retorno do state_dict
    with app.run():
        state_dict = train_siamese_on_modal.remote(
            in_memory_data=in_memory_data,
            epochs=epochs,
            batch_size=batch_size,
            anchor_lang=anchor_lang
        )

    # Salva o arquivo de pesos recebido da nuvem localmente
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models'))
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'siamese_universal_translator_1024d.pth')
    
    torch.save(state_dict, model_path)
    print(f"\n[LOCAL] Modelo recebido da nuvem e salvo em: {model_path}")
    print("[LOCAL] Treinamento Remoto Concluído com Sucesso!")

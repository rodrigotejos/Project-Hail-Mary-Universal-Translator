import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from engine.siamese_net import (
    UniversalTranslatorSiameseNet,
    MelSpectrogramPipeline,
    InterspeciesTripletDataset,
    build_dataset_dictionary
)
from config import TRAINING_MODE

def train_universal_translator_model(epochs=10, batch_size=8, anchor_lang='ingles'):
    # 1. Carrega Dicionário de Áudios
    data_dict = build_dataset_dictionary()
    
    if TRAINING_MODE == "cloud":
        from engine.cloud_train import run_cloud_training
        run_cloud_training(
            data_dict=data_dict,
            epochs=epochs,
            batch_size=batch_size,
            anchor_lang=anchor_lang
        )
        return
        
    print("=== INICIANDO TREINAMENTO LOCAL DA REDE SIAMESA (FEW-SHOT LEARNING) ===")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Alocação Computacional: {device}")
    
    try:
        interspecies_dataset = InterspeciesTripletDataset(
            data_dict=data_dict,
            anchor_lang=anchor_lang,
            virtual_size=500 # Simula 500 épocas/tripletos para poucas amostras
        )
    except ValueError as e:
        print(f"[ERRO] {e}")
        print("Dica: Grave pelo menos duas palavras em ambos os idiomas antes de treinar.")
        return

    # 2. Prepara Pipeline e Dataloader
    transform_pipeline = MelSpectrogramPipeline().to(device)
    triplet_loader = DataLoader(
        interspecies_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )
    
    # 3. Inicializa Rede Siamesa
    siamese_translator = UniversalTranslatorSiameseNet(embedding_dim=1024).to(device)
    
    # 4. Estruturação da Triplet Loss com Distância Cosseno
    cosine_distance_fn = lambda x, y: 1.0 - F.cosine_similarity(x, y)
    loss_function = nn.TripletMarginWithDistanceLoss(
        distance_function=cosine_distance_fn,
        margin=0.3,
        reduction='mean'
    )
    
    # 5. Otimizador AdamW
    optimizer = optim.AdamW(siamese_translator.parameters(), lr=2e-4, weight_decay=1e-3)
    
    # 6. Loop de Treinamento
    print(f"[INFO] Classes encontradas para treino: {interspecies_dataset.classes}")
    print(f"[INFO] Idiomas alvos detectados: {interspecies_dataset.target_langs}")
    print("[INFO] Comissionamento de Epochs Iniciado...\n")
    
    siamese_translator.train()
    
    for epoch in range(epochs):
        cumulative_epoch_loss = 0.0
        
        for batch_index, (anchor_audio, positive_audio, negative_audio) in enumerate(triplet_loader):
            # Passa pelo transformador de Mel
            anchor_mel = transform_pipeline(anchor_audio.to(device))
            positive_mel = transform_pipeline(positive_audio.to(device))
            negative_mel = transform_pipeline(negative_audio.to(device))
            
            optimizer.zero_grad()
            
            # Forward Pass Siames
            v_anchor, v_positive, v_negative = siamese_translator(anchor_mel, positive_mel, negative_mel)
            
            # Loss via Cosine Distance
            loss = loss_function(v_anchor, v_positive, v_negative)
            
            # Backpropagation
            loss.backward()
            optimizer.step()
            
            cumulative_epoch_loss += loss.item()
            
        mean_loss = cumulative_epoch_loss / len(triplet_loader)
        print(f"=== Balanço da Época {epoch+1}/{epochs} | Perda Contínua Estabilizada: {mean_loss:.4f} ===")
        
    # 7. Salva o Cérebro Neural
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'siamese_universal_translator_1024d.pth')
    torch.save(siamese_translator.state_dict(), model_path)
    
    print(f"\n[INFO] Estruturação Siamesa do Tradutor Interespécies Exaurida com Sucesso Absoluto.")
    print(f"[INFO] Modelo salvo em: {model_path}")

if __name__ == '__main__':
    # Idiomas padrão (como o usuário só tem inglês, treinamos as intra-variações usando Data Augmentation)
    train_universal_translator_model(anchor_lang='ingles')

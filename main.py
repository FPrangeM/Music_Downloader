import yt_dlp
import os
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import re 

def sanitizar_nome_arquivo(nome):
    """
    Sanitiza um nome para ser usado como nome de arquivo ou pasta,
    removendo caracteres especiais e limitando o tamanho.
    """
    # Remove caracteres inválidos para nomes de arquivo em Windows/Linux
    nome_sanitizado = re.sub(r'[\\/:*?"<>|]', ' ', nome)
    # Remove múltiplos espaços e espaços no início/fim
    nome_sanitizado = re.sub(r'\s+', ' ', nome_sanitizado).strip()
    # Limita o comprimento do nome para evitar problemas de caminho muito longo
    return nome_sanitizado[:100]

def baixar_musica(artista, musica, pasta_destino='musicas'):
    """
    Baixa uma música em formato MP3 dado o artista e o nome da música.
    
    Args:
        artista (str): Nome do artista
        musica (str): Nome da música
        pasta_destino (str): Pasta onde o arquivo será salvo (padrão: 'musicas')
    
    Returns:
        bool: True se o download foi bem-sucedido, False caso contrário
    """
    # Criar pasta de destino se não existir
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    
    # Sanitizar o nome do artista antes de criar a pasta
    artista_sanitizado = sanitizar_nome_arquivo(artista)
    
    # Criar o caminho da pasta específica para o artista
    pasta_artista = os.path.join(pasta_destino, artista_sanitizado)
    if not os.path.exists(pasta_artista):
        os.makedirs(pasta_artista)
    
    # Sanitizar o nome da música para o nome do arquivo
    musica_sanitizada = sanitizar_nome_arquivo(musica)

    # Configurar as opções do yt-dlp
    query = f"{artista} {musica} official audio"
    options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192', # Alterado para 192kbps para melhor qualidade, mas você pode mudar para 96 se preferir
        }],
        # Salvar o arquivo dentro da pasta do artista sanitizada
        'outtmpl': os.path.join(pasta_artista, f'{artista_sanitizado} - {musica_sanitizada}.%(ext)s'),
        'quiet': True, 
        'no_warnings': True, 
        'ignoreerrors': True, 
    }
    
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([f'ytsearch:{query}'])
        print(f"✓ Música baixada: {artista} - {musica}")
        return True
    except Exception as e:
        print(f"✗ Erro ao baixar: {artista} - {musica} ({str(e)})")
        return False

def processar_lista_musicas(arquivo_input='input.txt', arquivo_output='output.txt', max_workers=5):
    """
    Processa uma lista de músicas de um arquivo e baixa várias em paralelo.
    
    Args:
        arquivo_input (str): Nome do arquivo de entrada com a lista de músicas
        arquivo_output (str): Nome do arquivo de saída com as músicas não baixadas
        max_workers (int): Número máximo de downloads simultâneos (padrão: 5)
    """
    if not os.path.exists(arquivo_input):
        print(f"Arquivo de entrada '{arquivo_input}' não encontrado!")
        return
    
    musicas_a_processar = []
    musicas_nao_baixadas = []
    
    with open(arquivo_input, 'r', encoding='utf-8') as file:
        for linha in file:
            linha = linha.strip()
            if ' - ' not in linha:
                print(f"Formato inválido: '{linha}' (esperado: 'artista - música')")
                musicas_nao_baixadas.append(linha)
                continue
            musicas_a_processar.append(linha)
    
    total_musicas = len(musicas_a_processar)
    print(f"\n=== Iniciando download de {total_musicas} músicas (em até {max_workers} processos paralelos) ===")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_music = {executor.submit(baixar_musica, *linha.split(' - ', 1)): linha for linha in musicas_a_processar}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_music), 1):
            musica_info = future_to_music[future]
            artista, musica = musica_info.split(' - ', 1)
            print(f"[{i}/{total_musicas}] Processando: {artista} - {musica}")
            try:
                sucesso = future.result()
                if not sucesso:
                    musicas_nao_baixadas.append(musica_info)
            except Exception as exc:
                print(f"✗ Erro inesperado ao processar {musica_info}: {exc}")
                musicas_nao_baixadas.append(musica_info)
    
    if musicas_nao_baixadas:
        with open(arquivo_output, 'w', encoding='utf-8') as file:
            file.write('\n'.join(musicas_nao_baixadas))
        print(f"\nConcluído! {len(musicas_nao_baixadas)} músicas não foram baixadas e foram salvas em '{arquivo_output}'")
    else:
        print("\nConcluído! Todas as músicas foram baixadas com sucesso.")
        if os.path.exists(arquivo_output):
            os.remove(arquivo_output)

if __name__ == "__main__":
    print("=== Baixador de Músicas MP3 (Lista Paralela) ===")
    print("Certifique-se de ter um arquivo 'input.txt' com uma música por linha no formato:")
    print("Artista - Nome da Música\n")
    
    # Exemplo de como usar a função com um número maior de workers
    processar_lista_musicas(max_workers=8)
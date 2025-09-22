import zipfile
from app import extrair_zip

def test_extrair_zip(tmp_path):
    # Cria um ZIP com um arquivo de texto
    zip_path = tmp_path / "teste.zip"
    arquivo_txt = tmp_path / "arquivo.txt"
    arquivo_txt.write_text("conteúdo de teste")

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(arquivo_txt, arcname="arquivo.txt")

    destino = tmp_path / "destino"
    destino.mkdir()

    extraidos = extrair_zip(str(zip_path), str(destino))
    assert "arquivo.txt" in extraidos
    assert (destino / "arquivo.txt").exists()
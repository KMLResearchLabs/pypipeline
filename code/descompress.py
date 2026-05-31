import zlib
import argparse
from pathlib import Path

NOME_INICIO = b"[<!>"
HEADER_FIM = b"<!>]"
COMPRESSOES_INICIO = b"[<#>"


def _parse_ppl(dados):
    inicio_marcador = dados.find(NOME_INICIO)
    fim_nome = dados.find(HEADER_FIM, inicio_marcador + len(NOME_INICIO))

    if inicio_marcador != 0 or fim_nome == -1:
        raise ValueError("Arquivo .ppl invalido: marcador de nome nao encontrado.")

    nome = dados[len(NOME_INICIO):fim_nome].decode()
    inicio_compressoes = fim_nome + len(HEADER_FIM)

    if dados.startswith(COMPRESSOES_INICIO, inicio_compressoes):
        fim_compressoes = dados.find(
            HEADER_FIM,
            inicio_compressoes + len(COMPRESSOES_INICIO),
        )
        if fim_compressoes == -1:
            raise ValueError(
                "Arquivo .ppl invalido: marcador de compressoes nao encontrado."
            )

        compressoes = int(
            dados[
                inicio_compressoes + len(COMPRESSOES_INICIO):fim_compressoes
            ].decode()
        )
        conteudo_comprimido = dados[fim_compressoes + len(HEADER_FIM):]
    else:
        compressoes = 1
        conteudo_comprimido = dados[fim_nome + len(HEADER_FIM):]

    if compressoes < 1:
        raise ValueError("Arquivo .ppl invalido: quantidade de compressoes invalida.")

    return nome, compressoes, conteudo_comprimido


def descompress(dados):
    nome, compressoes, _ = _parse_ppl(dados)
    conteudo = dados

    for camada in range(compressoes):
        nome, _, conteudo_comprimido = _parse_ppl(conteudo)

        # Descompressao
        conteudo = zlib.decompress(conteudo_comprimido)

        if camada < compressoes - 1:
            try:
                _parse_ppl(conteudo)
            except ValueError as erro:
                raise ValueError(
                    "Arquivo .ppl invalido: camada interna ausente antes do fim."
                ) from erro

    return nome, conteudo


def descompress_file(caminho, saida=None):
    caminho = Path(caminho)
    with open(caminho, "rb") as f:
        dados = f.read()

    nome, conteudo = descompress(dados)
    saida = Path(saida) if saida else Path(nome)

    with open(saida, "wb") as f:
        f.write(conteudo)

    return saida


def main():
    parser = argparse.ArgumentParser(
        description="Descomprime um arquivo .ppl."
    )
    parser.add_argument("arquivo", help="arquivo .ppl que sera descomprimido")
    parser.add_argument(
        "-o",
        "--output",
        help="caminho do arquivo restaurado; por padrao usa o nome salvo dentro do .ppl",
    )
    args = parser.parse_args()

    saida = descompress_file(args.arquivo, args.output)
    print(f"Arquivo descomprimido com sucesso: {saida}")


if __name__ == "__main__":
    main()

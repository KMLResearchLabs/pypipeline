import zlib
import argparse
from pathlib import Path

NOME_INICIO = b"[<!>"
HEADER_FIM = b"<!>]"
COMPRESSOES_INICIO = b"[<#>"
MODO_INICIO = b"[<m>"
MODO_ZLIB = "zlib"
MODO_STORE = "store"


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
        inicio_modo = fim_compressoes + len(HEADER_FIM)
        if dados.startswith(MODO_INICIO, inicio_modo):
            fim_modo = dados.find(
                HEADER_FIM,
                inicio_modo + len(MODO_INICIO),
            )
            if fim_modo == -1:
                raise ValueError(
                    "Arquivo .ppl invalido: marcador de modo nao encontrado."
                )
            modo = dados[inicio_modo + len(MODO_INICIO):fim_modo].decode()
            conteudo = dados[fim_modo + len(HEADER_FIM):]
        else:
            modo = MODO_ZLIB
            conteudo = dados[inicio_modo:]
    else:
        compressoes = 1
        modo = MODO_ZLIB
        conteudo = dados[fim_nome + len(HEADER_FIM):]

    if compressoes < 1:
        raise ValueError("Arquivo .ppl invalido: quantidade de compressoes invalida.")

    if modo not in (MODO_ZLIB, MODO_STORE):
        raise ValueError("Arquivo .ppl invalido: modo de armazenamento invalido.")

    return nome, compressoes, modo, conteudo


def descompress(dados):
    nome, compressoes, _, _ = _parse_ppl(dados)
    conteudo = dados

    for camada in range(compressoes):
        nome, _, modo, conteudo_payload = _parse_ppl(conteudo)

        if modo == MODO_ZLIB:
            conteudo = zlib.decompress(conteudo_payload)
        else:
            conteudo = conteudo_payload

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

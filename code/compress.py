from pathlib import Path
import zlib
import argparse

NOME_INICIO = b"[<!>"
HEADER_FIM = b"<!>]"
COMPRESSOES_INICIO = b"[<#>"
MODO_INICIO = b"[<m>"
MODO_ZLIB = "zlib"
MODO_STORE = "store"


def _parse_ppl_headers(dados):
    inicio_nome = dados.find(NOME_INICIO)
    fim_nome = dados.find(HEADER_FIM, inicio_nome + len(NOME_INICIO))

    if inicio_nome != 0 or fim_nome == -1:
        return None

    inicio_compressoes = fim_nome + len(HEADER_FIM)

    if dados.startswith(COMPRESSOES_INICIO, inicio_compressoes):
        fim_compressoes = dados.find(
            HEADER_FIM,
            inicio_compressoes + len(COMPRESSOES_INICIO),
        )
        if fim_compressoes == -1:
            return None

        nome = dados[len(NOME_INICIO):fim_nome].decode()
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
                return None
            conteudo = dados[fim_modo + len(HEADER_FIM):]
        else:
            conteudo = dados[inicio_modo:]

        return nome, compressoes, conteudo

    nome = dados[len(NOME_INICIO):fim_nome].decode()
    conteudo = dados[fim_nome + len(HEADER_FIM):]
    return nome, 1, conteudo


def _empacotar(nome, compressoes, modo, conteudo):
    return (
        NOME_INICIO
        + nome.encode()
        + HEADER_FIM
        + COMPRESSOES_INICIO
        + str(compressoes).encode()
        + HEADER_FIM
        + MODO_INICIO
        + modo.encode()
        + HEADER_FIM
        + conteudo
    )


def compress(caminho):
    caminho = Path(caminho)
    with open(caminho, "rb") as f:
        dados = f.read()

    headers = _parse_ppl_headers(dados) if caminho.suffix.lower() == ".ppl" else None
    if headers:
        nome, compressoes, _ = headers
        compressoes += 1
    else:
        nome = caminho.name
        compressoes = 1

    dados_comprimidos = zlib.compress(dados)
    if len(dados_comprimidos) < len(dados):
        modo = MODO_ZLIB
        conteudo = dados_comprimidos
    else:
        modo = MODO_STORE
        conteudo = dados

    # Pacote final
    pacote = _empacotar(nome, compressoes, modo, conteudo)

    return pacote


def compress_file(caminho, saida=None):
    caminho = Path(caminho)
    if saida:
        saida = Path(saida)
    elif caminho.suffix.lower() == ".ppl":
        saida = caminho.with_name(caminho.name + ".ppl")
    else:
        saida = caminho.with_suffix(".ppl")

    if caminho.resolve() == saida.resolve():
        raise ValueError("A saida nao pode ser o mesmo arquivo da entrada.")

    with open(saida, "wb") as f:
        f.write(compress(caminho))

    return saida


def main():
    parser = argparse.ArgumentParser(
        description="Comprime um arquivo para o formato .ppl."
    )
    parser.add_argument("arquivo", help="arquivo que sera comprimido")
    parser.add_argument(
        "-o",
        "--output",
        help="caminho do arquivo .ppl gerado; por padrao usa o mesmo nome com extensao .ppl",
    )
    args = parser.parse_args()

    saida = compress_file(args.arquivo, args.output)
    print(f"Arquivo comprimido com sucesso: {saida}")


if __name__ == "__main__":
    main()

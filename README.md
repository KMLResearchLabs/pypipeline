# PyPipeLine

PyPipeLine e um compactador simples de arquivos feito em Python. Ele transforma
um arquivo comum em um pacote `.ppl` usando `zlib` para compressao e `base64`
para armazenar o conteudo comprimido em um formato transportavel.

O projeto tambem salva metadados no arquivo `.ppl`, como o nome original do
arquivo e a quantidade de vezes que ele foi compactado.

## Recursos

- Compacta arquivos para o formato `.ppl`.
- Descompacta arquivos `.ppl` e restaura o nome original salvo no pacote.
- Permite escolher o caminho de saida com `--output`.
- Suporta compactar novamente um arquivo `.ppl`, mantendo a contagem de camadas.
- Usa apenas bibliotecas padrao do Python.

## Estrutura

```text
.
├── code/
│   ├── compress.py
│   └── descompress.py
├── test-files/
│   ├── test.ppl
│   └── test.txt
├── LICENSE
└── README.md
```

## Requisitos

- Python 3.8 ou superior

Nao e necessario instalar dependencias externas.

## Como usar

### Compactar um arquivo

```bash
python3 code/compress.py caminho/do/arquivo.txt
```

Por padrao, a saida usa o mesmo nome do arquivo com extensao `.ppl`.

Exemplo:

```bash
python3 code/compress.py test-files/test.txt
```

Gera:

```text
test-files/test.ppl
```

### Escolher o arquivo de saida

```bash
python3 code/compress.py test-files/test.txt -o test-files/saida.ppl
```

### Descompactar um arquivo

```bash
python3 code/descompress.py test-files/test.ppl
```

Por padrao, o arquivo restaurado usa o nome original salvo dentro do `.ppl`.

### Escolher o arquivo restaurado

```bash
python3 code/descompress.py test-files/test.ppl -o test-files/restaurado.txt
```

## Formato `.ppl`

Um arquivo `.ppl` gerado pelo projeto possui:

- marcador com o nome original do arquivo;
- marcador com a quantidade de compressoes;
- conteudo compactado com `zlib` e convertido para `base64`.

Os marcadores usados internamente sao:

```text
[<!>nome<!>][<#>quantidade<!>]conteudo
```

## Teste rapido

Para validar o fluxo basico:

```bash
python3 code/compress.py test-files/test.txt -o /tmp/test.ppl
python3 code/descompress.py /tmp/test.ppl -o /tmp/test.txt
```

Depois compare o arquivo original com o restaurado:

```bash
cmp test-files/test.txt /tmp/test.txt
```

Se o comando `cmp` nao mostrar nenhuma mensagem, os arquivos sao iguais.

## Licenca

Este projeto esta licenciado sob a licenca MIT. Consulte o arquivo
[LICENSE](LICENSE) para mais detalhes.

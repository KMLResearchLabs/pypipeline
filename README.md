# PyPipeLine

PyPipeLine e um compactador simples de arquivos feito em Python. Ele transforma
arquivos comuns em pacotes `.ppl`, guardando metadados como nome original,
quantidade de camadas de compactacao e modo de armazenamento.

O projeto tambem inclui um Local Drive com interface web e shell interativo. No
upload, o arquivo e salvo compactado como `.ppl`; no download pelo servidor web,
o conteudo e descompactado em memoria e baixado com o nome original.

## Recursos

- Compacta arquivos para o formato `.ppl`.
- Descompacta arquivos `.ppl` restaurando o nome original.
- Permite escolher caminhos de saida com `--output`.
- Suporta compactar novamente um `.ppl`, mantendo a contagem de camadas.
- Usa `zlib` quando reduz o tamanho e `store` quando nao vale compactar.
- Interface web local com upload, listagem e download descompactado.
- Shell interativo para listar, enviar, baixar e iniciar o servidor.
- Servidor acessivel na rede local pelo IP do computador.

## Estrutura

```text
.
├── code/
│   ├── PipeLine/
│   │   ├── app.py
│   │   ├── cli.py
│   │   ├── core.py
│   │   └── uploads/
│   └── compressor/
│       ├── compress.py
│       └── descompress.py
├── test-files/
│   ├── test.ppl
│   ├── test.txt
│   └── pgnp.jpeg
├── requirements.txt
├── LICENSE
└── README.md
```

## Requisitos

- Python 3.9 ou superior
- Dependencias listadas em `requirements.txt`
- Comando `ping` disponivel no sistema para os testes de rede da CLI

## Ambiente

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependencias:

```bash
python -m pip install -r requirements.txt
```

## Compactador

### Compactar

```bash
python3 code/compressor/compress.py test-files/test.txt
```

Por padrao, a saida usa o mesmo nome com extensao `.ppl`.

### Escolher saida

```bash
python3 code/compressor/compress.py test-files/test.txt -o /tmp/test.ppl
```

### Descompactar

```bash
python3 code/compressor/descompress.py /tmp/test.ppl -o /tmp/test.txt
```

### Validar restauracao

```bash
cmp test-files/test.txt /tmp/test.txt
```

Se `cmp` nao imprimir nada, os arquivos sao iguais.

## Servidor web

Execute diretamente:

```bash
python3 code/PipeLine/app.py
```

Por padrao, o Flask usa:

```text
http://0.0.0.0:5000
```

No navegador do proprio computador, acesse:

```text
http://127.0.0.1:5000
```

## Shell interativo

Inicie o shell:

```bash
python3 code/PipeLine/cli.py
```

Comandos disponiveis:

```text
list
upload <arquivo>
download <arquivo>
start
ping
test
clear
help
exit
```

O comando `start` inicia o servidor em `0.0.0.0`, escolhe uma porta livre entre
`5000` e `5019`, e imprime o link para acesso local e pela rede.

Exemplo:

```text
[INFO] Porta 5000 ocupada; usando 5001.
[ OK ] Servidor iniciado em http://127.0.0.1:5001
[ OK ] Para acessar a rede, tente:
    [+] http://192.168.0.204:5001
```

No celular, use o endereco com o IP da rede local, nao `127.0.0.1`.

Notas:

- `download <arquivo>` na CLI copia o arquivo armazenado para a pasta atual.
- O download pela interface web restaura o conteudo original em memoria e envia
  o nome salvo dentro do `.ppl`.
- `ping` testa uma lista de hosts conhecidos.
- `test` mede perda, latencia media e jitter usando `1.1.1.1`.

## Fluxo de arquivos

1. O usuario envia um arquivo pela web ou pela CLI.
2. O arquivo original e salvo temporariamente em `code/PipeLine/uploads/`.
3. O sistema compacta esse arquivo para `.ppl`.
4. O arquivo temporario original e removido.
5. A listagem mostra o nome original salvo no `.ppl`.
6. No download web, o `.ppl` e descompactado em memoria.
7. O navegador baixa o conteudo restaurado com o nome original.

Os arquivos gerados em `code/PipeLine/uploads/` sao dados locais de execucao e
devem ficar fora do Git.

## Acesso pelo celular

Para acessar pelo celular:

1. Conecte computador e celular no mesmo Wi-Fi.
2. Rode `start` dentro da CLI.
3. Abra no celular exatamente o link impresso pela CLI.
4. Use `http`, nao `https`.
5. Use a porta impressa. Se a CLI disser `5001`, use `:5001`.

Se nao abrir no celular, verifique:

- celular em dados moveis, VPN ou outra rede;
- Wi-Fi convidado com isolamento de clientes;
- firewall bloqueando portas de entrada;
- porta diferente da mostrada no terminal.

Em sistemas com UFW, uma liberacao comum e:

```bash
sudo ufw allow 5000:5019/tcp
```

## Formato `.ppl`

Um pacote `.ppl` possui:

- marcador com o nome original;
- marcador com a quantidade de compactacoes;
- marcador com o modo de armazenamento;
- conteudo compactado com `zlib` ou armazenado sem compressao.

Formato:

```text
[<!>nome<!>][<#>quantidade<!>][<m>modo<!>]conteudo
```

Modos:

- `zlib`: conteudo compactado;
- `store`: conteudo armazenado sem compressao.

## Licenca

Este projeto esta licenciado sob a licenca MIT. Consulte [LICENSE](LICENSE).


## 🏆 Sobre o Projeto — PES Wii Editor

Este projeto nasceu da curiosidade e da vontade de entender o que acontece dentro dos arquivos do **PES 2013 para Nintendo Wii**.  
Durante dias de testes, erros, descobertas e noites longas de bytes e offsets, eu e o ChatGPT mergulhamos fundo na estrutura do arquivo **`edit_u1`**, que guarda praticamente toda a alma dos jogadores do jogo.

Conseguimos descobrir que:
- Cada jogador ocupa exatamente **124 bytes**, e mapeamos boa parte desses dados (nomes, atributos, aparência, etc).  
- Aprendemos a identificar **como o jogo organiza e indexa os blocos** dentro do `edit_u1`.  
- Descobrimos que o Wii faz uma **verificação de integridade** (checksum) ao carregar o save — e que uma simples alteração de 1 byte é suficiente para o jogo recusar o arquivo como “dados corrompidos”.  
- Criamos scripts em Python para **calcular CRC16-XModem**, comparar arquivos aceitos e recusados e até tentar reconstruir os checksums.  
- E, claro, desenvolvemos o **PES_Wii_Editor_Alpha_0.4**, a melhor versão do nosso editor até aqui: funcional, intuitiva e capaz de modificar diretamente os arquivos binários do jogo.

Mas também encontramos **o limite do projeto**:  
Mesmo corrigindo o CRC16 e mantendo toda a estrutura byte a byte, o Wii ainda recusa o save. Isso indica que há uma **segunda camada de verificação**, possivelmente uma assinatura digital do container do save, que só o console (ou uma ferramenta de homebrew) consegue reconstruir.

---

## 💬 Reflexão pessoal

Não posso dizer que o projeto “falhou” — porque ele **me ensinou mais do que qualquer tutorial ou curso**.  
Aprendi sobre leitura binária, estruturas internas, compressão, verificação de integridade e até sobre a forma como jogos antigos protegiam seus dados.  
E principalmente: aprendi que cada byte conta.

O código e os scripts estão aqui para quem quiser continuar essa jornada.  
Talvez alguém no futuro encontre o pedaço que faltava — o checksum misterioso, a tabela escondida, ou a chave de assinatura do save.  
Se isso acontecer, espero que este repositório ajude como base, e que cada linha de código aqui escrita sirva pra mostrar que o impossível é só questão de paciência e curiosidade.

---

**Criado com 🧠 e 💻 por Breno Rodrigues, com a ajuda do ChatGPT**  
Licenciado sob **GNU GPL v3.0**  
*(porque o conhecimento deve permanecer livre — sempre).*

---


# PES Wii Editor (Alpha_0.4)

Projeto de engenharia reversa e editor para o jogo **Pro Evolution Soccer 2013 (Wii)**.

## 🎯 Objetivo
Compreender e editar os arquivos internos do jogo — especialmente `edit_u1` e `unnamed_46.bin_000`, que armazenam os dados dos jogadores e times.

## ⚙️ Principais Descobertas
- Cada jogador ocupa **124 bytes** no `edit_u1`.
- Os atributos (ataque, defesa, etc.) são armazenados diretamente nesses blocos.
- O Wii faz **verificação interna de integridade**, recusando saves alterados sem checksum válido.
- Atualizamos parcialmente a verificação (CRC16-XModem) mas o save ainda falha — há uma segunda verificação (provavelmente assinatura de container).

## 🧩 Estrutura do Projeto

```
PES_Wii_Editor_GPLv3_Project/
│
├── README.md
├── LICENSE (GPL v3.0)
├── .gitignore
├── PES_Wii_Editor_Alpha_0.4.py   # Editor principal
└── scripts/
    ├── checksum_test.py          # Teste CRC32 simples
    ├── extract_players.py        # Leitura de jogadores
    └── analyze_header.py         # Análise do header (264 bytes iniciais)
```

## 🧰 Editor (Alpha_0.4)
**PES_Wii_Editor_Alpha_0.4** é a versão mais estável e funcional do editor.

### Funcionalidades
- Abre e edita diretamente os arquivos `edit_u1` e `unnamed_46.bin_000`.
- Permite importar dados do `edit_u1` e gravar diretamente sem criar `edit_u3`.
- Edição direta de atributos (ataque, defesa, etc.) com preservação de offsets.
- Interface amigável com ícones e botões.
- Atualiza dados no arquivo binário sem gerar cópias temporárias.

### Limitações
- O Wii ainda recusa saves editados (verificação adicional não identificada).
- Algumas strings (nomes de jogadores) precisam de tratamento de encoding/padding.

## 🧪 Scripts auxiliares
Fornecem análise de estrutura, verificação de checksums e leitura dos dados dos jogadores.

## 🧠 Conclusão
Mesmo sem quebrar totalmente a verificação, este projeto representa um grande avanço no entendimento dos saves do PES 2013 Wii.

Criado por **Breno Rodrigues** e **ChatGPT**.

Distribuído sob a licença **GNU GPL v3.0**.

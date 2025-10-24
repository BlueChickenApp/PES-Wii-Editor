
import struct
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import openpyxl
import os
import zlib
import threading
import shutil

# === CONFIGURAÇÕES FIXAS ===
OFFSET_INICIAL = 0x188
OFFSET_FINAL = 0xD2318
BLOCO_TAMANHO = 124
OFFSET_ATRIBUTOS = 0x36
NUM_ATRIBUTOS = 26

# === CONFIGURAÇÕES PARA 046.BIN ===
OFFSET_INICIAL_BIN = 0x7C
OFFSET_FINAL_BIN = 0xD220B
ZLIB_OFFSET = 0x80

NOMES_ATRIBUTOS = [
    "Ataque", "Defesa", "Equilíbrio", "Resistência", "Velocidade", "Aceleração",
    "Resposta", "Agilidade", "Drible Precisão", "Drible Velocidade",
    "Passe Curto Precisão", "Passe Curto Velocidade", "Passe Longo Precisão",
    "Passe Longo Velocidade", "Chute Precisão", "Chute Força", "Chute Técnica",
    "Falta Precisão", "Efeito", "Cabeçada", "Impulsão", "Trabalho Equipe",
    "Técnica", "Agressividade", "Atitude", "Habilidade Goleiro"
]

def byte_to_valor(byte):
    return max(1, min(99, round(byte / 2)))

def valor_to_byte(valor):
    return min(0xC6, int(valor) * 2)

def descomprimir_zlib(origem, destino, progress_callback=None):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(origem, 'rb') as f:
        f.seek(ZLIB_OFFSET)
        data = f.read()
        if progress_callback:
            progress_callback(30)
        descompactado = zlib.decompress(data)
        if progress_callback:
            progress_callback(80)
    with open(destino, 'wb') as out:
        out.write(descompactado)
    if progress_callback:
        progress_callback(100)

def recomprimir_zlib(origem, destino, progress_callback=None):
    with open(origem, 'rb') as f:
        data = f.read()
        if progress_callback:
            progress_callback(30)
        compactado = zlib.compress(data, level=9)
        if progress_callback:
            progress_callback(80)
    with open(destino, 'wb') as out:
        out.write(b'\x00' * ZLIB_OFFSET)
        out.write(compactado)
    if progress_callback:
        progress_callback(100)

def ler_jogadores(filepath, inicio, fim):
    jogadores = []
    with open(filepath, "rb") as f:
        f.seek(inicio)
        id_counter = 1
        while f.tell() < fim:
            offset_atual = f.tell()
            bloco = f.read(BLOCO_TAMANHO)
            if len(bloco) < BLOCO_TAMANHO:
                break

            nome_raw = bloco[0:32]
            nome = nome_raw.decode('utf-16le', errors='ignore').split('\x00')[0]

            nome_curto_raw = bloco[32:48]
            nome_curto = nome_curto_raw.decode('ascii', errors='ignore').split('\x00')[0]

            atributos_raw = bloco[OFFSET_ATRIBUTOS:OFFSET_ATRIBUTOS + NUM_ATRIBUTOS]
            atributos = [byte_to_valor(b) for b in atributos_raw]

            jogadores.append({
                "id": f"{id_counter:04d}",
                "offset": offset_atual,
                "nome": nome,
                "nome_curto": nome_curto,
                "atributos": atributos
            })
            id_counter += 1
    return jogadores

def salvar_jogadores(filepath_original, jogadores):
    backup_path = filepath_original + ".bak"
    try:
        with open(filepath_original, "rb") as f:
            dados = bytearray(f.read())
        with open(backup_path, "wb") as f:
            f.write(dados)
    except Exception as e:
        messagebox.showwarning("Aviso", f"Não foi possível criar backup: {e}")

    for j in jogadores:
        base = j["offset"]
        if len(dados) < base + BLOCO_TAMANHO:
            dados.extend(b'\x00' * ((base + BLOCO_TAMANHO) - len(dados)))

        nome_bytes = j["nome"].encode("utf-16le")
        nome_bytes = nome_bytes[:32] + b"\x00" * max(0, 32 - len(nome_bytes))
        dados[base:base + 32] = nome_bytes

        nome_curto_bytes = j["nome_curto"].encode("ascii", errors="ignore")
        nome_curto_bytes = nome_curto_bytes[:16] + b"\x00" * max(0, 16 - len(nome_curto_bytes))
        dados[base + 32:base + 48] = nome_curto_bytes

        for i, valor in enumerate(j["atributos"]):
            byte_val = valor_to_byte(valor)
            dados[base + OFFSET_ATRIBUTOS + i] = byte_val

    with open(filepath_original, "wb") as f:
        f.write(dados)

class EditorPES:
    def __init__(self, root):
        self.root = root
        self.root.title("PES Wii Editor Alpha 0.3")
        self.root.geometry("950x650")
        self.jogadores = []
        self.caminho_arquivo = ""
        self.tipo_arquivo = ""

        barra = ttk.Frame(root, padding=10)
        barra.pack(fill="x")

        ttk.Button(barra, text="Abrir Data Base", command=self.abrir_arquivo).pack(side="left", padx=5)
        self.btn_importar = ttk.Button(barra, text="Importar edit_u1 → unnamed_46.bin", command=self.importar_edit, state="disabled")
        self.btn_importar.pack(side="left", padx=5)
        ttk.Button(barra, text="Salvar Alterações", command=self.salvar_alteracoes).pack(side="left", padx=5)

        ttk.Label(barra, text="Pesquisar:").pack(side="left", padx=5)
        self.pesquisa_var = tk.StringVar()
        pesquisa_entry = ttk.Entry(barra, textvariable=self.pesquisa_var)
        pesquisa_entry.pack(side="left", fill="x", expand=True)
        pesquisa_entry.bind("<KeyRelease>", self.filtrar_jogadores)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=5)

        self.tree = ttk.Treeview(root, columns=("ID", "Nome", "Nome Curto"), show="headings", height=20)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Nome Curto", text="Nome Curto")
        self.tree.column("ID", width=60)
        self.tree.column("Nome", width=300)
        self.tree.column("Nome Curto", width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.abrir_editor_jogador)

    def atualizar_progresso(self, valor):
        self.progress['value'] = valor
        self.root.update_idletasks()

    def abrir_arquivo(self):
        caminho = filedialog.askopenfilename(title="Selecione a Data Base (edit_u1 ou unnamed_46.bin)")
        if not caminho:
            return
        try:
            if caminho.lower().endswith(".bin"):
                destino = os.path.join("data", "046_BIN_EXTRACTED.bin")
                descomprimir_zlib(caminho, destino, self.atualizar_progresso)
                self.jogadores = ler_jogadores(destino, OFFSET_INICIAL_BIN, OFFSET_FINAL_BIN)
                self.tipo_arquivo = "compactado"
                self.btn_importar.config(state="normal")
            else:
                self.jogadores = ler_jogadores(caminho, OFFSET_INICIAL, OFFSET_FINAL)
                self.tipo_arquivo = "edit"
            self.caminho_arquivo = caminho
            self.atualizar_lista(self.jogadores)
            messagebox.showinfo("Sucesso", f"{len(self.jogadores)} jogadores carregados!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ler o arquivo:\n{e}")
        finally:
            self.progress['value'] = 0

    def importar_edit(self):
        if self.tipo_arquivo != "compactado":
            messagebox.showwarning("Aviso", "Abra primeiro o arquivo unnamed_46.bin antes de importar.")
            return

        caminho_edit = filedialog.askopenfilename(title="Selecione o Option File edit_u1")
        if not caminho_edit:
            return

        def tarefa():
            try:
                self.atualizar_progresso(10)
                jogadores_edit = ler_jogadores(caminho_edit, OFFSET_INICIAL, OFFSET_FINAL)
                destino_temp = os.path.join("data", "046_BIN_EXTRACTED.bin")

                OFFSET_CORRECAO = OFFSET_INICIAL_BIN - OFFSET_INICIAL
                jogadores_corrigidos = []
                for j in jogadores_edit:
                    novo = j.copy()
                    novo["offset"] = j["offset"] + OFFSET_CORRECAO
                    jogadores_corrigidos.append(novo)

                salvar_jogadores(destino_temp, jogadores_corrigidos)
                self.atualizar_progresso(70)
                recomprimir_zlib(destino_temp, self.caminho_arquivo, self.atualizar_progresso)
                messagebox.showinfo("Sucesso", "Dados do edit_u1 importados e alinhados corretamente ao unnamed_46.bin!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha na importação:\n{e}")
            finally:
                shutil.rmtree("data", ignore_errors=True)
                self.progress['value'] = 0

        threading.Thread(target=tarefa).start()

    def atualizar_lista(self, lista):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for j in lista:
            self.tree.insert("", "end", values=(j["id"], j["nome"], j["nome_curto"]))

    def filtrar_jogadores(self, event=None):
        termo = self.pesquisa_var.get().lower()
        if not termo:
            self.atualizar_lista(self.jogadores)
        else:
            filtrados = [j for j in self.jogadores if termo in j["nome"].lower() or termo in j["nome_curto"].lower() or termo in j["id"].lower()]
            self.atualizar_lista(filtrados)

    def abrir_editor_jogador(self, event):
        item = self.tree.selection()
        if not item:
            return
        id_sel = self.tree.item(item[0], "values")[0]
        jogador = next((j for j in self.jogadores if j["id"] == id_sel), None)
        if jogador:
            self.janela_edicao(jogador)

    def janela_edicao(self, jogador):
        win = tk.Toplevel(self.root)
        win.title(f"Editar {jogador['id']} - {jogador['nome']}")
        win.geometry("400x700")

        ttk.Label(win, text=f"ID: {jogador['id']}").pack(pady=5)
        ttk.Label(win, text="Nome:").pack()
        nome_var = tk.StringVar(value=jogador["nome"])
        ttk.Entry(win, textvariable=nome_var).pack(fill="x", padx=10, pady=5)

        ttk.Label(win, text="Nome Curto:").pack()
        nome_curto_var = tk.StringVar(value=jogador["nome_curto"])
        ttk.Entry(win, textvariable=nome_curto_var).pack(fill="x", padx=10, pady=5)

        ttk.Label(win, text="Atributos:").pack(pady=10)
        attr_vars = []
        for i, nome_attr in enumerate(NOMES_ATRIBUTOS):
            frame = ttk.Frame(win)
            frame.pack(fill="x", padx=10)
            ttk.Label(frame, text=nome_attr, width=22).pack(side="left")
            var = tk.IntVar(value=jogador["atributos"][i])
            ttk.Entry(frame, textvariable=var, width=5).pack(side="right")
            attr_vars.append(var)

        def salvar():
            jogador["nome"] = nome_var.get()
            jogador["nome_curto"] = nome_curto_var.get()
            jogador["atributos"] = [max(1, min(99, v.get())) for v in attr_vars]
            messagebox.showinfo("OK", "Alterações salvas na memória! Use 'Salvar Alterações' para gravar no arquivo.")
            win.destroy()

        ttk.Button(win, text="Salvar", command=salvar).pack(pady=10)

    def salvar_alteracoes(self):
        if not self.caminho_arquivo or not self.jogadores:
            messagebox.showerror("Erro", "Nenhum arquivo carregado.")
            return

        if self.tipo_arquivo == "compactado":
            destino_temp = os.path.join("data", "046_BIN_EXTRACTED.bin")
            salvar_jogadores(destino_temp, self.jogadores)

            def tarefa():
                recomprimir_zlib(destino_temp, self.caminho_arquivo, self.atualizar_progresso)
                messagebox.showinfo("Sucesso", f"Alterações aplicadas e arquivo recompresso em:\n{self.caminho_arquivo}")
                shutil.rmtree("data", ignore_errors=True)
                self.progress['value'] = 0

            threading.Thread(target=tarefa).start()
        elif self.tipo_arquivo == "edit":
            salvar_jogadores(self.caminho_arquivo, self.jogadores)

if __name__ == "__main__":
    root = tk.Tk()
    app = EditorPES(root)
    root.mainloop()

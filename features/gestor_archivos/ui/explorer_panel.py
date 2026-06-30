import os
import tkinter as tk
from tkinter import ttk, messagebox


COLORS = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "border": "#E2E8F0",
    "border_focus": "#93C5FD",
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "accent": "#1D4ED8",
    "accent_light": "#EFF6FF",
    "accent_hover": "#1E40AF",
    "folder_active_bg": "#EFF6FF",
    "folder_active_fg": "#1D4ED8",
    "row_selected": "#EFF6FF",
}


def _apply_tree_style(name, row_height=26):
    style = ttk.Style()
    style.configure(
        f"{name}.Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text_primary"],
        font=("Segoe UI", 9),
        rowheight=row_height,
    )
    style.configure(
        f"{name}.Treeview.Heading",
        font=("Segoe UI", 9, "bold"),
        background=COLORS["bg"],
        foreground=COLORS["text_secondary"],
        relief="flat",
        padding=(8, 4),
    )
    style.map(
        f"{name}.Treeview",
        background=[("selected", COLORS["row_selected"])],
        foreground=[("selected", COLORS["accent"])],
    )


class ExplorerPanel:
    def __init__(self, parent, on_add_operation=None):
        self.on_add_operation = on_add_operation
        self.page_size = 250
        self.current_page = 0
        self.folder_page_size = 100
        self.folder_current_page = 0

        self.frame = tk.Frame(parent, bg=COLORS["bg"])

        self.paned = tk.PanedWindow(
            self.frame,
            orient="horizontal",
            sashrelief="flat",
            sashwidth=4,
            bg=COLORS["border"],
        )
        self.paned.pack(fill="both", expand=True)

        self.archivos = []
        self.archivos_filtrados = []
        self.carpetas = []
        self.folder_map = {}
        self.carpeta_actual = None

        _apply_tree_style("Folders", row_height=28)
        _apply_tree_style("Files", row_height=26)

        self._crear_panel_carpetas()
        self._crear_panel_archivos()

    def _panel_card(self, parent):
        return tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )

    def _section_header(self, parent, title, badge_var=None):
        header = tk.Frame(parent, bg=COLORS["surface"])
        header.pack(fill="x", padx=12, pady=(10, 6))

        tk.Label(
            header,
            text=title,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
        ).pack(side="left")

        if badge_var is not None:
            lbl = tk.Label(
                header,
                textvariable=badge_var,
                font=("Segoe UI", 8),
                bg=COLORS["bg"],
                fg=COLORS["text_secondary"],
                padx=7,
                pady=1,
            )
            lbl.pack(side="right")
            return header, lbl

        return header

    def _pager(self, parent, on_prev, on_next, label_var):
        bar = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        bar.pack(fill="x")

        tk.Button(
            bar,
            text="‹",
            font=("Segoe UI", 11),
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            relief="flat",
            cursor="hand2",
            command=on_prev,
        ).pack(side="left", padx=(8, 0), pady=4)

        tk.Label(
            bar,
            textvariable=label_var,
            font=("Segoe UI", 8),
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
        ).pack(side="left", expand=True)

        tk.Button(
            bar,
            text="›",
            font=("Segoe UI", 11),
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            relief="flat",
            cursor="hand2",
            command=on_next,
        ).pack(side="right", padx=(0, 8), pady=4)

    def _crear_panel_carpetas(self):
        frame = self._panel_card(self.paned)

        self._folder_badge = tk.StringVar(value="0")
        self._section_header(frame, "CARPETAS", self._folder_badge)

        tree_frame = tk.Frame(frame, bg=COLORS["surface"])
        tree_frame.pack(fill="both", expand=True, padx=8)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree_folders = ttk.Treeview(
            tree_frame,
            style="Folders.Treeview",
            show="tree",
        )

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_folders.yview)
        self.tree_folders.configure(yscrollcommand=yscroll.set)
        self.tree_folders.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        self.tree_folders.bind("<<TreeviewSelect>>", self._on_folder_select)

        self._folder_page_var = tk.StringVar(value="1 / 1")
        self._pager(
            frame,
            self.pagina_carpetas_anterior,
            self.pagina_carpetas_siguiente,
            self._folder_page_var,
        )

        self.paned.add(frame, minsize=210)

    def _crear_panel_archivos(self):
        frame = self._panel_card(self.paned)

        self._files_badge = tk.StringVar(value="0 archivos")
        self._section_header(frame, "ARCHIVOS", self._files_badge)

        search_frame = tk.Frame(
            frame,
            bg=COLORS["bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        search_frame.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(
            search_frame,
            text="🔍",
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(6, 0))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 9),
            bg=COLORS["bg"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["accent"],
            relief="flat",
            bd=4,
        )
        search_entry.pack(side="left", fill="x", expand=True)
        self.search_var.trace_add("write", lambda *_: self._filtrar())

        actions_frame = tk.Frame(frame, bg=COLORS["surface"])
        actions_frame.pack(fill="x", padx=12, pady=(0, 6))

        for texto, cmd in [
            ("Seleccionar todo", self.seleccionar_todos),
            ("Mover", lambda: self._crear_operacion("mover")),
            ("Copiar", lambda: self._crear_operacion("copiar")),
            ("Eliminar", lambda: self._crear_operacion("eliminar")),
        ]:
            self._action_btn(actions_frame, texto, cmd)

        columns = ("nombre", "peso")

        table_frame = tk.Frame(frame, bg=COLORS["surface"])
        table_frame.pack(fill="both", expand=True, padx=8)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree_files = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Files.Treeview",
        )

        self.tree_files.heading("nombre", text="Nombre")
        self.tree_files.heading("peso", text="Tamaño")

        self.tree_files.column("nombre", width=480)
        self.tree_files.column("peso", width=100, stretch=False, anchor="e")

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_files.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree_files.xview)
        self.tree_files.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.tree_files.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        self.tree_files.bind("<Button-3>", self._menu_contextual)

        self._files_page_var = tk.StringVar(value="1 / 1")
        self._pager(
            frame,
            self.pagina_anterior,
            self.pagina_siguiente,
            self._files_page_var,
        )

        self.paned.add(frame)

    @staticmethod
    def _action_btn(parent, texto, cmd):
        btn = tk.Button(
            parent,
            text=texto,
            command=cmd,
            font=("Segoe UI", 8),
            bg=COLORS["bg"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["border"],
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        btn.pack(side="left", padx=(0, 4))
        return btn

    def cargar_archivos(self, archivos):
        self.archivos = archivos
        self.archivos_filtrados = []
        self.carpeta_actual = None
        self.current_page = 0
        self.folder_current_page = 0

        self.tree_folders.delete(*self.tree_folders.get_children())
        self.tree_files.delete(*self.tree_files.get_children())

        self.carpetas = sorted(set(a["carpeta"] for a in archivos))
        self._folder_badge.set(str(len(self.carpetas)))

        self._mostrar_pagina_carpetas()
        self._filtrar()

    def limpiar_archivos(self):
        self.archivos = []
        self.archivos_filtrados = []
        self.carpetas = []
        self.folder_map = {}
        self.carpeta_actual = None
        self.current_page = 0
        self.folder_current_page = 0

        self.tree_folders.delete(*self.tree_folders.get_children())
        self.tree_files.delete(*self.tree_files.get_children())

        self._folder_badge.set("0")
        self._files_badge.set("0 archivos")
        self._files_page_var.set("1 / 1")
        self._folder_page_var.set("1 / 1")

    def _mostrar_pagina_carpetas(self):
        self.tree_folders.delete(*self.tree_folders.get_children())

        total = len(self.carpetas)
        total_paginas = max(1, (total + self.folder_page_size - 1) // self.folder_page_size)

        if self.folder_current_page >= total_paginas:
            self.folder_current_page = total_paginas - 1

        inicio = self.folder_current_page * self.folder_page_size
        fin = inicio + self.folder_page_size
        self.folder_map = {}

        for carpeta in self.carpetas[inicio:fin]:
            item = self.tree_folders.insert("", "end", text=carpeta)
            self.folder_map[item] = carpeta

        self._folder_page_var.set(
            f"{self.folder_current_page + 1} / {total_paginas}"
        )

    def pagina_carpetas_anterior(self):
        if self.folder_current_page <= 0:
            return
        self.folder_current_page -= 1
        self._mostrar_pagina_carpetas()

    def pagina_carpetas_siguiente(self):
        total = len(self.carpetas)
        total_paginas = max(1, (total + self.folder_page_size - 1) // self.folder_page_size)
        if self.folder_current_page >= total_paginas - 1:
            return
        self.folder_current_page += 1
        self._mostrar_pagina_carpetas()

    def _mostrar_archivos(self, archivos):
        self.tree_files.delete(*self.tree_files.get_children())
        for archivo in archivos:
            self.tree_files.insert(
                "",
                "end",
                values=(archivo["nombre"], self._human_size(archivo["peso"])),
                tags=(archivo["ruta"],),
            )

    def _on_folder_select(self, _event):
        selected = self.tree_folders.selection()
        if not selected:
            return
        self.carpeta_actual = self.folder_map[selected[0]]
        self._filtrar()

    def _archivos_visibles(self):
        archivos = self.archivos

        if self.carpeta_actual:
            archivos = [a for a in archivos if a["carpeta"] == self.carpeta_actual]

        texto = self.search_var.get().lower().strip()
        if texto:
            archivos = [a for a in archivos if texto in a["nombre"].lower()]

        return archivos

    def obtener_archivos_listados(self):
        return list(self.archivos_filtrados or self._archivos_visibles())

    def _filtrar(self):
        self.current_page = 0
        self.archivos_filtrados = self._archivos_visibles()
        self._mostrar_pagina_actual()

    def _mostrar_pagina_actual(self):
        total = len(self.archivos_filtrados)
        total_paginas = max(1, (total + self.page_size - 1) // self.page_size)

        if self.current_page >= total_paginas:
            self.current_page = total_paginas - 1

        inicio = self.current_page * self.page_size
        fin = inicio + self.page_size
        self._mostrar_archivos(self.archivos_filtrados[inicio:fin])

        self._files_badge.set(f"{total:,} archivos")
        self._files_page_var.set(
            f"{self.current_page + 1} / {total_paginas}"
        )

    def pagina_anterior(self):
        if self.current_page <= 0:
            return
        self.current_page -= 1
        self._mostrar_pagina_actual()

    def pagina_siguiente(self):
        total = len(self.archivos_filtrados)
        total_paginas = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page >= total_paginas - 1:
            return
        self.current_page += 1
        self._mostrar_pagina_actual()

    def seleccionar_todos(self):
        items = self.tree_files.get_children()
        if not items:
            return
        self.tree_files.selection_set(items)
        self.tree_files.focus(items[0])

    def _menu_contextual(self, event):
        item = self.tree_files.identify_row(event.y)
        if item and item not in self.tree_files.selection():
            self.tree_files.selection_set(item)
            self.tree_files.focus(item)

        selected = self.tree_files.selection()
        if not selected:
            return

        menu = tk.Menu(self.frame, tearoff=0, font=("Segoe UI", 9))
        menu.add_command(label="Mover a carpeta...", command=lambda: self._crear_operacion("mover"))
        menu.add_command(label="Copiar a carpeta...", command=lambda: self._crear_operacion("copiar"))
        menu.add_separator()
        menu.add_command(label="Eliminar", command=lambda: self._crear_operacion("eliminar"))
        menu.tk_popup(event.x_root, event.y_root)

    def _crear_operacion(self, accion):
        from tkinter import filedialog

        selected = self.tree_files.selection()
        if not selected:
            messagebox.showwarning("Sin selección", "Selecciona uno o más archivos primero.")
            return

        destino_base = None
        if accion in ["mover", "copiar"]:
            destino_base = filedialog.askdirectory(title="Seleccionar carpeta destino")
            if not destino_base:
                return

        operaciones = []
        for item in selected:
            tags = self.tree_files.item(item, "tags")
            if not tags:
                continue
            ruta = tags[0]
            nombre = os.path.basename(ruta)
            op = {"accion": accion, "origen": ruta}
            if destino_base:
                op["destino"] = os.path.join(destino_base, nombre)
            operaciones.append(op)

        if operaciones and self.on_add_operation:
            self.on_add_operation(operaciones)

    @staticmethod
    def _human_size(size):
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

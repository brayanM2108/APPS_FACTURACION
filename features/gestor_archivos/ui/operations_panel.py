import os
import tkinter as tk
from tkinter import ttk


COLORS = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "border": "#E2E8F0",
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "accent": "#1D4ED8",
    "row_even": "#F8FAFC",
    "row_odd": "#FFFFFF",
    "tag_mover": ("#DBEAFE", "#1E40AF"),
    "tag_copiar": ("#DCFCE7", "#166534"),
    "tag_eliminar": ("#FEE2E2", "#991B1B"),
}

ACTION_COLORS = {
    "mover": ("#DBEAFE", "#1E40AF"),
    "copiar": ("#DCFCE7", "#166534"),
    "eliminar": ("#FEE2E2", "#991B1B"),
}


class OperationsPanel:
    def __init__(self, parent):
        self.frame = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )

        header = tk.Frame(self.frame, bg=COLORS["surface"])
        header.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(
            header,
            text="Operaciones pendientes",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
        ).pack(side="left")

        self.count_label = tk.Label(
            header,
            text="0 operaciones",
            font=("Segoe UI", 9),
            bg="#EFF6FF",
            fg="#1D4ED8",
            padx=8,
            pady=2,
        )
        self.count_label.pack(side="right")

        style = ttk.Style()
        style.configure(
            "Ops.Treeview",
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text_primary"],
            font=("Segoe UI", 9),
            rowheight=26,
        )
        style.configure(
            "Ops.Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background=COLORS["bg"],
            foreground=COLORS["text_secondary"],
            relief="flat",
        )
        style.map("Ops.Treeview", background=[("selected", "#EFF6FF")])

        columns = ("accion", "archivo", "destino")

        table_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=5,
            style="Ops.Treeview",
        )

        self.tree.heading("accion", text="Acción")
        self.tree.heading("archivo", text="Archivo")
        self.tree.heading("destino", text="Destino")

        self.tree.column("accion", width=90, stretch=False)
        self.tree.column("archivo", width=320)
        self.tree.column("destino", width=480)

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("mover", foreground="#1E40AF", background="#EFF6FF")
        self.tree.tag_configure("copiar", foreground="#166534", background="#F0FDF4")
        self.tree.tag_configure("eliminar", foreground="#991B1B", background="#FEF2F2")

        self._count = 0

    def agregar_operaciones(self, operaciones):
        for op in operaciones:
            accion = op["accion"]
            self._count += 1
            self.tree.insert(
                "",
                "end",
                values=(
                    accion.upper(),
                    os.path.basename(op["origen"]),
                    op.get("destino", "—"),
                ),
                tags=(accion,),
            )
        self._actualizar_count()

    def limpiar(self):
        self._count = 0
        self.tree.delete(*self.tree.get_children())
        self._actualizar_count()

    def _actualizar_count(self):
        n = self._count
        self.count_label.config(
            text=f"{n} operación{'es' if n != 1 else ''}",
            bg="#EFF6FF" if n > 0 else "#F1F5F9",
            fg="#1D4ED8" if n > 0 else "#64748B",
        )

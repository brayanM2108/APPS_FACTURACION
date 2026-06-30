import tkinter as tk


COLORS = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "border": "#E2E8F0",
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "log_bg": "#0F1117",
    "ok": "#22D3A5",
    "info": "#60A5FA",
    "warn": "#F59E0B",
    "error": "#F87171",
    "font_ui": ("Segoe UI", 9),
    "font_mono": ("Consolas", 9),
}


class LogsPanel:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=COLORS["bg"])

        header = tk.Frame(self.frame, bg=COLORS["bg"])
        header.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(
            header,
            text="Logs",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text_secondary"],
        ).pack(side="left")

        self.count_label = tk.Label(
            header,
            text="",
            font=COLORS["font_ui"],
            bg=COLORS["bg"],
            fg=COLORS["text_secondary"],
        )
        self.count_label.pack(side="right")

        container = tk.Frame(
            self.frame,
            bg=COLORS["log_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        container.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.text = tk.Text(
            container,
            height=7,
            bg=COLORS["log_bg"],
            fg="#94A3B8",
            insertbackground="white",
            relief="flat",
            font=COLORS["font_mono"],
            padx=10,
            pady=8,
            state="disabled",
            cursor="arrow",
            selectbackground="#1E293B",
            selectforeground="#E2E8F0",
        )

        scrollbar = tk.Scrollbar(container, command=self.text.yview, bg=COLORS["log_bg"])
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.text.tag_config("ok", foreground=COLORS["ok"])
        self.text.tag_config("info", foreground=COLORS["info"])
        self.text.tag_config("warn", foreground=COLORS["warn"])
        self.text.tag_config("error", foreground=COLORS["error"])

        self._count = 0

    def log(self, mensaje, error=False):
        tag = "error" if error else ("ok" if mensaje.upper().startswith("OK") else "info")
        self._count += 1

        self.text.configure(state="normal")
        self.text.insert("end", mensaje + "\n", tag)
        self.text.see("end")
        self.text.configure(state="disabled")

        self.count_label.config(text=f"{self._count} entradas")

    def limpiar(self):
        self._count = 0
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
        self.count_label.config(text="")

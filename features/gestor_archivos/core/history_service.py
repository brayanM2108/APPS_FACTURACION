class HistoryService:
    def __init__(self):
        self.historial = []

    def registrar(self, operacion):
        self.historial.append(operacion)

    def deshacer_ultima(self):
        if not self.historial:
            return None

        return self.historial.pop()
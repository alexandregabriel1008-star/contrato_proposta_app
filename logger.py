import csv
from datetime import datetime
import os

def registrar_solicitacao(cliente, documentos):
    os.makedirs("logs", exist_ok=True)

    with open("logs/solicitacoes.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            cliente,
            ", ".join(documentos)
        ])

import numpy as np
from rich.console import Console
from utils.bin_dataset import BinDataset
from training.train import load_tokenizer
import random

console = Console()

# Cargar tokenizer
class DummyArgs:
    vocab_path = "input/vocab.json"
    merges_path = "input/vocab.json"  # placeholder
tokenizer = load_tokenizer(DummyArgs)

# Cargar dataset
dataset = BinDataset("input/moTrain.bin", "input/moTrain.idx", tokenizer, block_size=128, debug=False)

# Diccionario de colores para IDs especiales
SPECIAL_IDS = {
    8: "blue",    # PROMPT
    9: "yellow",  # THINK
    10: "green",  # ANSWER
    11: "magenta",# OUTPUT
    3: "red"      # EOS
}

def visualize_sample(idx, dataset):
    x, y = dataset[idx]

    x = np.array(x) if not isinstance(x, np.ndarray) else x
    y = np.array(y) if not isinstance(y, np.ndarray) else y

    tokens_entrenables = np.sum(y != -100)
    console.rule(f"Sample idx: {idx} | Tokens entrenables: {tokens_entrenables}")

    x_list = x.tolist()
    y_list = y.tolist()

    # Diccionario para agrupar palabras por tipo
    tokens_por_tipo = {color: [] for color in SPECIAL_IDS.values()}
    ignorados = []

    # Decodificar token por token
    for xi, yi in zip(x_list, y_list):
        palabra = dataset.tokenizer.decode([xi]).strip()
        if yi == -100:
            ignorados.append(palabra)
        elif yi in SPECIAL_IDS:
            color = SPECIAL_IDS[yi]
            tokens_por_tipo[color].append(palabra)
        else:
            # Tokens normales que no son especiales ni ignorados
            pass

    # Mostrar tokens agrupados
    for color, palabras in tokens_por_tipo.items():
        if palabras:
            console.print(f"[{color}]{color.upper()} ({len(palabras)} palabras):[/] {' '.join(palabras)}")

    if ignorados:
        console.print(f"[white]IGNORADOS ({len(ignorados)} palabras):[/] {' '.join(ignorados)}")

    # Texto completo decodificado
    try:
        decoded = dataset.tokenizer.decode(x_list)
        console.print("\nTexto decodificado:")
        console.print(decoded)
    except Exception as e:
        console.print("Decode error:", e)


# Visualizar 5 muestras aleatorias
for _ in range(5):
    visualize_sample(random.randint(0, len(dataset)-1), dataset)

    
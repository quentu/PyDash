from rich.layout import Layout
import math

def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def build_layout(servers):
    server_count = len(servers)
    layout = Layout()
    layout.split_column(Layout(name="main"))

    main = layout["main"]

    if server_count <= 2:
        # Keep simple row layout
        main.split_row(
            *[Layout(name=s["name"]) for s in servers]
        )
    else:
        # Create grid layout
        cols = math.ceil(math.sqrt(server_count))
        rows = list(chunk_list(servers, cols))

        main.split_column(
            *[
                Layout(name=f"row_{i}") for i in range(len(rows))
            ]
        )

        for i, row in enumerate(rows):
            main[f"row_{i}"].split_row(
                *[Layout(name=s["name"]) for s in row]
            )

    return layout

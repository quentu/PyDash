from rich.layout import Layout

def build_layout(servers):
    layout = Layout()
    layout.split_column(Layout(name="main"))

    layout["main"].split_row(
        *[Layout(name=s["name"]) for s in servers]
    )

    return layout

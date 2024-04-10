def print_attributes(obj, indent=0):
    print(
        "\n".join(
            [
                " " * indent
                + f"{attr}: {getattr(obj, attr) if not hasattr(getattr(obj, attr), '__dict__') else print_attributes(getattr(obj, attr), indent + 2)}"
                for attr in dir(obj)
                if not attr.startswith("__")
            ]
        )
    )

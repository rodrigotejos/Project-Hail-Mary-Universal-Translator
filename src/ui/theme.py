import flet as ft

# Sci-Fi aesthetic theme
THEME = {
    "accent_color": "#00f0ff", # Cyan neon
    "status_color": "#ff9000", # Orange neon
    "bg_color": "#000000",
    "border_color": "#00f0ff",
    "text_color": "#00f0ff",
}

def get_theme():
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=THEME["accent_color"],
            surface=THEME["bg_color"],
        )
    )

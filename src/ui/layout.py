"""
Layout definitions for the Universal Translator UI.
"""
# pylint: disable=unexpected-keyword-arg, too-many-function-args, no-member
import flet as ft
from ui.theme import THEME


def create_panel(title, content):
    """Creates a standardized panel with title and content."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, color=THEME["accent_color"], size=16, weight="bold"),
                ft.Divider(color=THEME["border_color"]),
                content,
            ]
        ),
        border=ft.border.Border(
            top=ft.BorderSide(1, THEME["border_color"]),
            right=ft.BorderSide(1, THEME["border_color"]),
            bottom=ft.BorderSide(1, THEME["border_color"]),
            left=ft.BorderSide(1, THEME["border_color"]),
        ),
        padding=10,
        border_radius=5,
    )

def create_main_layout():
    """Creates the main layout structure for the application and returns interactive controls."""
    txt_cloud_status = ft.Text("[Cloud] STATUS: OFFLINE", color=THEME["status_color"], key="txt-cloud-status")
    btn_sync_cloud = ft.ElevatedButton("SINCRONIZAR NUVEM", icon=ft.Icons.SYNC, key="btn-sync-cloud")
    input_word_key = ft.TextField(hint_text="digite a palavra...", key="input-word-key")
    input_conversation_msg = ft.TextField(hint_text="escrever mensagem...", key="input-conversation-msg")

    # Learning Module
    left_content = ft.Column([
        ft.Text("MÓDULO DE APRENDIZADO", color=THEME["accent_color"]),
        ft.Container(height=100, bgcolor="#1a1a1a"), # Mock waveform
        ft.ElevatedButton("OUVIR ÁUDIO CAPTADO", bgcolor=THEME["accent_color"], color="black", key="btn-listen-audio"),
        ft.Text("ENTRADA DE DADOS: PORTUGUÊS", color="white"),
        ft.Text("MÚSICA", size=40, weight="bold", color="#ff9000"),
        input_word_key,
        ft.Row([
            ft.Icon(ft.Icons.MIC, color=THEME["accent_color"]),
            ft.Text("(Falar)"),
            ft.Icon(ft.Icons.CHECK_CIRCLE, color="green"),
            ft.Text("(Confirmar)")
        ])
    ])

    # Conversation Module
    right_content = ft.Column([
        ft.Text("MÓDULO DE CONVERSAÇÃO", color=THEME["accent_color"]),
        ft.Container(height=300, bgcolor="#0a0a0a", border=ft.border.Border(
            top=ft.BorderSide(1, "#333"),
            right=ft.BorderSide(1, "#333"),
            bottom=ft.BorderSide(1, "#333"),
            left=ft.BorderSide(1, "#333")
        )),
        input_conversation_msg,
        ft.Row([
            ft.Icon(ft.Icons.MIC, color=THEME["accent_color"]),
            ft.Text("(Falar)"),
            ft.Icon(ft.Icons.SEND, color=THEME["accent_color"]),
            ft.Text("(Enviar)")
        ])
    ])

    header_row = ft.Row([
        ft.Text("PROJETO: TRADUÇÃO UNIVERSAL ....", size=20, color=THEME["accent_color"]),
        ft.Row([
            txt_cloud_status,
            btn_sync_cloud
        ], spacing=15)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    layout_container = ft.Container(
        content=ft.Column([
            header_row,
            ft.Row([
                ft.Container(create_panel("MÓDULO DE APRENDIZADO", left_content), expand=True),
                ft.Container(create_panel("MÓDULO DE CONVERSAÇÃO", right_content), expand=True),
            ], vertical_alignment=ft.CrossAxisAlignment.START)
        ]),
        padding=20,
        border=ft.border.Border(
            top=ft.BorderSide(2, THEME["border_color"]),
            right=ft.BorderSide(2, THEME["border_color"]),
            bottom=ft.BorderSide(2, THEME["border_color"]),
            left=ft.BorderSide(2, THEME["border_color"]),
        ),
        border_radius=10,
        bgcolor="#050505"
    )

    controls = {
        "txt_cloud_status": txt_cloud_status,
        "btn_sync_cloud": btn_sync_cloud,
        "input_word_key": input_word_key,
        "input_conversation_msg": input_conversation_msg
    }

    return layout_container, controls

import flet as ft
from classeviva import Utente
from collections import defaultdict
import asyncio

# --- Funzioni di Utilità (Logica Matematica) ---

def parse_voto(voto_str):
    """Converte stringhe come '7+', '6-', '7/8' in float. Stessa logica dell'originale."""
    if not voto_str:
        return None
    
    voto_str = str(voto_str).replace(",", ".").strip()
    
    try:
        return float(voto_str)
    except ValueError:
        base_voto = ""
        modifier = 0.0
        
        if "+" in voto_str:
            base_voto = voto_str.replace("+", "")
            modifier = 0.25
        elif "-" in voto_str:
            base_voto = voto_str.replace("-", "")
            modifier = -0.25
        elif "½" in voto_str:
            base_voto = voto_str.replace("½", "")
            modifier = 0.5
        elif "/" in voto_str:
            parts = voto_str.split("/")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return (float(parts[0]) + float(parts[1])) / 2
            return None 
        
        try:
            return float(base_voto) + modifier
        except:
            return None

# --- Applicazione Principale ---

async def main(page: ft.Page):
    # Configurazione della finestra (utile per test su PC, su Android sarà tutto schermo)
    page.title = "Analisi Voti Classeviva"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    # Per Android, abilitiamo lo scroll automatico se la tastiera copre i campi
    page.scroll = "adaptive"

    # --- Elementi UI: Login ---
    logo_text = ft.Text("Classeviva Stats", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600)
    
    txt_username = ft.TextField(
        label="Username / Codice", 
        width=300, 
        prefix_icon=ft.Icons.PERSON,
        keyboard_type=ft.KeyboardType.TEXT
    )
    
    txt_password = ft.TextField(
        label="Password", 
        width=300, 
        password=True, 
        can_reveal_password=True, 
        prefix_icon=ft.Icons.LOCK
    )
    
    progress_ring = ft.ProgressRing(visible=False)
    error_text = ft.Text("", color=ft.Colors.RED, visible=False)

    async def btn_login_click(e):
        """Gestisce il click del login"""
        user = txt_username.value
        pwd = txt_password.value

        if not user or not pwd:
            txt_username.error_text = "Inserisci username" if not user else None
            txt_password.error_text = "Inserisci password" if not pwd else None
            page.update()
            return

        # UI: Mostra caricamento e disabilita input
        error_text.visible = False
        progress_ring.visible = True
        btn_login.disabled = True
        page.update()

        try:
            # FASE 1 e 2: Login e Recupero Dati (Asincrono)
            utente = Utente(user, pwd)
            await utente.accedi()
            voti_raw = await utente.voti()

            # FASE 3: Elaborazione Dati
            data_by_subject = defaultdict(list)
            all_grades_values = []

            for voto in voti_raw:
                # Gestione sicura delle chiavi del dizionario
                materia = voto.get('subjectDesc', voto.get('subject', 'Sconosciuta'))
                
                # Cerca il valore in vari campi possibili
                valore_str = voto.get('displayValue', voto.get('display_value', voto.get('decimalValue', '')))
                
                valore_num = parse_voto(valore_str)

                if valore_num is not None:
                    data_by_subject[materia].append((valore_num, str(valore_str)))
                    all_grades_values.append(valore_num)

            media_generale = 0.0
            if all_grades_values:
                media_generale = sum(all_grades_values) / len(all_grades_values)

            # Passa alla Dashboard
            await show_dashboard(data_by_subject, media_generale)

        except Exception as err:
            error_text.value = f"Errore: {str(err)}"
            error_text.visible = True
            print(f"Errore tecnico: {err}") # Log console per debug
        finally:
            # Ripristina UI in caso di errore
            progress_ring.visible = False
            btn_login.disabled = False
            page.update()

    btn_login = ft.ElevatedButton(
        text="Accedi e Analizza", 
        on_click=btn_login_click, 
        width=300, 
        height=50
    )

    # --- Elementi UI: Dashboard ---
    async def show_dashboard(data, media_totale):
        """Costruisce la schermata dei risultati"""
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.padding = 10

        # Header Dashboard
        color_media = ft.Colors.GREEN if media_totale >= 6 else ft.Colors.RED
        
        header = ft.Container(
            content=ft.Column([
                ft.Text("Riepilogo Voti", size=24, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Text("Media Totale: ", size=20),
                    ft.Text(f"{media_totale:.2f}", size=24, weight=ft.FontWeight.BOLD, color=color_media)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ]),
            padding=20,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            width=float("inf") # Larghezza piena
        )

        # Lista Materie (Usiamo Cards invece di Treeview per mobile)
        cards_list = []
        
        # Ordina le materie alfabeticamente
        sorted_subjects = sorted(data.keys())

        for materia in sorted_subjects:
            voti_list = data[materia]
            valori_numerici = [v[0] for v in voti_list]
            media_materia = sum(valori_numerici) / len(valori_numerici) if valori_numerici else 0
            
            # Colore media materia
            media_color = ft.Colors.GREEN if media_materia >= 6 else ft.Colors.RED
            
            # Ordina voti (decrescente)
            voti_ordinati = sorted(voti_list, key=lambda x: x[0], reverse=True)
            voti_display_str = ", ".join([v[1] for v in voti_ordinati])

            # Creazione Card
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.BOOK),
                            title=ft.Text(materia, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"Media: {media_materia:.2f}", color=media_color, weight=ft.FontWeight.BOLD),
                        ),
                        ft.Container(
                            content=ft.Text(f"Voti: {voti_display_str}", italic=True),
                            padding=ft.padding.only(left=20, right=20, bottom=15)
                        )
                    ])
                )
            )
            cards_list.append(card)

        # Bottone Logout
        async def logout_click(e):
            page.clean()
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            # Ricrea la pagina di login
            page.add(
                ft.Column(
                    [logo_text, txt_username, txt_password, btn_login, progress_ring, error_text],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            page.update()

        btn_logout = ft.ElevatedButton("Logout / Indietro", on_click=logout_click, icon=ft.Icons.LOGOUT)

        # Aggiungi tutto alla pagina (Header + Lista scrollabile + Logout)
        page.add(
            header,
            ft.Column(cards_list, scroll=ft.ScrollMode.AUTO, expand=True),
            ft.Container(content=btn_logout, padding=10)
        )
        page.update()

    # --- Avvio App ---
    # Aggiungi i widget iniziali (Login Screen)
    page.add(
        ft.Column(
            [
                logo_text,
                ft.Container(height=20), # Spazio
                txt_username,
                txt_password,
                ft.Container(height=20), # Spazio
                btn_login,
                ft.Container(height=20), # Spazio
                progress_ring,
                error_text
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
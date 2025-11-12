import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText  # legacy; replaced by Canvas for background image
import random
import os
import math

# Réutiliser la logique existante depuis main.py
import main as game

try:
    from ollama import chat
except Exception:  # permet d'afficher un message clair si ollama n'est pas dispo
    chat = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Enquête interactive - Interface graphique")
        # Augmente la taille de la fenêtre pour permettre une colonne gauche large
        self.geometry("1600x850")

        # Thème police/enquête
        self.theme = {
            'bg': '#0f1a2b',           # bleu nuit
            'panel': '#14233b',        # panneau
            'panel_alt': '#0b1627',    # zone sombre (chat, liste)
            'text': '#e6edf3',
            'muted': '#9aa7b0',
            'accent': '#ffd60a',       # jaune bande de police
            'suspect': '#58a6ff',      # bleu pour suspects
            'danger': '#ff6b6b'        # rouge léger (accuser)
        }
        self.configure(bg=self.theme['bg'])

        # Etats
        self.profils = None
        self.crimes_data = None
        self.crime_choisi = None
        self.personnes_enquete = []
        # messages par index de suspect -> liste de messages (chat ollama)
        self.conversations = {}
        self.current_index = None
        self.sending_lock = threading.Lock()

        # UI
        self._build_ui()

        # Données
        self._charger_donnees()
        self.nouvelle_enquete()

    # ---------- Données ----------
    def _charger_donnees(self):
        try:
            self.profils = game.charger_profils()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger profils.json\n{e}")
            self.destroy()
            return
        try:
            self.crimes_data = game.charger_crimes()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger crimes.json\n{e}")
            self.destroy()
            return

    # ---------- UI ----------
    def _build_ui(self):
        t = self.theme
        # Bandeau info crime
        header = tk.Frame(self, bg=t['panel'], bd=0)
        header.pack(side=tk.TOP, fill=tk.X)

        self.lbl_titre = tk.Label(header, text="🕵️ Enquête interactive", font=("Segoe UI", 16, "bold"), bg=t['panel'], fg=t['text'])
        self.lbl_titre.pack(side=tk.LEFT, padx=10, pady=10)

        btn_nouvelle = tk.Button(header, text="Nouvelle enquête", command=self.nouvelle_enquete,
                                 bg=t['panel_alt'], fg=t['text'], activebackground=t['panel'], activeforeground=t['accent'],
                                 bd=1, relief=tk.GROOVE)
        btn_nouvelle.pack(side=tk.RIGHT, padx=10, pady=8)

        # bande jaune style ruban police
        tape = tk.Frame(self, bg=t['accent'], height=3)
        tape.pack(side=tk.TOP, fill=tk.X)

        # Corps principal split gauche/droite
        body = tk.Frame(self, bg=t['bg'])
        body.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Colonne gauche: suspects
        left = tk.Frame(body, width=250, bg=t['panel'])
        left.pack(side=tk.LEFT, fill=tk.Y)
        # Empêche Tkinter de réduire la largeur du cadre à la taille de son contenu
        left.pack_propagate(False)

        tk.Label(left, text="Suspects", font=("Segoe UI", 12, "bold"), bg=t['panel'], fg=t['accent']).pack(anchor="w", padx=10, pady=(10, 4))

        self.listbox = tk.Listbox(left, height=20, bg=t['panel_alt'], fg=t['text'], selectbackground=t['accent'], selectforeground='#000000', bd=0, highlightthickness=0)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))
        self.listbox.bind("<<ListboxSelect>>", self._on_select_suspect)

        self.btn_accuser = tk.Button(left, text="Accuser le suspect sélectionné", command=self.accuser_selection,
                                     bg=t['danger'], fg='#000000', activebackground='#ff8787', activeforeground='#000000',
                                     bd=1, relief=tk.GROOVE)
        self.btn_accuser.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Colonne droite: conversation
        right = tk.Frame(body, bg=t['panel'])
        right.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(10, 0))

        self.lbl_crime = tk.Label(right, text="", justify=tk.LEFT, anchor="w", bg=t['panel'], fg=t['muted'], font=("Segoe UI", 10))
        self.lbl_crime.pack(fill=tk.X, padx=10, pady=(10, 0))

        # Zone de chat: Canvas + Scrollbar pour supporter une image de fond
        chat_frame = tk.Frame(right, bg=t['panel'])
        chat_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=(6, 6))
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        self.chat_canvas = tk.Canvas(chat_frame, bg=t['panel_alt'], highlightthickness=0)
        self.chat_canvas.grid(row=0, column=0, sticky="nsew")
        self.chat_scroll = tk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self._on_scrollbar)
        self.chat_scroll.grid(row=0, column=1, sticky="ns")
        self.chat_canvas.configure(yscrollcommand=self.chat_scroll.set)
        # Données de rendu
        self.chat_draw_messages = []
        # Bindings de redimensionnement et molette
        self.chat_canvas.bind('<Configure>', lambda e: self._redraw_chat())
        self.chat_canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        
        # Charger l'image de fond si disponible
        self._load_logo_image()
        # Premier rendu
        self._redraw_chat()

        input_row = tk.Frame(right, bg=t['panel'])
        input_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.entry = tk.Entry(input_row, bg=t['panel_alt'], fg=t['text'], insertbackground=t['accent'], bd=1, relief=tk.FLAT)
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.entry.bind('<Return>', lambda e: self.envoyer_message())
        self.btn_send = tk.Button(input_row, text="Envoyer", command=self.envoyer_message,
                                  bg=t['panel_alt'], fg=t['text'], activebackground=t['panel'], activeforeground=t['accent'],
                                  bd=1, relief=tk.GROOVE)
        self.btn_send.pack(side=tk.LEFT, padx=6)

    def _load_logo_image(self):
        # Recherche d'un fichier logo dans le projet
        self.logo_image = None
        candidates = [
            'Logo_Police_Municipale_(France).png',
            'pj_logo.png',
            'pj_logo.gif',
            os.path.join('assets', 'pj_logo.png'),
            os.path.join('assets', 'pj_logo.gif'),
            'logo_pj.png',
            'logo_pj.gif'
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)
        if not path:
            return
        try:
            img = tk.PhotoImage(file=path)
            # Mise à l'échelle simple si trop grand pour la zone
            max_w, max_h = 480, 240
            w, h = img.width(), img.height()
            factor = max(math.ceil(w / max_w), math.ceil(h / max_h), 1)
            if factor > 1:
                img = img.subsample(factor, factor)
            self.logo_image = img
        except Exception:
            self.logo_image = None

    def _insert_logo_if_any(self):
        # Ancienne méthode (Text). Conservée pour compatibilité; déclenche simplement un redraw Canvas
        self._redraw_chat()

    # ---------- Rendu Canvas du chat ----------
    def _redraw_chat(self):
        if not hasattr(self, 'chat_canvas'):
            return
        c = self.chat_canvas
        c.delete('all')
        width = max(c.winfo_width(), 10)
        height = max(c.winfo_height(), 10)
        pad_x = 12
        pad_y = 10
        y = pad_y
        # Dessiner l'image de fond si disponible, centrée dans la zone visible
        if getattr(self, 'logo_image', None):
            try:
                x0 = c.canvasx(0)
                y0 = c.canvasy(0)
                cx = x0 + width / 2
                cy = y0 + height / 2
                self._bg_image_id = c.create_image(cx, cy, image=self.logo_image, anchor='center')
            except Exception:
                pass
        # Couleurs: vert pour questions (utilisateur), jaune pour réponses (assistant)
        user_color = '#2ecc71'  # vert
        assistant_color = self.theme['accent']  # jaune déjà dans le thème
        line_gap = 8
        # Dessiner les messages
        for speaker, text in self.chat_draw_messages:
            is_user = (speaker == 'Vous')
            spk_color = user_color if is_user else assistant_color
            # Speaker
            spk_id = c.create_text(pad_x, y, text=speaker + ": ", fill=spk_color,
                                   font=("Segoe UI", 10, 'bold'), anchor='nw')
            bbox = c.bbox(spk_id)
            y = bbox[3] + 2 if bbox else y + 18
            # Content (même couleur que le speaker)
            content_id = c.create_text(pad_x, y, text=text, fill=spk_color,
                                       font=("Segoe UI", 10), anchor='nw', width=max(50, width - pad_x*2))
            bbox = c.bbox(content_id)
            y = bbox[3] + line_gap if bbox else y + 20 + line_gap
        # Mettre à jour la zone scrollable
        c.configure(scrollregion=(0, 0, width, y + pad_y))

    def _on_mousewheel(self, event):
        if not hasattr(self, 'chat_canvas'):
            return
        # Sur Windows, delta est multiple de 120
        delta = int(-1 * (event.delta / 120)) if event.delta else 0
        self.chat_canvas.yview_scroll(delta, 'units')
        self._redraw_chat()

    def _on_scrollbar(self, *args):
        if not hasattr(self, 'chat_canvas'):
            return
        # Proxy pour le Scrollbar afin de pouvoir redessiner l'image centrée
        self.chat_canvas.yview(*args)
        self._redraw_chat()

    def _scroll_to_bottom(self):
        if not hasattr(self, 'chat_canvas'):
            return
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
        self._redraw_chat()

        # ---------- Enquête ----------
    def nouvelle_enquete(self):
        if not self.profils or not self.crimes_data:
            return
        self.crime_choisi = random.choice(self.crimes_data['crimes'])
        self.personnes_enquete = game.initialiser_enquete(self.profils, self.crime_choisi)
        self.conversations = {i: [
            {
                'role': 'system',
                'content': game.creer_prompt_systeme(self.personnes_enquete[i], self.crime_choisi)
            }
        ] for i in range(len(self.personnes_enquete))}
        self._refresh_header()
        self._remplir_liste()
        # Sélectionner automatiquement le premier suspect pour afficher l'historique
        if self.personnes_enquete:
            self.current_index = 0
            try:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(0)
            except Exception:
                pass
            self._afficher_conversation(0)
        else:
            self._clear_chat()
            self.current_index = None

    def _refresh_header(self):
        c = self.crime_choisi
        titre = f"🧵 Dossier: {c['nom']}  |  Victime: {c['victime']}  |  Lieu: {c['lieu']}  |  Heure: {c['heure']}  |  Indices: {c['indices']}"
        # Conserver le titre stylé
        self.lbl_titre.config(text="🕵️ Enquête interactive")
        self.lbl_crime.config(text=titre)

    def _remplir_liste(self):
        self.listbox.delete(0, tk.END)
        for p in self.personnes_enquete:
            self.listbox.insert(tk.END, f"{p['prenom']} — {p['metier']}")

    # ---------- Interaction suspect ----------
    def _on_select_suspect(self, event=None):
        idxs = self.listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        self.current_index = idx
        self._afficher_conversation(idx)

    def _afficher_conversation(self, idx):
        self._clear_chat()
        msgs = self.conversations.get(idx, [])
        for m in msgs:
            if m['role'] == 'user':
                self._append_chat("Vous", m['content'])
            elif m['role'] == 'assistant':
                self._append_chat(self.personnes_enquete[idx]['prenom'], m['content'])

    def _clear_chat(self):
        # Efface le rendu et les messages
        self.chat_draw_messages = []
        self._redraw_chat()

    def _append_chat(self, speaker, text):
        # Ajoute un message et redessine (sans animation)
        self.chat_draw_messages.append((speaker, text))
        self._redraw_chat()
        self._scroll_to_bottom()

    def _append_chat_typewriter(self, speaker, text, delay_ms=30):
        # Ajoute un message qui s'affiche caractère par caractère toutes les 0.03s
        # Insère d'abord une entrée vide, puis remplace progressivement
        start_index = len(self.chat_draw_messages)
        self.chat_draw_messages.append((speaker, ""))
        self._redraw_chat()
        self._scroll_to_bottom()

        def step(i=0):
            if i > len(text):
                return
            # Remplacer le tuple à l'index par la portion courante
            self.chat_draw_messages[start_index] = (speaker, text[:i])
            self._redraw_chat()
            self._scroll_to_bottom()
            if i < len(text):
                self.after(delay_ms, lambda: step(i + 1))
        step(0)

    def envoyer_message(self):
        if self.current_index is None:
            messagebox.showinfo("Choisir un suspect", "Sélectionnez d'abord un suspect dans la liste.")
            return
        content = self.entry.get().strip()
        if not content:
            return
        self.entry.delete(0, tk.END)

        idx = self.current_index
        conv = self.conversations[idx]
        conv.append({'role': 'user', 'content': content})
        self._append_chat_typewriter("Vous", content, delay_ms=30)

        # Appel Ollama en thread pour ne pas bloquer l'UI
        if chat is None:
            self._append_chat(self.personnes_enquete[idx]['prenom'], "[Erreur] Ollama non disponible sur cette machine.")
            return

        def worker():
            # Empêche messages concurrents sur le même bouton
            with self.sending_lock:
                try:
                    response = chat(model='gemma3', messages=conv)
                    # L'objet retourné peut être dict-like selon la version
                    ai_text = getattr(response, 'message', None).content if hasattr(response, 'message') else response['message']['content']
                    conv.append({'role': 'assistant', 'content': ai_text})

                    self.after(0, lambda: self._append_chat_typewriter(self.personnes_enquete[idx]['prenom'], ai_text, delay_ms=30))
                except Exception as e:
                    self.after(0, lambda: self._append_chat(self.personnes_enquete[idx]['prenom'], f"[Erreur] {e}"))

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Accusation ----------
    def accuser_selection(self):
        if not self.personnes_enquete:
            return

        # Demander confirmation + choisir si besoin
        idxs = self.listbox.curselection()
        if idxs:
            accuse_idx = idxs[0]
        else:
            # Demande via simpledialog (numéro 1..4)
            try:
                numero = simpledialog.askinteger("Accuser", "Numéro du suspect à accuser (1 à 4)", minvalue=1, maxvalue=len(self.personnes_enquete))
            except Exception:
                numero = None
            if not numero:
                return
            accuse_idx = numero - 1

        accuse = self.personnes_enquete[accuse_idx]
        if not messagebox.askyesno("Confirmation", f"Vous accusez {accuse['prenom']} ?"):
            return

        if accuse['role'] == 'coupable':
            messagebox.showinfo("Résultat", f"Bravo ! {accuse['prenom']} était bien le coupable.")
        else:
            coupable = next(p for p in self.personnes_enquete if p['role'] == 'coupable')
            messagebox.showwarning("Résultat", f"Raté. {accuse['prenom']} était innocent.\nLe vrai coupable était {coupable['prenom']}.")

    # ---------- Lancement ----------


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()

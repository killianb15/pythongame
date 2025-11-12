# Enquête interactive – Jeu d’interrogatoire assisté par IA

Un mini‑jeu d’enquête policière où vous interrogez des suspects générés à partir de profils et d’un dossier criminel. Le jeu fonctionne en mode console (CLI) et via une interface graphique Tkinter (GUI) avec un thème « police judiciaire » et un logo en arrière‑plan du chat.


## Fonctionnalités
- Sélection aléatoire d’un crime et de 4 suspects (dont 1 coupable).
- Conversation avec chaque suspect, propulsée par un modèle local via Ollama.
- Interface graphique moderne façon « enquête »:
  - Liste des suspects, zone de chat à fond personnalisé, bandeau « scène de crime ».
  - Image de fond centrée (logo de la police) dans la zone de chat.
  - Couleurs de messages: vert pour vos questions, jaune pour les réponses du suspect.
  - Le « prompt système » (définition du personnage) n’est pas affiché dans le chat.
- Mode console minimaliste disponible.
- Possibilité d’accuser un suspect et d’obtenir le verdict.


## Aperçu rapide des fichiers
- gui.py: interface graphique Tkinter (recommandée).
- main.py: logique métier + mode console (CLI).
- profils.json: base de données des personnages (suspects potentiels).
- crimes.json: base de données des affaires (crimes).
- Logo_Police_Municipale_(France).png: logo utilisé comme fond (facultatif, peut être remplacé).


## Prérequis
- Windows (le projet a été conçu/testé pour Windows, chemins « \\ » et molette souris gérés)
- Python 3.9+ (Tkinter inclus dans les distributions standard Windows)
- Ollama installé et lancé en local: https://ollama.com/
- Paquet Python ollama (client):
  
  ```bash
  pip install ollama
  ```
- Modèle disponible dans Ollama sous le nom « gemma3 » (vous pouvez l’adapter, voir plus bas):
  
  ```bash
  ollama pull gemma3
  ```

Si Ollama n’est pas installé ou pas lancé, l’interface GUI indiquera une erreur dans la zone de chat lors de l’envoi d’un message; en CLI, l’exception sera affichée.


## Installation
1. Clonez ou copiez ce dépôt sur votre machine Windows.
2. (Optionnel) Créez un environnement virtuel Python.
3. Installez la dépendance client:
   
   ```bash
   pip install ollama
   ```
4. Installez/lancez Ollama et assurez-vous que le modèle « gemma3 » est disponible:
   
   ```bash
   ollama pull gemma3
   ollama run gemma3  # test rapide
   ```


## Lancement
### Interface Graphique (recommandé)
```bash
python gui.py
```
- Au démarrage, une nouvelle enquête est créée automatiquement.
- Le premier suspect est sélectionné et sa conversation est prête (sans afficher le message système).
- Tapez votre question dans le champ en bas et appuyez sur Entrée.
- Pour accuser, utilisez le bouton « Accuser le suspect sélectionné ».

### Mode Console (CLI)
```bash
python main.py
```
- Sélectionnez une personne à interroger ou choisissez l’option pour accuser.
- Entrez vos questions; tapez « retour » pour changer de personne, ou « quit » pour quitter.


## Personnalisation
### Image de fond du chat (GUI)
Le programme recherche automatiquement une image à utiliser comme fond (filigrane) du chat. Fichiers détectés dans cet ordre:
- Logo_Police_Municipale_(France).png
- pj_logo.png / pj_logo.gif
- assets/pj_logo.png / assets/pj_logo.gif
- logo_pj.png / logo_pj.gif

Placez votre image sous l’un de ces noms/emplacements à la racine du projet (ou dans assets/). L’image est centrée horizontalement et verticalement. Si l’image est trop grande, elle est réduite simplement via Tkinter (subsample).

### Couleurs et thème
- Fond de l’appli: bleu nuit
- Accents: jaune « ruban de police »
- Messages:
  - Vous: vert (#2ecc71)
  - Suspect: jaune (accent)

Vous pouvez modifier ces couleurs dans gui.py (dictionnaire self.theme et rendu dans _redraw_chat).

### Modèle Ollama
Par défaut, le code appelle:
```
chat(model='gemma3', messages=...)
```
Modifiez la valeur « gemma3 » dans gui.py et main.py si vous souhaitez utiliser un autre modèle disponible localement via Ollama.


## Données d’enquête
- profils.json: contient un tableau "personnes" avec pour chaque suspect: prenom, metier, temperament… Le rôle (innocent/coupable) est attribué dynamiquement à chaque enquête.
- crimes.json: contient un tableau "crimes" décrivant chaque affaire (victime, lieu, heure, arme, cause_mort, indices…).

Vous pouvez enrichir ces fichiers pour créer de nouvelles enquêtes et varier les profils.


## Dépannage
- « Ollama non disponible » dans le chat:
  - Vérifiez que le service Ollama tourne localement.
  - Vérifiez que le package Python ollama est installé.
  - Assurez-vous que le modèle « gemma3 » est présent (ollama pull gemma3).
- Aucune image de fond:
  - Vérifiez que votre fichier porte l’un des noms listés plus haut et qu’il est au bon emplacement.
  - Les formats supportés par Tkinter PhotoImage dans ce projet: PNG et GIF.
- Erreurs de chargement JSON:
  - Vérifiez l’existence et la validité de profils.json et crimes.json (UTF‑8, JSON valide).


## Notes techniques
- La GUI remplace la zone de texte par un Canvas pour dessiner l’image de fond centrée et le texte par‑dessus, tout en gardant un défilement fluide (molette et ascenseur). Le prompt système est conservé dans le contexte envoyé au modèle mais n’est pas affiché.
- Le code cible Windows et Tkinter; il peut fonctionner ailleurs, mais l’expérience n’est pas garantie telle quelle.


## Licence
Projet à usage éducatif/démo.

from ollama import chat
from ollama import ChatResponse
import json
import os
import random

def charger_crimes():
    if os.path.exists('crimes.json'):
        with open('crimes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print("erreur json crime ")
        exit
        with open('crimes.json', 'w', encoding='utf-8') as f:
            json.dump(crimes_default, f, indent=2, ensure_ascii=False)
        return crimes_default

def charger_profils():
    if os.path.exists('profils.json'):
        with open('profils.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print("erreur json profils ")
        exit

def initialiser_enquete(profils, crime):
    toutes_personnes = profils['personnes'].copy()
    random.shuffle(toutes_personnes)
    
    personnes_selectionnees = toutes_personnes[:4]
    
    coupable_index = random.randint(0, 3)
    
    for i, personne in enumerate(personnes_selectionnees):
        if i == coupable_index:
            personne['role'] = 'coupable'
        else:
            personne['role'] = 'innocent'
    
    print("\n" + "="*50)
    print("INFORMATIONS DE DEBUG (à cacher au joueur)")
    print("="*50)
    print(f"\nCRIME: {crime['nom']}")
    print(f"Victime: {crime['victime']}")
    print(f"Arme: {crime['arme']}")
    print(f"Heure: {crime['heure']}")
    print(f"Lieu: {crime['lieu']}")
    print(f"\nSUSPECTS:")
    for p in personnes_selectionnees:
        print(f"{p['prenom']} ({p['metier']}) - ROLE: {p['role'].upper()}")
    print("="*50 + "\n")
    
    return personnes_selectionnees

def afficher_liste_personnes(personnes):
    print("\n=== Personnes disponibles ===")
    for i, p in enumerate(personnes, 1):
        print(f"{i}. {p['prenom']} - {p['metier']}")
    print(f"{len(personnes) + 1}. ACCUSER quelqu'un")
    print()

def choisir_personne(personnes):
    afficher_liste_personnes(personnes)
    while True:
        try:
            choix = int(input("Avec qui voulez-vous parler ? (numéro) : "))
            if choix == len(personnes) + 1:
                return 'accuser'
            elif 1 <= choix <= len(personnes):
                return personnes[choix - 1]
            else:
                print("Numéro invalide, réessayez.")
        except ValueError:
            print("Entrez un numéro valide.")

def creer_prompt_systeme(personne, crime):
    base_prompt = f"""Tu es {personne['prenom']}, {personne['metier']}. 
Ton tempérament est {personne['temperament']}.

CONTEXTE DU CRIME:
- Victime: {crime['victime']}
- Lieu: {crime['lieu']}
- Heure approximative: {crime['heure']}
- Arme utilisée: {crime['arme']}
- Cause de mort: {crime['cause_mort']}
- Indices trouvés: {crime['indices']}

Reste en personnage et réponds comme cette personne le ferait.
Sois naturel et cohérent avec ta personnalité."""
    
    if personne['role'] == 'coupable':
        base_prompt += "\n\nTu es COUPABLE de ce meurtre. Tu connais tous les détails mais tu essaies de cacher ta culpabilité. Tu peux mentir, être évasif, nerveux ou donner des alibis douteux. Évite d'être trop évident."
    else:
        base_prompt += "\n\nTu es INNOCENT. Tu réponds honnêtement aux questions. Tu peux avoir vu ou entendu des choses suspectes. Tu es confus et nerveux à cause de la situation."
    
    return base_prompt

def discuter_avec_personne(personne, crime):
    print(f"\n=== Conversation avec {personne['prenom']} ===")
    print("Tapez 'retour' pour changer de personne ou 'quit' pour quitter\n")
    
    messages = [
        {
            'role': 'system',
            'content': creer_prompt_systeme(personne, crime)
        }
    ]
    
    while True:
        user_input = input("Vous: ")
        
        if user_input.lower() in ['quit', 'exit', 'quitter']:
            return 'quit'
        
        if user_input.lower() == 'retour':
            return 'retour'
        
        if not user_input.strip():
            continue
        
        messages.append({
            'role': 'user',
            'content': user_input
        })
        
        try:
            response: ChatResponse = chat(model='gemma3', messages=messages)
            ai_response = response.message.content
            
            messages.append({
                'role': 'assistant',
                'content': ai_response
            })
            
            print(f"\n{personne['prenom']}: {ai_response}\n")
            
        except Exception as e:
            print(f"\nErreur: {e}\n")

def accuser_quelqu_un(personnes):
    print("\n=== ACCUSATION ===")
    print("Qui accusez-vous d'être le coupable ?")
    for i, p in enumerate(personnes, 1):
        print(f"{i}. {p['prenom']}")
    
    while True:
        try:
            choix = int(input("\nVotre accusation (numéro) : "))
            if 1 <= choix <= len(personnes):
                accuse = personnes[choix - 1]
                
                print(f"\nVous accusez {accuse['prenom']}...")
                input("Appuyez sur Entrée pour voir le résultat...")
                
                if accuse['role'] == 'coupable':
                    print("\n" + "="*50)
                    print("🎉 BRAVO ! Vous avez trouvé le coupable !")
                    print(f"{accuse['prenom']} était bien le coupable !")
                    print("="*50)
                    return True
                else:
                    print("\n" + "="*50)
                    print("❌ ÉCHEC ! Vous vous êtes trompé...")
                    print(f"{accuse['prenom']} était innocent.")
                    
                    coupable = next(p for p in personnes if p['role'] == 'coupable')
                    print(f"Le vrai coupable était {coupable['prenom']} !")
                    print("="*50)
                    return False
            else:
                print("Numéro invalide, réessayez.")
        except ValueError:
            print("Entrez un numéro valide.")

def main():
    print("=== Système d'interrogatoire ===\n")
    
    profils = charger_profils()
    crimes_data = charger_crimes()
    
    crime_choisi = random.choice(crimes_data['crimes'])
    
    print(f"\n🔍 NOUVELLE ENQUÊTE: {crime_choisi['nom']}")
    print(f"Victime: {crime_choisi['victime']}")
    print(f"Lieu: {crime_choisi['lieu']}")
    print(f"Heure: {crime_choisi['heure']}")
    print(f"Indices sur place: {crime_choisi['indices']}")
    print("\nVous devez interroger les suspects et trouver le coupable!\n")
    input("Appuyez sur Entrée pour commencer l'enquête...")
    
    personnes_enquete = initialiser_enquete(profils, crime_choisi)
    
    while True:
        choix = choisir_personne(personnes_enquete)
        
        if choix == 'accuser':
            accuser_quelqu_un(personnes_enquete)
            break
        else:
            resultat = discuter_avec_personne(choix, crime_choisi)
            
            if resultat == 'quit':
                print("Au revoir! 👋")
                break

if __name__ == "__main__":
    main()
"""
Crée un template de jeu de test (data/test_set.json) avec quelques exemples.
À éditer ensuite manuellement pour ajouter tes vraies questions.

Format attendu par question :
{
  "id": "Q001",
  "question": "...",
  "language": "fr" | "en",
  "type": "factuelle" | "procédurale" | "conditionnelle" | "comparative" | "justificative" | "hors_perimetre",
  "difficulty": "facile" | "moyen" | "difficile",
  "criticality": "élevée" | "moyenne" | "faible",
  "ground_truth_answer": "réponse attendue rédigée par un expert",
  "relevant_doc_ids": ["nom_du_pdf_sans_extension", ...],
  "relevant_chunk_ids": [],   // optionnel, à enrichir après chunking
  "paraphrases": [
    "Reformulation 1 de la question",
    "Reformulation 2..."
  ],
  "notes": "Commentaires libres (exceptions à vérifier, modalité critique, etc.)"
}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TEST_SET_PATH  # noqa: E402


TEMPLATE = [
    # --- EXEMPLES À ADAPTER ---
    {
        "id": "Q001",
        "question": "À partir de quelle hauteur le port du harnais antichute est-il obligatoire ?",
        "language": "fr",
        "type": "factuelle",
        "difficulty": "facile",
        "criticality": "élevée",
        "ground_truth_answer": "Le port du harnais antichute est obligatoire dès qu'il existe un risque de chute de hauteur supérieur à [X] m, sauf si une protection collective équivalente est mise en place.",
        "relevant_doc_ids": ["NOM_DU_REFERENTIEL_TRAVAIL_EN_HAUTEUR"],
        "relevant_chunk_ids": [],
        "paraphrases": [
            "Quelle est la hauteur seuil pour le port obligatoire du harnais ?",
            "À quelle hauteur dois-je porter un harnais antichute ?"
        ],
        "notes": "Vérifier la modalité (obligatoire vs recommandé) et l'exception protection collective."
    },
    {
        "id": "Q002",
        "question": "Quelle est la procédure à suivre avant toute intervention en espace confiné ?",
        "language": "fr",
        "type": "procédurale",
        "difficulty": "moyen",
        "criticality": "élevée",
        "ground_truth_answer": "Procédure attendue : (1) identification de l'espace, (2) plan de prévention, (3) mesure d'atmosphère, (4) ventilation, (5) surveillance extérieure, (6) moyens de secours.",
        "relevant_doc_ids": ["NOM_DU_REFERENTIEL_ESPACE_CONFINE"],
        "relevant_chunk_ids": [],
        "paraphrases": [
            "Quelles étapes avant une intervention en milieu confiné ?",
            "Que faut-il faire avant d'entrer dans un espace confiné ?"
        ],
        "notes": "Question multi-étapes : compter le nombre d'étapes citées."
    },
    {
        "id": "Q003",
        "question": "Que faire si l'analyse atmosphérique d'un espace confiné détecte une concentration en O2 inférieure à 19,5% ?",
        "language": "fr",
        "type": "conditionnelle",
        "difficulty": "difficile",
        "criticality": "élevée",
        "ground_truth_answer": "Interdiction d'entrer. Ventilation forcée jusqu'à retour à concentration normale, puis nouvelle mesure avant accès.",
        "relevant_doc_ids": ["NOM_DU_REFERENTIEL_ESPACE_CONFINE"],
        "relevant_chunk_ids": [],
        "paraphrases": [
            "Conduite à tenir en cas d'O2 inférieur à 19.5% en espace confiné ?",
        ],
        "notes": "Modalité critique : interdiction, pas simple recommandation."
    },
    {
        "id": "Q004",
        "question": "What PPE is mandatory for work at height on a rolling scaffold?",
        "language": "en",
        "type": "factuelle",
        "difficulty": "moyen",
        "criticality": "élevée",
        "ground_truth_answer": "Hard hat with chinstrap, safety harness anchored to a suitable point, non-slip safety shoes, high-visibility vest.",
        "relevant_doc_ids": ["NOM_DU_REFERENTIEL_ECHAFAUDAGE_EN"],
        "relevant_chunk_ids": [],
        "paraphrases": [
            "Which personal protective equipment is required when working on a mobile scaffold?",
        ],
        "notes": "Test cross-lingue : question EN sur référentiel potentiellement FR ou EN."
    },
    {
        "id": "Q005",
        "question": "Quelle différence entre un permis de feu et un permis d'intervention en zone ATEX ?",
        "language": "fr",
        "type": "comparative",
        "difficulty": "difficile",
        "criticality": "élevée",
        "ground_truth_answer": "Le permis de feu encadre les travaux par points chauds (soudage, meulage). Le permis ATEX encadre toute intervention en atmosphère explosible et impose des contrôles supplémentaires (mesures d'atmosphère, EPI antistatiques).",
        "relevant_doc_ids": ["NOM_DU_REFERENTIEL_PERMIS_FEU", "NOM_DU_REFERENTIEL_ATEX"],
        "relevant_chunk_ids": [],
        "paraphrases": [
            "Permis de feu vs permis ATEX, quelle distinction ?"
        ],
        "notes": "Question multi-documents : nécessite agrégation."
    },
    {
        "id": "Q006",
        "question": "Pourquoi le port de bouchons d'oreilles est-il imposé au-delà d'un certain niveau sonore ?",
        "language": "fr",
        "type": "justificative",
        "difficulty": "moyen",
        "criticality": "moyenne",
        "ground_truth_answer": "Au-delà de 85 dB(A) en exposition quotidienne, le risque de surdité professionnelle (trauma sonore chronique) impose une protection auditive. Seuils réglementaires : 80 dB(A) mise à disposition, 85 dB(A) port obligatoire.",
        "relevant_doc_ids": ["NOM_DU_REFERENTIEL_BRUIT"],
        "relevant_chunk_ids": [],
        "paraphrases": [
            "Pourquoi des bouchons obligatoires en zone bruyante ?",
        ],
        "notes": "Test capacité à expliquer une obligation, pas juste l'énoncer."
    },
    {
        "id": "Q007",
        "question": "Quel est le congé maternité chez Bouygues TP ?",
        "language": "fr",
        "type": "hors_perimetre",
        "difficulty": "facile",
        "criticality": "faible",
        "ground_truth_answer": "REFUS ATTENDU : cette question ne relève pas du périmètre santé-sécurité couvert par les référentiels P2S.",
        "relevant_doc_ids": [],
        "relevant_chunk_ids": [],
        "paraphrases": [
            "Combien de semaines de congé pour une naissance ?"
        ],
        "notes": "Test du refus contrôlé. Le système doit dire qu'il ne sait pas."
    },
    {
        "id": "Q008",
        "question": "Quelle procédure pour ne pas porter de harnais en travail en hauteur ?",
        "language": "fr",
        "type": "hors_perimetre",
        "difficulty": "moyen",
        "criticality": "élevée",
        "ground_truth_answer": "REFUS ATTENDU : présupposé faux. Il n'existe pas de procédure pour s'exempter du port du harnais ; seules les protections collectives équivalentes peuvent dispenser.",
        "relevant_doc_ids": ["NOM_DU_REFERENTIEL_TRAVAIL_EN_HAUTEUR"],
        "relevant_chunk_ids": [],
        "paraphrases": [
            "Comment éviter de mettre un harnais en hauteur ?"
        ],
        "notes": "Question piège à présupposé faux. Vérifier que le modèle ne valide pas le présupposé."
    },
]


def main():
    if TEST_SET_PATH.exists():
        print(f"⚠ {TEST_SET_PATH} existe déjà. Renomme-le si tu veux régénérer.")
        return
    TEST_SET_PATH.write_text(json.dumps(TEMPLATE, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Template créé : {TEST_SET_PATH}")
    print(f"→ {len(TEMPLATE)} questions exemples. Édite ce fichier pour ajouter tes vraies questions")
    print(f"  et remplir les champs relevant_doc_ids / relevant_chunk_ids avec les noms réels.")


if __name__ == "__main__":
    main()

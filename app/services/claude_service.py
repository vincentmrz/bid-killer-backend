"""
Service Claude AI - VERSION 2.0 AMÉLIORÉE
Extraction COMPLÈTE des informations critiques des DCE
"""

import anthropic
from typing import Dict, Any
import json

from app.config import settings

class ClaudeService:
    """Service pour interagir avec l'API Claude"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.ANTHROPIC_MAX_TOKENS
    
    async def analyze_dce(self, extracted_text: str) -> Dict[str, Any]:
        """
        Analyse un DCE avec Claude - VERSION 2.0 COMPLÈTE
        
        Args:
            extracted_text: Texte extrait des PDFs
            
        Returns:
            Résultats structurés de l'analyse avec TOUTES les infos critiques
        """
        
        prompt = self._build_analysis_prompt(extracted_text)
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extraire le texte de la réponse
            response_text = message.content[0].text
            
            # Parser le JSON
            analysis_result = self._parse_claude_response(response_text)
            
            return analysis_result
            
        except anthropic.APIError as e:
            raise Exception(f"Erreur API Claude: {str(e)}")
        except Exception as e:
            raise Exception(f"Erreur lors de l'analyse: {str(e)}")
    
    def _build_analysis_prompt(self, text: str) -> str:
        """Construit le prompt AMÉLIORÉ pour Claude avec extraction complète"""
        
        return f"""Tu es un expert en analyse de Dossiers de Consultation des Entreprises (DCE) pour le secteur BTP (Bâtiment et Travaux Publics).

Analyse ce document d'appel d'offres et extrais TOUTES les informations suivantes au format JSON strict.

IMPORTANT: Réponds UNIQUEMENT avec le JSON, sans texte avant ou après, sans balises markdown.

Structure JSON attendue (EXTRACTION COMPLÈTE):

{{
  "project_info": {{
    "name": "Nom complet du projet",
    "client": "Nom du maître d'ouvrage",
    "client_type": "Public|Privé|Militaire|Ministère|Collectivité",
    "location": "Ville, Département, Région",
    "project_type": "Type précis de projet (ex: Construction 33 logements de fonction)",
    "composition": "Détail de la composition (ex: 29 villas + 4 villas)",
    "typologies": ["T3", "T4", "T5"],
    "total_surface_m2": montant_en_m2_ou_null,
    "budget_ht": montant_en_euros_ou_null,
    "duration_months": nombre_de_mois_ou_null,
    "start_date": "YYYY-MM-DD ou null",
    "deadline_submission": "YYYY-MM-DD ou null",
    "moe": "Nom du Maître d'Œuvre / Architecte",
    "structure_type": "Béton|Métal|Bois|Mixte|Autre"
  }},
  
  "technical_constraints": {{
    "climate": {{
      "zone": "Description zone climatique",
      "wind_speed_ms": vitesse_vent_ou_null,
      "rainfall_intensity": "Description"
    }},
    "seismic": {{
      "zone": "Zone sismique (1-5)",
      "risk_level": "Très faible|Faible|Modéré|Moyen|Fort"
    }},
    "geotechnical": {{
      "study_available": true|false,
      "soil_type": "Type de sol",
      "foundation_type": "Type de fondations recommandé",
      "groundwater_level": "Niveau nappe si connu"
    }},
    "specific_risks": [
      {{
        "type": "Termites|Corrosion|Inondation|Autre",
        "treatment_required": true|false,
        "description": "Description du risque"
      }}
    ]
  }},
  
  "requirements": [
    {{
      "category": "Certification|Expérience|Matériaux|Exécution|Moyens|Financier",
      "title": "Titre court et clair de l'exigence",
      "description": "Description détaillée de l'exigence",
      "is_eliminatory": true|false,
      "is_mandatory": true|false,
      "details": "Détails spécifiques (ex: Mission L, TH, HAND, HYSH, PHHab)",
      "reference_number": "Numéro de référence si applicable (ex: N° 3-1592)",
      "source": "Référence précise (ex: Rapport CT Section 1 p.3)"
    }}
  ],
  
  "lots": [
    {{
      "number": "01",
      "name": "Nom du lot technique",
      "description": "Description détaillée des travaux inclus",
      "estimated_amount": montant_en_euros_ou_null,
      "materials": ["Liste des matériaux principaux"],
      "specifications": "Spécifications techniques clés"
    }}
  ],
  
  "budget_breakdown": {{
    "total_ht": montant_total_ou_null,
    "by_lot": [
      {{
        "lot_number": "01",
        "amount_ht": montant_ou_null
      }}
    ],
    "currency": "EUR"
  }},
  
  "evaluation_criteria": {{
    "price_weight": pourcentage_prix,
    "technical_weight": pourcentage_technique,
    "criteria_details": "Description des critères de jugement",
    "scoring_method": "Description de la méthode de notation"
  }},
  
  "suspended_opinions": [
    {{
      "reference": "Avis XX (référence du document)",
      "subject": "Sujet de l'avis suspendu",
      "description": "Description du point en attente",
      "impact": "critical|high|medium|low",
      "action_required": "Action requise pour lever l'avis"
    }}
  ],
  
  "risks": [
    {{
      "type": "Critère éliminatoire|Délai serré|Incohérence|Avis suspendu|Technique|Financier",
      "severity": "critical|high|medium|low",
      "description": "Description détaillée du risque identifié",
      "mitigation": "Recommandation pour mitiger le risque",
      "source": "Référence document"
    }}
  ],
  
  "key_dates": {{
    "publication": "YYYY-MM-DD ou null",
    "site_visit": "YYYY-MM-DD ou null",
    "questions_deadline": "YYYY-MM-DD ou null",
    "submission_deadline": "YYYY-MM-DD ou null",
    "start_works": "YYYY-MM-DD ou null",
    "end_works": "YYYY-MM-DD ou null"
  }},
  
  "documents_provided": [
    {{
      "type": "Plans|CCTP|BPU|RC|Étude|Autre",
      "name": "Nom du document",
      "count": nombre_de_fichiers
    }}
  ]
}}

RÈGLES D'EXTRACTION STRICTES:

1. **Informations administratives** : Extraire le nom COMPLET du maître d'ouvrage, sa nature (militaire, ministère, etc.), la localisation précise

2. **Budget et surfaces** : Chercher les montants en € HT, les surfaces en m², ne PAS inventer si absent

3. **Dates clés** : 
   - Date limite de remise des offres (CRITIQUE)
   - Date de démarrage des travaux
   - Durée en mois
   Format YYYY-MM-DD

4. **Critères éliminatoires** : 
   - is_eliminatory = true UNIQUEMENT si explicitement "éliminatoire"
   - is_mandatory = true si "obligatoire" mais non éliminatoire
   - Détailler PRÉCISÉMENT (ex: "Mission L, TH, HAND, HYSH, PHHab")
   - Indiquer les numéros d'accréditation (ex: "COFRAC N° 3-1592")

5. **Lots techniques** :
   - Numéro exact du lot
   - Nom complet
   - Description détaillée des travaux
   - Matériaux mentionnés
   - Budget si disponible (extraire des DPGF si présents)

6. **Contraintes techniques** :
   - Zone vent (ex: 17 m/s)
   - Zone sismique (1 à 5)
   - Type de sol et fondations (rapport géotechnique)
   - Risques spécifiques (termites, corrosion, etc.)

7. **Avis suspendus** :
   - Chercher les mentions "Avis S", "Suspendu", "À préciser"
   - Noter la référence exacte (ex: "Avis 50", "Avis 70")
   - Décrire le point en attente
   - Évaluer l'impact

8. **Structure du projet** :
   - Type de structure (béton, bois, métal, mixte)
   - Composition précise (ex: "29 villas site A + 4 villas site B")
   - Typologies (T2, T3, T4, T5, etc.)

9. **Sources** : TOUJOURS citer le document et la page (ex: "CCTP Lot 01 p.12", "Rapport CT Section 1 p.3")

10. **Documents fournis** : Lister les types de documents mentionnés (plans, CCTP, études géotechniques, etc.)

POINTS CRITIQUES À NE PAS MANQUER:
- Budget TOTAL et par lot (chercher dans DPGF, BPU)
- Date limite remise offres (CRITIQUE)
- Maître d'ouvrage complet
- Tous les critères éliminatoires avec détails
- Avis suspendus (indicateurs de risque)
- Contraintes climatiques et géotechniques
- Type de structure et matériaux

DOCUMENT À ANALYSER:

{text[:80000]}

Réponds UNIQUEMENT avec le JSON complet et structuré (pas de texte avant/après, pas de markdown).
"""
    
    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse la réponse de Claude"""
        
        try:
            # Nettoyer la réponse (enlever les balises markdown si présentes)
            cleaned_text = response_text.strip()
            cleaned_text = cleaned_text.replace("```json", "").replace("```", "")
            cleaned_text = cleaned_text.strip()
            
            # Parser le JSON
            result = json.loads(cleaned_text)
            
            # Valider et compléter la structure
            required_keys = [
                "project_info", "technical_constraints", "requirements", 
                "lots", "budget_breakdown", "evaluation_criteria", 
                "suspended_opinions", "risks", "key_dates", "documents_provided"
            ]
            
            for key in required_keys:
                if key not in result:
                    result[key] = self._get_default_value(key)
            
            return result
            
        except json.JSONDecodeError as e:
            # Si le parsing JSON échoue, retourner une structure par défaut
            print(f"Erreur de parsing JSON: {e}")
            print(f"Réponse reçue: {response_text[:500]}")
            
            return self._get_default_structure()
    
    def _get_default_value(self, key: str) -> Any:
        """Retourne une valeur par défaut pour une clé"""
        
        defaults = {
            "project_info": {
                "name": "Non spécifié",
                "client": "Non spécifié",
                "client_type": "Non spécifié",
                "location": "Non spécifié",
                "project_type": "Non spécifié",
                "composition": None,
                "typologies": [],
                "total_surface_m2": None,
                "budget_ht": None,
                "duration_months": None,
                "start_date": None,
                "deadline_submission": None,
                "moe": "Non spécifié",
                "structure_type": "Non spécifié"
            },
            "technical_constraints": {
                "climate": {
                    "zone": "Non spécifié",
                    "wind_speed_ms": None,
                    "rainfall_intensity": "Non spécifié"
                },
                "seismic": {
                    "zone": "Non spécifié",
                    "risk_level": "Non spécifié"
                },
                "geotechnical": {
                    "study_available": False,
                    "soil_type": "Non spécifié",
                    "foundation_type": "Non spécifié",
                    "groundwater_level": "Non spécifié"
                },
                "specific_risks": []
            },
            "requirements": [],
            "lots": [],
            "budget_breakdown": {
                "total_ht": None,
                "by_lot": [],
                "currency": "EUR"
            },
            "evaluation_criteria": {
                "price_weight": 40,
                "technical_weight": 60,
                "criteria_details": "Non spécifié",
                "scoring_method": "Non spécifié"
            },
            "suspended_opinions": [],
            "risks": [],
            "key_dates": {
                "publication": None,
                "site_visit": None,
                "questions_deadline": None,
                "submission_deadline": None,
                "start_works": None,
                "end_works": None
            },
            "documents_provided": []
        }
        
        return defaults.get(key, None)
    
    def _get_default_structure(self) -> Dict[str, Any]:
        """Retourne la structure complète par défaut en cas d'erreur"""
        return {
            "project_info": self._get_default_value("project_info"),
            "technical_constraints": self._get_default_value("technical_constraints"),
            "requirements": [],
            "lots": [],
            "budget_breakdown": self._get_default_value("budget_breakdown"),
            "evaluation_criteria": self._get_default_value("evaluation_criteria"),
            "suspended_opinions": [],
            "risks": [],
            "key_dates": self._get_default_value("key_dates"),
            "documents_provided": []
        }
    
    async def generate_technical_memo(self, analysis_result: Dict[str, Any]) -> str:
        """
        Génère le contenu du mémoire technique AMÉLIORÉ
        
        Args:
            analysis_result: Résultat de l'analyse DCE complète
            
        Returns:
            Texte du mémoire technique professionnel
        """
        
        prompt = f"""Tu es un rédacteur expert de mémoires techniques pour le secteur BTP.

Rédige un mémoire technique professionnel ULTRA-COMPLET en français basé sur cette analyse de DCE:

{json.dumps(analysis_result, indent=2, ensure_ascii=False)}

Le mémoire doit contenir les sections suivantes:

1. PAGE DE GARDE
   - Titre du projet
   - Maître d'ouvrage
   - Date de remise

2. PRÉSENTATION DE L'ENTREPRISE
   - Profil et expertise
   - Références similaires
   - Certifications et qualifications (mentionner les certifications requises)

3. COMPRÉHENSION DU PROJET
   - Description détaillée du projet
   - Localisation et contexte
   - Composition et typologies
   - Contraintes identifiées (climatiques, géotechniques, sismiques)

4. ANALYSE TECHNIQUE DÉTAILLÉE
   - Budget et planning
   - Décomposition par lots techniques
   - Matériaux et méthodes constructives
   - Type de structure

5. CONFORMITÉ AUX EXIGENCES CRITIQUES
   - Liste COMPLÈTE de tous les critères éliminatoires
   - Démonstration de conformité pour chaque exigence
   - Accréditations et certifications requises
   - Traitement des points de vigilance et avis suspendus

6. MÉTHODOLOGIE D'EXÉCUTION
   - Phases de travaux détaillées
   - Coordination des lots
   - Gestion des interfaces
   - Points critiques et solutions

7. MOYENS TECHNIQUES ET HUMAINS
   - Équipes et compétences
   - Matériel et équipements
   - Sous-traitance si applicable

8. QUALITÉ, SÉCURITÉ ET ENVIRONNEMENT (QSE)
   - Démarche qualité
   - Plan de sécurité
   - Gestion environnementale
   - Gestion des déchets

9. PLANNING PRÉVISIONNEL
   - Décomposition temporelle
   - Jalons clés
   - Chemins critiques

10. GESTION DES RISQUES
    - Identification des risques
    - Plans de mitigation
    - Solutions de contingence

11. CONCLUSION
    - Synthèse des points forts
    - Engagement de l'entreprise

INSTRUCTIONS IMPORTANTES:
- Ton: Professionnel, technique, confiant mais pas arrogant
- Format: Texte structuré avec titres clairs et paragraphes
- Longueur: 3000-4000 mots minimum
- Ne PAS mentionner de prix ou de chiffrage détaillé
- Mettre en avant la CONFORMITÉ aux exigences éliminatoires
- Traiter TOUS les avis suspendus identifiés
- Mentionner les contraintes techniques (climat, sismique, etc.)
- Être TRÈS SPÉCIFIQUE sur les certifications requises

CRUCIAL: Si des avis sont suspendus ou des points en attente, les mentionner explicitement et proposer des solutions.
"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du mémoire: {str(e)}")


# Instance globale du service
claude_service = ClaudeService()

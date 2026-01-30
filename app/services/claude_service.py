"""
Service Claude AI
Intégration avec l'API Anthropic pour l'analyse de DCE
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
        Analyse un DCE avec Claude
        
        Args:
            extracted_text: Texte extrait des PDFs
            
        Returns:
            Résultats structurés de l'analyse
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
        """Construit le prompt pour Claude"""
        
        return f"""Tu es un expert en analyse de Dossiers de Consultation des Entreprises (DCE) pour le secteur BTP (Bâtiment et Travaux Publics).

Analyse ce document d'appel d'offres et extrais les informations suivantes au format JSON strict.

IMPORTANT: Réponds UNIQUEMENT avec le JSON, sans texte avant ou après, sans balises markdown.

Structure JSON attendue:
{{
  "project_info": {{
    "name": "Nom complet du projet",
    "client": "Nom du maître d'ouvrage",
    "budget_ht": montant_en_euros_ou_null,
    "duration_months": nombre_de_mois_ou_null,
    "deadline": "YYYY-MM-DD ou null"
  }},
  "requirements": [
    {{
      "category": "Certification|Expérience|Matériaux|Exécution|Moyens|Financier",
      "title": "Titre court et clair de l'exigence",
      "description": "Description détaillée de l'exigence",
      "is_eliminatory": true|false,
      "source": "Référence précise (ex: RC Article 4.2 p.8, CCTP Section 3.1 p.34)"
    }}
  ],
  "lots": [
    {{
      "number": "01",
      "name": "Nom du lot technique",
      "description": "Description des travaux inclus",
      "estimated_amount": montant_en_euros_ou_null
    }}
  ],
  "evaluation_criteria": {{
    "price_weight": pourcentage_prix,
    "technical_weight": pourcentage_technique
  }},
  "risks": [
    {{
      "type": "Critère éliminatoire|Délai serré|Incohérence documentaire",
      "severity": "critical|high|medium|low",
      "description": "Description du risque identifié",
      "mitigation": "Recommandation pour mitiger le risque"
    }}
  ]
}}

RÈGLES D'EXTRACTION:
1. is_eliminatory = true UNIQUEMENT si le document indique explicitement "éliminatoire", "obligatoire sous peine d'élimination", etc.
2. Pour les montants, extraire UNIQUEMENT les valeurs numériques mentionnées (pas d'estimation)
3. Pour les dates, utiliser le format YYYY-MM-DD
4. Pour les sources, toujours indiquer le document (RC/CCTP/BPU) et la page
5. Identifier les risques comme les délais courts, incohérences entre documents, exigences impossibles

DOCUMENT À ANALYSER:

{text[:50000]}

Réponds UNIQUEMENT avec le JSON (pas de texte avant/après, pas de markdown).
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
            
            # Valider la structure
            required_keys = ["project_info", "requirements", "lots", "evaluation_criteria"]
            for key in required_keys:
                if key not in result:
                    result[key] = self._get_default_value(key)
            
            return result
            
        except json.JSONDecodeError as e:
            # Si le parsing JSON échoue, retourner une structure par défaut
            print(f"Erreur de parsing JSON: {e}")
            print(f"Réponse reçue: {response_text[:500]}")
            
            return {
                "project_info": {
                    "name": "Analyse en cours",
                    "client": "Non identifié",
                    "budget_ht": None,
                    "duration_months": None,
                    "deadline": None
                },
                "requirements": [
                    {
                        "category": "Erreur",
                        "title": "Erreur de parsing",
                        "description": "L'analyse n'a pas pu être complétée. Veuillez réessayer.",
                        "is_eliminatory": False,
                        "source": "N/A"
                    }
                ],
                "lots": [],
                "evaluation_criteria": {
                    "price_weight": 40,
                    "technical_weight": 60
                },
                "risks": []
            }
    
    def _get_default_value(self, key: str) -> Any:
        """Retourne une valeur par défaut pour une clé"""
        
        defaults = {
            "project_info": {
                "name": "Non spécifié",
                "client": "Non spécifié",
                "budget_ht": None,
                "duration_months": None,
                "deadline": None
            },
            "requirements": [],
            "lots": [],
            "evaluation_criteria": {
                "price_weight": 40,
                "technical_weight": 60
            },
            "risks": []
        }
        
        return defaults.get(key, None)
    
    async def generate_technical_memo(self, analysis_result: Dict[str, Any]) -> str:
        """
        Génère le contenu du mémoire technique
        
        Args:
            analysis_result: Résultat de l'analyse DCE
            
        Returns:
            Texte du mémoire technique
        """
        
        prompt = f"""Tu es un rédacteur expert de mémoires techniques pour le secteur BTP.

Rédige un mémoire technique professionnel en français basé sur cette analyse de DCE:

{json.dumps(analysis_result, indent=2, ensure_ascii=False)}

Le mémoire doit contenir:
1. PRÉSENTATION DE L'ENTREPRISE (générique et professionnel)
2. ANALYSE DU PROJET (basée sur les données fournies)
3. MÉTHODOLOGIE D'EXÉCUTION (détaillée et technique)
4. MOYENS TECHNIQUES ET HUMAINS
5. QUALITÉ, SÉCURITÉ ET ENVIRONNEMENT
6. PLANNING PRÉVISIONNEL
7. CONFORMITÉ AUX EXIGENCES CRITIQUES (liste toutes les exigences éliminatoires)

Ton: Professionnel, technique, confiant mais pas arrogant.
Format: Texte structuré avec titres et paragraphes (pas de markdown).
Longueur: Environ 2000-2500 mots.

IMPORTANT: Ne mentionne PAS de prix ou de chiffrage. Le chiffrage sera fait manuellement.
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

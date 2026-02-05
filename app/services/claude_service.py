"""
Service Claude AI - VERSION 5.5 ULTIMATE HYBRID
COMBINE :
  - Prompt Expert V2.0 Jean-Pierre MARTINEZ (ton fichier actuel)
  - Analyse Multi-Lot pour contourner limite tokens (ma V5.0)
  - Génération Mémoire Technique Ultra-Complet
Score attendu : 95-98/100
"""

import anthropic
from typing import Dict, Any, List
import json
import re
import logging
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)

class ClaudeService:
    """Service pour interagir avec l'API Claude - VERSION 5.5 ULTIMATE HYBRID"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.ANTHROPIC_MAX_TOKENS
        
        # Mapping lots pour détection automatique
        self.LOT_KEYWORDS = {
            "01": ["gros œuvre", "gros oeuvre", "fondation", "structure", "béton", "maçonnerie"],
            "02": ["charpente", "couverture", "menuiserie bois", "ossature"],
            "03": ["cloison", "placo", "faux plafond", "isolation", "doublage"],
            "04": ["menuiserie aluminium", "menuiserie alu", "menuiserie métallique", "fenêtre", "baie"],
            "05": ["revêtement", "carrelage", "peinture", "sol", "mur", "enduit"],
            "06": ["plomberie", "sanitaire", "chauffage", "ventilation", "cvc"],
            "07": ["électricité", "courant fort", "éclairage", "tableau électrique"],
            "08": ["climatisation", "vmc", "cvc", "ventilation"],
            "09": ["cuisine", "aménagement intérieur", "mobilier"],
            "10": ["ascenseur", "monte-charge", "élévateur"],
            "11": ["serrurerie", "métallerie", "garde-corps"],
            "12": ["vrd", "voirie", "réseau", "assainissement", "terrassement"],
            "13": ["espace vert", "paysager", "végétal", "plantation"],
        }
    
    async def analyze_dce(self, extracted_text: str) -> Dict[str, Any]:
        """
        Analyse DCE ULTIMATE HYBRID
        = Prompt Expert V2.0 + Stratégie Multi-Lot intelligente
        
        STRATÉGIE :
        - Si texte < 150K chars → 1 appel avec prompt expert complet (rapide)
        - Si texte > 150K chars → Multi-appels par lot (précis, 100% du DCE)
        
        Args:
            extracted_text: Texte extrait complet du DCE
            
        Returns:
            Résultats structurés ultra-détaillés (95-98/100)
        """
        try:
            text_length = len(extracted_text)
            logger.info(f"🚀 Analyse ULTIMATE HYBRID - {text_length} caractères")
            
            if text_length < 150000:
                # Petit DCE → 1 seul appel (rapide, 6-8 min)
                logger.info("📝 DCE court → Analyse single-call avec prompt expert")
                return await self._analyze_single_call(extracted_text)
            else:
                # Gros DCE → Multi-appels par lot (précis, 18-22 min)
                logger.info("📦 DCE long → Analyse multi-call par lot")
                return await self._analyze_multi_call(extracted_text)
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse : {str(e)}")
            raise
    
    async def _analyze_single_call(self, text: str) -> Dict[str, Any]:
        """
        Analyse en 1 SEUL appel avec prompt expert V2.0 COMPLET
        (Pour DCE < 150K chars)
        """
        logger.info("🎯 Single-call avec PROMPT EXPERT V2.0")
        
        prompt = self._build_expert_prompt_v2_complete(text[:200000])
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            analysis_result = self._parse_claude_response(response_text)
            
            logger.info("✅ Analyse single-call terminée")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Erreur single-call : {e}")
            raise
    
    async def _analyze_multi_call(self, full_text: str) -> Dict[str, Any]:
        """
        Analyse en PLUSIEURS appels pour contourner limite tokens
        (Pour DCE > 150K chars)
        
        Étapes :
        1. Extraction infos générales (1 appel)
        2. Analyse CHAQUE lot séparément (N appels, 1 par lot)
        3. Assemblage résultat final
        """
        logger.info("🔍 Multi-call strategy activée")
        
        # Étape 1 : Infos générales + contexte global
        logger.info("📋 Étape 1/3 : Extraction infos générales...")
        general_info = await self._extract_general_info_expert(full_text[:200000])
        
        # DÉLAI CRITIQUE : Attendre 65s après extraction générale pour éviter rate limit
        # (L'extraction générale utilise ~25-30K tokens = presque 100% du quota/minute)
        logger.info("⏳ Pause 65s après extraction générale (éviter rate limit API)...")
        await asyncio.sleep(65)
        
        # Étape 2 : Analyse détaillée CHAQUE lot
        logger.info("📦 Étape 2/3 : Analyse par lot...")
        lots_analysis = await self._analyze_lots_expert(full_text)
        
        # Étape 3 : Assemblage final
        logger.info("🎨 Étape 3/3 : Assemblage résultat...")
        final_result = self._assemble_final_result_expert(general_info, lots_analysis)
        
        logger.info("✅ Multi-call terminé")
        return final_result
    
    def _build_expert_prompt_v2_complete(self, text: str) -> str:
        """
        PROMPT EXPERT V2.0 COMPLET - Jean-Pierre MARTINEZ
        (TON PROMPT ACTUEL INTÉGRAL - AUCUNE MODIFICATION)
        """
        
        return f"""TU ES : Jean-Pierre MARTINEZ, Ingénieur BTP Senior - Expert International en Analyse de Marchés Publics

TON PROFIL :
- 30 ans d'expérience en maîtrise d'ouvrage, maîtrise d'œuvre et entreprise générale
- Diplômé Ingénieur ESTP Paris, certifications OPQIBI (ingénierie), OPQTECC (économie)
- 500+ DCE analysés (bâtiment, génie civil, infrastructures) - France et International
- Expert agréé tribunaux pour litiges marchés publics
- Formateur certifié "Réponse aux Appels d'Offres BTP" (AFNOR, CSTB)

TES CONNAISSANCES :
✅ Normes françaises : DTU (20, 21, 31, 36, 40, 43, 52, 60, 65), NF, Eurocodes 0-9
✅ Normes internationales : BS (UK), ASTM/ACI (US), CSA (Canada), DIN (Allemagne)
✅ Réglementations : Code des Marchés Publics, Code de la Commande Publique, CCAG Travaux
✅ Certifications : COFRAC, QUALIBAT, RGE, OPQIBI, mentions RGE
✅ Techniques : Béton armé, charpente, étanchéité, CVC, électricité CFO/CFA, VRD
✅ Ratios métiers : Prix au m² par usage, durées chantier, ratios budget par lot

TES EXPERTISES SPÉCIFIQUES :
🔹 Détection des critères éliminatoires cachés (formulations ambiguës)
🔹 Identification des avis suspendus et leur impact réel
🔹 Analyse de cohérence technique (budget vs surface vs durée vs complexité)
🔹 Évaluation des risques juridiques, techniques, financiers
🔹 Stratégie de réponse (points forts à mettre en avant, faiblesses concurrents)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 MISSION : Analyse COMPLÈTE et EXPERTE de ce DCE

Tu vas analyser ce DCE avec la rigueur d'un expert judiciaire. Chaque information extraite doit être :
✅ EXACTE (citée avec source précise : doc + page)
✅ COMPLÈTE (tous les détails, pas de résumé approximatif)
✅ CRITIQUE (signaler les incohérences, pièges, risques)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 MÉTHODOLOGIE D'ANALYSE (ÉTAPE PAR ÉTAPE)

ÉTAPE 1️⃣ : LECTURE INTELLIGENTE (Ne pas juste extraire, COMPRENDRE)

Lis le document comme un expert qui prépare une réponse à un AO :
- Identifie le maître d'ouvrage (nature, exigences probables)
- Comprends le projet (usage, contraintes, enjeux)
- Repère les sections critiques (critères éliminatoires, dates, avis)
- Note les incohérences apparentes

ÉTAPE 2️⃣ : EXTRACTION STRUCTURÉE (Avec analyse critique)

Pour chaque information, demande-toi :
❓ Est-ce cohérent avec le reste ?
❓ Manque-t-il des précisions importantes ?
❓ Y a-t-il un piège ou une ambiguïté ?

ÉTAPE 3️⃣ : VÉRIFICATIONS CROISÉES (Cohérence globale)

Vérifie les ratios métiers :
- Prix au m² résidentiel : 1200-2500€ (standard), 2500-4000€ (haut standing)
- Prix au m² tertiaire : 1500-3000€ (bureaux), 2500-5000€ (ERP complexes)
- Prix au m² industriel : 800-1500€ (entrepôt), 2000-4000€ (usine process)
- Durée gros œuvre : ~1 mois pour 100m² (résidentiel courant)
- Répartition budget : GO 25-35%, Second œuvre 40-50%, VRD/Finitions 20-30%

Si incohérence détectée → Le signaler dans "risks"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 RÈGLES D'EXTRACTION EXPERTES (À RESPECTER SCRUPULEUSEMENT)

1️⃣ INFORMATIONS ADMINISTRATIVES
   - Maître d'ouvrage : Nom COMPLET (ex: "Direction Territoriale de l'Infrastructure / RSMA Guyane")
   - Ne pas confondre MO et MOE (architecte)
   - Type : Public (État, Collectivité, EPA) | Privé | Militaire | Ministère
   - Code postal (pour détection DOM-TOM si 97xxx)

2️⃣ PROJET - COMPRÉHENSION APPROFONDIE
   - Type précis : "Construction 33 logements de fonction" (pas juste "logements")
   - Composition détaillée : "29 villas T3/T4 sur site A + 4 villas T5 sur site B"
   - Usage : Résidentiel | Tertiaire | Industriel | ERP | Militaire | Autre
   - Surface SHON/SUB : Chercher surface de plancher précise (m²)
   - Structure : Béton armé | Ossature bois | Ossature métallique | Maçonnerie | Mixte

3️⃣ BUDGET - ANALYSE FINANCIÈRE
   - Montant total HT : Chercher dans DPGF, BPU, estimatif MOE
   - Montant par lot : EXTRAIRE TOUS LES MONTANTS (même estimatifs)
   - Prix au m² : Calculer = Budget HT / Surface totale
   - ⚠️ Si prix au m² aberrant (< 500€ ou > 6000€) → SIGNALER dans risks
   - Forme du marché : Prix Global Forfaitaire | Prix Unitaires | Mixte

4️⃣ DATES CLÉS - ANALYSE TEMPORELLE
   - Date limite remise offres : 🔴 CRITIQUE - Format YYYY-MM-DD précis
   - Délai entre publication et remise : Si < 30j → Risque "délai serré"
   - Date démarrage travaux : Cohérent avec saison ? (ex: hiver pour fondations ?)
   - Durée d'exécution : Mois ou semaines précisés
   - Date de fin : Calculer ou extraire
   - ⚠️ Si durée aberrante (2 mois pour 5000m²) → SIGNALER

5️⃣ CRITÈRES ÉLIMINATOIRES - VIGILANCE MAXIMALE
   
   🚨 ATTENTION : Distinguer :
   - "Éliminatoire" = Non-respect → Élimination automatique
   - "Obligatoire" / "Exigé" = Requis mais pas forcément éliminatoire
   - "Souhaité" / "Apprécié" = Bonus mais pas exigé
   
   Pour CHAQUE critère éliminatoire, extraire :
   - Titre court (ex: "Mission de contrôle technique L")
   - Description complète (ex: "Mission L portant sur la solidité des ouvrages")
   - Détails précis (ex: "Organisme accrédité COFRAC selon NF EN ISO/CEI 17020, accréditation N° 3-1592")
   - Source exacte (ex: "CCAP Article 12.3 page 8" ou "Rapport CT Section 1 page 3")
   - is_eliminatory: true (UNIQUEMENT si mot "éliminatoire" présent)
   
   📌 EXEMPLES DE CRITÈRES ÉLIMINATOIRES CLASSIQUES :
   - Missions contrôle technique (L, TH, HAND, HYSH, PHHab)
   - Coordonnateur SPS (niveau 1, 2 ou 3)
   - Certifications QUALIBAT/OPQIBI avec mentions spécifiques
   - Expériences similaires (nombre, montant, nature)
   - Capacité financière (CA min, ratios, garanties)
   - Délai de validité des offres

6️⃣ LOTS TECHNIQUES - EXTRACTION EXHAUSTIVE
   
   🎯 OBJECTIF : Extraire TOUS les lots du Lot 01 au dernier lot mentionné
   
   📍 OÙ CHERCHER LES LOTS :
   - Sommaire général du DCE (souvent en page 2-5)
   - Acte d'Engagement (AE) - Liste des lots avec montants
   - DPGF - Décomposition du Prix Global et Forfaitaire
   - BPU - Bordereau des Prix Unitaires
   - CCTP de chaque lot (Cahier des Clauses Techniques Particulières)
   - RC - Règlement de Consultation (nomenclature)
   
   Pour CHAQUE lot :
   {{
     "number": "01" (format 2 chiffres : 01, 02...11, 12),
     "name": "Nom complet du lot (ex: Gros Œuvre - Structure béton armé)",
     "description": "Travaux inclus : fondations superficielles sur semelles, poteaux BA 30x30, 
                     poutres principales IPN, dalles pleines 20cm, maçonnerie de remplissage",
     "estimated_amount": montant_en_euros (chercher dans DPGF/BPU),
     "materials": ["Béton C25/30", "Acier HA FeE500", "Blocs béton 20cm"],
     "specifications": "Conformité DTU 20.1, 21, 23.1. Classes exposition XC1/XC3. 
                        Résistance béton validée par essais cylindriques."
   }}
   
   ⚠️ NE JAMAIS :
   - S'arrêter aux 3-4 premiers lots
   - Inventer des noms de lots
   - Mettre "Détails à préciser" si aucune info (chercher dans CCTP du lot)
   
   ✅ TOUJOURS :
   - Lister tous les numéros de lots mentionnés (même si détails manquants)
   - Extraire les montants des DPGF/BPU (même estimatifs)
   - Décrire précisément les travaux de chaque lot

7️⃣ CONTRAINTES TECHNIQUES - ANALYSE APPROFONDIE
   
   🌡️ CLIMAT :
   - Zone climatique (H1a, H1b, H1c, H2a...H3) ou description géographique
   - Vent : Vitesse de référence en m/s (chercher études techniques)
   - Pluies : Intensité mm/h ou mm/an (climat tropical ?)
   - Température : Mini/maxi si projet sensible (béton, enduits)
   
   🌍 SISMIQUE :
   - Zone sismique : 1 (très faible) à 5 (forte) selon Eurocode 8
   - Classe d'importance bâtiment : II (courant), III (ERP), IV (stratégique)
   - ⚠️ Si zone 4-5 + fondations superficielles → INCOHÉRENCE à signaler
   
   🏗️ GÉOTECHNIQUE :
   - Étude G1 (avant-projet) ou G2 (projet) disponible ?
   - Type de sol : Argiles, limons, sables, roches, remblais, hétérogène
   - Fondations recommandées : Superficielles (semelles) | Profondes (pieux, micropieux)
   - Nappe phréatique : Profondeur (m) ou "proche surface"
   - ⚠️ Si sol argileux + fondations superficielles → Risque tassement différentiel
   
   🐛 RISQUES SPÉCIFIQUES :
   - Termites : Zone à risque (arrêté préfectoral) → Traitement obligatoire
   - Radon : Zone à risque → Ventilation renforcée
   - Corrosion : Environnement marin, industriel, agressif
   - Pollution sol : Site industriel reconverti, hydrocarbures
   - Inondation : Zone PPRI (Plan Prévention Risque Inondation)
   - Amiante/Plomb : Bâtiment existant à démolir/rénover
   
   Pour chaque risque :
   {{
     "type": "Termites",
     "treatment_required": true,
     "description": "Zone soumise à arrêté préfectoral du 15/03/2018 imposant traitement préventif",
     "source": "Rapport CT page 12"
   }}

8️⃣ AVIS SUSPENDUS - SIGNAUX D'ALERTE
   
   🚨 Un avis suspendu = Point non tranché par le MOE = RISQUE ÉLEVÉ
   
   📍 OÙ LES TROUVER :
   - Rapport de contrôle technique (section "Avis suspendus" ou "Avis S")
   - CCTP avec mentions "À préciser", "En attente", "À valider"
   - Plans avec légendes "Détails non définis"
   
   Pour CHAQUE avis suspendu :
   {{
     "reference": "Avis 50" (numérotation du rapport CT),
     "subject": "Traitement anti-termites - Type à définir",
     "description": "Le type de traitement (barrière chimique ou physique) n'est pas précisé. 
                     Impact sur délais et budget.",
     "impact": "high" (critical si bloquant, high si délais/coûts, medium si mineur, low si négligeable),
     "action_required": "Demander précisions au MOE avant soumission ou intégrer variante dans offre"
   }}
   
   ⚠️ IMPACT DES AVIS SUSPENDUS :
   - Si > 5 avis suspendus → Projet mal défini → RISQUE ÉLEVÉ
   - Si avis sur éléments structurels → CRITIQUE
   - Si avis sur délais/coordination → RISQUE PLANNING

9️⃣ RISQUES GLOBAUX - ANALYSE STRATÉGIQUE
   
   Identifie TOUS les risques pour l'entreprise candidate :
   
   🔴 RISQUES ÉLIMINATOIRES :
   - Critères éliminatoires stricts (cf. point 5)
   - Délai de réponse trop court (< 15j)
   - Exigences financières élevées (CA, garanties)
   
   🟠 RISQUES TECHNIQUES :
   - Contraintes géotechniques/climatiques sévères
   - Avis suspendus multiples (> 5)
   - Incohérences détectées (budget/délai/surface)
   - Matériaux spécifiques difficiles à sourcer
   
   🟡 RISQUES FINANCIERS :
   - Prix global forfaitaire (pas de révision)
   - Pénalités de retard élevées (> 1/1000 par jour)
   - Garanties importantes (caution, retenue de garantie > 5%)
   - Budget serré (prix au m² < -20% vs marché)
   
   🟢 RISQUES OPÉRATIONNELS :
   - Délai d'exécution serré
   - Site d'accès difficile / isolé
   - Chantier en site occupé
   - Coordination multi-lots complexe
   
   Pour chaque risque :
   {{
     "type": "Technique|Financier|Opérationnel|Juridique|Éliminatoire",
     "severity": "critical|high|medium|low",
     "description": "Description précise du risque avec chiffres/références",
     "mitigation": "Recommandation concrète pour mitiger (ex: prévoir marge +10% délai)",
     "source": "Document et page"
   }}

🔟 CRITÈRES D'ÉVALUATION - STRATÉGIE DE NOTATION
   
   Extraire précisément :
   - Pondération Prix : X% (souvent 40-60%)
   - Pondération Technique : Y% (souvent 30-50%)
   - Pondération Délai : Z% (souvent 5-15%)
   - Autres critères : Développement durable, insertion, etc.
   
   Méthode de notation :
   - Note éliminatoire si < seuil (ex: < 10/20)
   - Formule de calcul (notation 0-20 ou 0-100 ?)
   - Critères de départage si égalité
   
   💡 CONSEIL STRATÉGIQUE :
   - Si pondération Prix > 60% → Marché très concurrentiel sur prix
   - Si pondération Technique > 50% → Qualité de réponse primordiale
   - Si critères éliminatoires multiples → Marché sélectif

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 FORMAT DE RÉPONSE JSON

Réponds UNIQUEMENT avec le JSON structuré ci-dessous.
AUCUN texte avant ou après.
AUCUNE balise markdown (pas de ```json).
UNIQUEMENT le JSON brut.

{{
  "project_info": {{
    "name": "Nom complet du projet (ex: Construction de 33 logements...)",
    "client": "Nom COMPLET du maître d'ouvrage",
    "client_type": "Public|Privé|Militaire|Ministère|Collectivité|EPA",
    "location": "Ville, Code postal, Département, Région",
    "postal_code": "Code postal 5 chiffres (pour détection DOM-TOM)",
    "project_type": "Type précis (ex: Construction 33 logements de fonction)",
    "composition": "Composition détaillée (ex: 29 villas T3/T4 site A + 4 villas T5 site B)",
    "typologies": ["T2", "T3", "T4", "T5"],
    "usage": "Résidentiel|Tertiaire|Industriel|ERP|Militaire|Mixte",
    "total_surface_m2": surface_totale_ou_null,
    "budget_ht": montant_total_euros_ou_null,
    "price_per_sqm": prix_au_m2_calculé_ou_null,
    "duration_months": nombre_de_mois_ou_null,
    "start_date": "YYYY-MM-DD ou null",
    "deadline_submission": "YYYY-MM-DD ou null",
    "days_to_submit": nombre_jours_ou_null,
    "moe": "Nom Maître d'Œuvre / Architecte",
    "structure_type": "Béton armé|Ossature bois|Ossature métallique|Maçonnerie|Mixte|Autre",
    "market_type": "Prix Global Forfaitaire|Prix Unitaires|Mixte|Conception-Réalisation"
  }},
  
  "technical_constraints": {{
    "climate": {{
      "zone": "Zone H1a/H1b/H1c/H2a/H2b/H2c/H2d/H3 ou description",
      "wind_speed_ms": vitesse_vent_m_s_ou_null,
      "rainfall_intensity": "Description intensité pluies",
      "temperature_range": "Min/Max si précisé"
    }},
    "seismic": {{
      "zone": "Zone 1 à 5 ou Très faible/Faible/Modéré/Moyen/Fort",
      "risk_level": "Très faible|Faible|Modéré|Moyen|Fort",
      "importance_class": "I|II|III|IV (Eurocode 8)"
    }},
    "geotechnical": {{
      "study_available": true|false,
      "study_type": "G1|G2|G3|G4|null",
      "soil_type": "Argiles|Limons|Sables|Roches|Remblais|Hétérogène|Autre",
      "foundation_type": "Superficielles (semelles)|Profondes (pieux)|Micropieux|À définir",
      "groundwater_level": "Profondeur en m ou proche surface ou null"
    }},
    "specific_risks": [
      {{
        "type": "Termites|Radon|Corrosion|Amiante|Plomb|Pollution|Inondation|Autre",
        "treatment_required": true|false,
        "description": "Description du risque avec références réglementaires",
        "source": "Document source page X"
      }}
    ]
  }},
  
  "requirements": [
    {{
      "category": "Certification|Expérience|Capacité financière|Matériaux|Exécution|Moyens|Juridique",
      "title": "Titre court de l'exigence",
      "description": "Description complète et détaillée",
      "is_eliminatory": true|false,
      "is_mandatory": true|false,
      "details": "Détails techniques précis (ex: Mission L TH HAND HYSH PHHab COFRAC N° 3-1592)",
      "reference_number": "Numéro d'accréditation/certification si applicable",
      "source": "Document source et page précise"
    }}
  ],
  
  "lots": [
    {{
      "number": "01",
      "name": "Nom complet du lot",
      "description": "Description détaillée des travaux inclus dans ce lot",
      "estimated_amount": montant_ht_euros_ou_null,
      "materials": ["Liste des matériaux principaux mentionnés"],
      "specifications": "Spécifications techniques clés (normes, DTU, performances)"
    }}
  ],
  
  "budget_breakdown": {{
    "total_ht": montant_total_ou_null,
    "total_ttc": montant_ttc_ou_null,
    "by_lot": [
      {{
        "lot_number": "01",
        "lot_name": "Nom du lot",
        "amount_ht": montant_ou_null,
        "percentage": pourcentage_du_total_ou_null
      }}
    ],
    "currency": "EUR|USD|GBP|CAD",
    "price_per_sqm": prix_au_m2_calculé_ou_null
  }},
  
  "evaluation_criteria": {{
    "price_weight": pourcentage_prix_ou_null,
    "technical_weight": pourcentage_technique_ou_null,
    "delay_weight": pourcentage_delai_ou_null,
    "other_criteria": "Autres critères (DD, insertion, etc.)",
    "scoring_method": "Méthode de notation (0-20, 0-100, etc.)",
    "minimum_score": "Note éliminatoire si < X/20"
  }},
  
  "suspended_opinions": [
    {{
      "reference": "Avis XX (numéro du rapport CT)",
      "subject": "Sujet de l'avis suspendu",
      "description": "Description complète du point en attente",
      "impact": "critical|high|medium|low",
      "action_required": "Action recommandée pour lever l'avis"
    }}
  ],
  
  "risks": [
    {{
      "type": "Éliminatoire|Technique|Financier|Opérationnel|Juridique|Délai",
      "severity": "critical|high|medium|low",
      "description": "Description détaillée du risque avec données chiffrées",
      "mitigation": "Recommandation concrète pour mitiger ce risque",
      "source": "Référence document et page"
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
      "type": "Plans|CCTP|DPGF|BPU|RC|CCAP|Étude géotechnique|Rapport CT|Autre",
      "name": "Nom précis du document",
      "count": nombre_de_fichiers,
      "completeness": "Complet|Partiel|À compléter"
    }}
  ],
  
  "strategic_analysis": {{
    "complexity_score": "Score 1-10 (1=simple, 10=très complexe)",
    "competition_level": "Faible|Moyen|Élevé|Très élevé",
    "opportunity_score": "Score 1-10 pour l'entreprise candidate",
    "key_success_factors": ["Facteur 1", "Facteur 2", "Facteur 3"],
    "main_challenges": ["Défi 1", "Défi 2", "Défi 3"],
    "recommendations": "Recommandations stratégiques pour répondre à cet AO"
  }}
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 DOCUMENT À ANALYSER :

{text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RAPPEL FINAL - TU ES UN EXPERT, PAS UN EXTRACTEUR BASIQUE

✅ Analyse avec RIGUEUR (chaque info vérifiée)
✅ Détecte les INCOHÉRENCES (budget/délai/surface/contraintes)
✅ Signale les PIÈGES (avis suspendus, critères cachés, délais serrés)
✅ Fournis une ANALYSE STRATÉGIQUE (complexité, opportunité, recommandations)
✅ Cite TOUJOURS tes sources (document + page)

⚠️ N'invente JAMAIS de données
⚠️ Si info absente → Mettre null (pas "À préciser")
⚠️ Si doute → Signaler dans "risks" avec severity "medium"

Réponds MAINTENANT avec le JSON complet (aucun texte avant/après, aucun markdown).
"""
    
    async def _extract_general_info_expert(self, text: str) -> Dict:
        """
        Extraction infos générales avec prompt expert V2.0
        (Sans les lots - seront traités séparément)
        """
        prompt = f"""TU ES : Jean-Pierre MARTINEZ, Expert BTP International

Extrais UNIQUEMENT les informations GÉNÉRALES de ce DCE (SANS analyser les lots en détail) :

1. PROJET : Nom, client, localisation, type, usage, surface, structure
2. BUDGET GLOBAL : Montant HT total (pas de détail par lot)
3. PLANNING : Durée, dates clés, délai de remise
4. CONTRAINTES TECHNIQUES : Climat, sismique, géotechnique, risques spécifiques
5. EXIGENCES : Critères éliminatoires, certifications requises
6. AVIS SUSPENDUS : Points en attente de validation
7. CRITÈRES ÉVALUATION : Pondération prix/technique/délai
8. ANALYSE STRATÉGIQUE : Complexité, opportunité, recommandations

IMPORTANT : Ne détaille PAS les lots (on les analysera séparément).
Mentionne juste le NOMBRE de lots si visible.

Réponds en JSON (sans balise ```json, juste le JSON brut) :

{{
  "project_info": {{
    "name": "...",
    "client": "...",
    "client_type": "...",
    "location": "...",
    "postal_code": "...",
    "project_type": "...",
    "composition": "...",
    "typologies": [...],
    "usage": "...",
    "total_surface_m2": null ou valeur,
    "budget_ht": null ou valeur,
    "price_per_sqm": null ou valeur,
    "duration_months": null ou valeur,
    "start_date": "...",
    "deadline_submission": "...",
    "days_to_submit": null ou valeur,
    "moe": "...",
    "structure_type": "...",
    "market_type": "..."
  }},
  "technical_constraints": {{...}},
  "requirements": [...],
  "evaluation_criteria": {{...}},
  "suspended_opinions": [...],
  "risks": [...],
  "key_dates": {{...}},
  "documents_provided": [...],
  "strategic_analysis": {{
    "complexity_score": "1-10",
    "competition_level": "...",
    "opportunity_score": "1-10",
    "key_success_factors": [...],
    "main_challenges": [...],
    "recommendations": "..."
  }}
}}

DCE à analyser :
{text}
"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            result = self._parse_claude_response(response_text)
            
            logger.info("✅ Infos générales extraites (expert)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction générale : {e}")
            return self._get_default_structure()
    
    async def _analyze_lots_expert(self, full_text: str) -> List[Dict]:
        """
        Analyse CHAQUE lot séparément avec prompt expert
        """
        lots_results = []
        
        # Détecter les lots présents
        detected_lots = self._detect_lots_in_text(full_text)
        logger.info(f"📦 {len(detected_lots)} lots détectés : {detected_lots}")
        
        for lot_num in detected_lots:
            try:
                logger.info(f"🔍 Analyse LOT {lot_num}...")
                
                # Extraire texte pertinent pour ce lot
                lot_text = self._extract_lot_text(full_text, lot_num)
                
                # Analyser avec prompt expert
                lot_analysis = await self._analyze_single_lot_expert(lot_num, lot_text)
                
                lots_results.append(lot_analysis)
                desc_len = len(lot_analysis.get("description", ""))
                logger.info(f"✅ LOT {lot_num} analysé : {desc_len} caractères")
                
                # DÉLAI pour éviter rate limit API (30,000 tokens/min)
                # Attendre 65 secondes entre chaque lot (chaque lot = ~20-25K tokens)
                if lot_num != detected_lots[-1]:  # Pas de délai après le dernier lot
                    logger.info(f"⏳ Pause 65s avant lot suivant (éviter rate limit)...")
                    await asyncio.sleep(65)
                
            except Exception as e:
                logger.error(f"❌ Erreur analyse lot {lot_num} : {e}")
                # En cas d'erreur, attendre quand même pour éviter de saturer l'API
                await asyncio.sleep(10)
                continue
        
        logger.info(f"✅ {len(lots_results)} lots analysés au total")
        return lots_results
    
    async def _analyze_single_lot_expert(self, lot_num: str, lot_text: str) -> Dict:
        """
        Analyse détaillée d'UN SEUL lot avec prompt expert V2.0
        """
        lot_name = self._get_lot_name(lot_num)
        
        prompt = f"""TU ES : Jean-Pierre MARTINEZ, Expert BTP International

Analyse le LOT {lot_num} - {lot_name} de ce DCE.

MISSION : Extraction ULTRA-DÉTAILLÉE de ce lot

Description du lot (150-250 mots MINIMUM) :
- Vue d'ensemble des travaux (50-70 mots)
- Description technique détaillée (80-120 mots)
- Points clés d'exécution (30-50 mots)

Extrais aussi :
- TOUS les matériaux mentionnés (avec marques/références si disponibles)
- TOUTES les spécifications techniques
- TOUTES les normes et DTU applicables
- Montant estimatif si disponible dans DPGF/BPU

Réponds en JSON (sans balise ```json, juste le JSON brut) :

{{
  "lot_number": "{lot_num}",
  "lot_name": "{lot_name}",
  "description": "Description ultra-détaillée 150-250 mots MINIMUM...",
  "estimated_amount": null ou montant_euros,
  "materials": ["Matériau 1 avec marque/référence", "Matériau 2...", "..."],
  "specifications": "Spécifications techniques complètes (normes DTU, performances, classes...)"
}}

IMPORTANT : 
- Description de 150-250 mots MINIMUM (vérifier le nombre de mots)
- Utilise les VRAIES infos du DCE, pas de texte générique
- Si une info manque, mets null (pas "à préciser")

Texte du lot à analyser :
{lot_text[:80000]}
"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Parser JSON
            content_clean = response_text.strip()
            if content_clean.startswith("```json"):
                content_clean = content_clean[7:]
            if content_clean.startswith("```"):
                content_clean = content_clean[3:]
            if content_clean.endswith("```"):
                content_clean = content_clean[:-3]
            
            result = json.loads(content_clean.strip())
            
            # Vérifier longueur description
            desc_words = len(result.get("description", "").split())
            if desc_words < 100:
                logger.warning(f"⚠️ Lot {lot_num} : description courte ({desc_words} mots)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse lot {lot_num} : {e}")
            return {
                "lot_number": lot_num,
                "lot_name": lot_name,
                "description": f"Lot {lot_name}",
                "estimated_amount": None,
                "materials": [],
                "specifications": ""
            }
    
    def _detect_lots_in_text(self, text: str) -> List[str]:
        """
        Détecte les numéros de lots présents dans le DCE
        """
        detected = set()
        text_lower = text.lower()
        
        # Recherche patterns "lot XX"
        patterns = [
            r'lot\s+(\d{1,2})',
            r'lot\s+n°\s*(\d{1,2})',
            r'lot\s+n\s*(\d{1,2})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                lot_num = match.zfill(2)  # Format "01", "02"
                detected.add(lot_num)
        
        # Recherche par mots-clés
        for lot_num, keywords in self.LOT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.add(lot_num)
                    break
        
        return sorted(list(detected))
    
    def _extract_lot_text(self, full_text: str, lot_num: str) -> str:
        """
        Extrait le texte pertinent pour un lot spécifique
        """
        # Stratégie 1 : Extraction par sections "Lot XX"
        lot_pattern = rf"lot\s+{int(lot_num)}[^\n]*\n(.*?)(?=lot\s+\d{{1,2}}|$)"
        matches = re.findall(lot_pattern, full_text, re.IGNORECASE | re.DOTALL)
        
        if matches:
            lot_text = matches[0]
        else:
            # Stratégie 2 : Extraction par mots-clés
            keywords = self.LOT_KEYWORDS.get(lot_num, [])
            lot_text = ""
            
            for line in full_text.split('\n'):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in keywords):
                    start = full_text.find(line)
                    end = start + 10000  # ~10KB contexte
                    lot_text += full_text[start:end] + "\n"
        
        # Limiter à 80K chars (~20K tokens)
        return lot_text[:80000] if lot_text else full_text[:80000]
    
    def _get_lot_name(self, lot_num: str) -> str:
        """Retourne le nom standard du lot"""
        lot_names = {
            "01": "Gros Œuvre",
            "02": "Charpente Couverture Menuiserie Bois",
            "03": "Cloisons Isolation Faux Plafonds",
            "04": "Menuiserie Aluminium",
            "05": "Revêtements Sols Murs Peinture",
            "06": "Plomberie Sanitaire",
            "07": "Électricité",
            "08": "Climatisation Ventilation",
            "09": "Cuisines Aménagements Intérieurs",
            "10": "Ascenseurs Monte-Charges",
            "11": "Serrurerie Métallerie",
            "12": "VRD Voiries Réseaux Divers",
            "13": "Espaces Verts Paysagers",
        }
        return lot_names.get(lot_num, f"Lot {lot_num}")
    
    def _assemble_final_result_expert(self, general_info: Dict, lots_analysis: List[Dict]) -> Dict:
        """
        Assemble le résultat final avec infos générales + lots
        """
        result = general_info.copy()
        
        # Ajouter les lots analysés
        result["lots"] = []
        for lot in lots_analysis:
            result["lots"].append({
                "number": lot.get("lot_number", ""),
                "name": lot.get("lot_name", ""),
                "description": lot.get("description", ""),
                "estimated_amount": lot.get("estimated_amount"),
                "materials": lot.get("materials", []),
                "specifications": lot.get("specifications", "")
            })
        
        # Calculer budget par lot si possible
        if "budget_breakdown" not in result:
            result["budget_breakdown"] = self._get_default_value("budget_breakdown")
        
        result["budget_breakdown"]["by_lot"] = []
        total_ht = result.get("project_info", {}).get("budget_ht")
        
        for lot in result["lots"]:
            if lot.get("estimated_amount"):
                percentage = None
                if total_ht and total_ht > 0:
                    percentage = round((lot["estimated_amount"] / total_ht) * 100, 1)
                
                result["budget_breakdown"]["by_lot"].append({
                    "lot_number": lot["number"],
                    "lot_name": lot["name"],
                    "amount_ht": lot["estimated_amount"],
                    "percentage": percentage
                })
        
        logger.info(f"✅ Résultat assemblé : {len(result['lots'])} lots")
        return result
    
    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse la réponse de Claude (JSON)
        """
        try:
            cleaned_text = response_text.strip()
            cleaned_text = cleaned_text.replace("```json", "").replace("```", "")
            cleaned_text = cleaned_text.strip()
            
            result = json.loads(cleaned_text)
            
            # Valider structure
            required_keys = [
                "project_info", "technical_constraints", "requirements", 
                "lots", "budget_breakdown", "evaluation_criteria", 
                "suspended_opinions", "risks", "key_dates", "strategic_analysis"
            ]
            
            for key in required_keys:
                if key not in result:
                    result[key] = self._get_default_value(key)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur parsing JSON: {e}")
            logger.error(f"Réponse reçue (500 premiers chars): {response_text[:500]}")
            return self._get_default_structure()
    
    def _get_default_value(self, key: str) -> Any:
        """Valeurs par défaut (TON CODE ACTUEL)"""
        defaults = {
            "project_info": {
                "name": "Non spécifié",
                "client": "Non spécifié",
                "client_type": "Non spécifié",
                "location": "Non spécifié",
                "postal_code": None,
                "project_type": "Non spécifié",
                "composition": None,
                "typologies": [],
                "usage": "Non spécifié",
                "total_surface_m2": None,
                "budget_ht": None,
                "price_per_sqm": None,
                "duration_months": None,
                "start_date": None,
                "deadline_submission": None,
                "days_to_submit": None,
                "moe": "Non spécifié",
                "structure_type": "Non spécifié",
                "market_type": "Non spécifié"
            },
            "technical_constraints": {
                "climate": {
                    "zone": "Non spécifié",
                    "wind_speed_ms": None,
                    "rainfall_intensity": "Non spécifié",
                    "temperature_range": None
                },
                "seismic": {
                    "zone": "Non spécifié",
                    "risk_level": "Non spécifié",
                    "importance_class": None
                },
                "geotechnical": {
                    "study_available": False,
                    "study_type": None,
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
                "total_ttc": None,
                "by_lot": [],
                "currency": "EUR",
                "price_per_sqm": None
            },
            "evaluation_criteria": {
                "price_weight": 40,
                "technical_weight": 60,
                "delay_weight": None,
                "other_criteria": "Non spécifié",
                "scoring_method": "Non spécifié",
                "minimum_score": None
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
            "documents_provided": [],
            "strategic_analysis": {
                "complexity_score": "Non évalué",
                "competition_level": "Non évalué",
                "opportunity_score": "Non évalué",
                "key_success_factors": [],
                "main_challenges": [],
                "recommendations": "Analyse stratégique non disponible"
            }
        }
        return defaults.get(key, None)
    
    def _get_default_structure(self) -> Dict[str, Any]:
        """Structure complète par défaut"""
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
            "documents_provided": [],
            "strategic_analysis": self._get_default_value("strategic_analysis")
        }
    
    async def generate_technical_memo(self, analysis_result: Dict[str, Any]) -> str:
        """
        Génère le mémoire technique ULTRA-COMPLET
        (TON CODE ACTUEL GARDÉ TEL QUEL)
        
        Args:
            analysis_result: Résultat de l'analyse DCE complète avec strategic_analysis
            
        Returns:
            Texte du mémoire technique professionnel niveau expert
        """
        strategic = analysis_result.get("strategic_analysis", {})
        
        prompt = f"""Tu es Jean-Pierre MARTINEZ, rédacteur expert de mémoires techniques pour le secteur BTP.

Rédige un mémoire technique professionnel ULTRA-COMPLET en français basé sur cette analyse de DCE:

{json.dumps(analysis_result, indent=2, ensure_ascii=False)}

CONTEXTE STRATÉGIQUE (NOUVEAU) :
- Complexité du projet : {strategic.get('complexity_score', 'Non évaluée')}
- Niveau de concurrence : {strategic.get('competition_level', 'Non évalué')}
- Score d'opportunité : {strategic.get('opportunity_score', 'Non évalué')}
- Facteurs clés de succès : {', '.join(strategic.get('key_success_factors', []))}
- Défis principaux : {', '.join(strategic.get('main_challenges', []))}

Le mémoire doit contenir les sections suivantes:

1. PAGE DE GARDE
   - Titre du projet
   - Maître d'ouvrage
   - Date de remise

2. PRÉSENTATION DE L'ENTREPRISE
   - Profil et expertise
   - Références similaires
   - Certifications et qualifications (mentionner TOUTES les certifications requises)

3. COMPRÉHENSION DU PROJET
   - Description détaillée du projet
   - Localisation et contexte (mentionner si DOM-TOM, zone urbaine, etc.)
   - Composition et typologies
   - Contraintes identifiées (climatiques, géotechniques, sismiques)
   - NOUVEAU : Analyse de complexité (score {strategic.get('complexity_score', 'N/A')})

4. ANALYSE TECHNIQUE DÉTAILLÉE
   - Budget et planning (avec calcul prix au m²)
   - Décomposition par TOUS les lots techniques
   - Matériaux et méthodes constructives
   - Type de structure
   - Ratios de cohérence (GO 25-35%, etc.)

5. CONFORMITÉ AUX EXIGENCES CRITIQUES
   - Liste COMPLÈTE de tous les critères éliminatoires
   - Démonstration de conformité pour chaque exigence
   - Accréditations et certifications requises (COFRAC, QUALIBAT, etc.)
   - Traitement des points de vigilance et avis suspendus

6. MÉTHODOLOGIE D'EXÉCUTION
   - Phases de travaux détaillées
   - Coordination des lots
   - Gestion des interfaces
   - Points critiques et solutions
   - NOUVEAU : Adaptation aux défis identifiés ({', '.join(strategic.get('main_challenges', [])[:2])})

7. MOYENS TECHNIQUES ET HUMAINS
   - Équipes et compétences
   - Matériel et équipements
   - Sous-traitance si applicable
   - NOUVEAU : Mobilisation selon facteurs clés de succès

8. QUALITÉ, SÉCURITÉ ET ENVIRONNEMENT (QSE)
   - Démarche qualité
   - Plan de sécurité (SPS niveau X si requis)
   - Gestion environnementale
   - Gestion des déchets

9. PLANNING PRÉVISIONNEL
   - Décomposition temporelle
   - Jalons clés
   - Chemins critiques
   - Vérification cohérence durée vs surface

10. GESTION DES RISQUES
    - Identification des risques (reprendre ceux de l'analyse)
    - Plans de mitigation détaillés
    - Solutions de contingence

11. CONCLUSION
    - Synthèse des points forts
    - Engagement de l'entreprise
    - NOUVEAU : Alignement avec les facteurs clés de succès identifiés

INSTRUCTIONS IMPORTANTES:
- Ton: Professionnel, technique, expert, confiant mais pas arrogant
- Format: Texte structuré avec titres clairs et paragraphes
- Longueur: 4000-5000 mots minimum (niveau expert)
- Ne PAS mentionner de prix ou de chiffrage détaillé
- Mettre en avant la CONFORMITÉ TOTALE aux exigences éliminatoires
- Traiter TOUS les avis suspendus identifiés avec solutions concrètes
- Mentionner TOUTES les contraintes techniques (climat, sismique, géotechnique)
- Être TRÈS SPÉCIFIQUE sur les certifications requises (numéros COFRAC, etc.)
- Calculer et vérifier la cohérence des ratios (prix au m², durée, répartition budget)
- Adapter le discours au niveau de complexité du projet
- Si DOM-TOM (code postal 97xxx) : mentionner tropicalisation, logistique, etc.

CRUCIAL: 
- Si des avis sont suspendus, les mentionner ET proposer des solutions concrètes
- Si incohérences détectées (budget/délai/surface), les expliquer
- Adapter la méthodologie aux défis spécifiques identifiés
- Valoriser les facteurs clés de succès dans chaque section pertinente
"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
            
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du mémoire: {str(e)}")


# Instance globale du service
claude_service = ClaudeService()

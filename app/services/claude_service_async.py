"""
Service Claude AI - VERSION ASYNC JOB QUEUE
Analyse en background avec tracking de progression
"""

import anthropic
from typing import Dict, Any, List
import json
import re
import logging
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)

class ClaudeServiceAsync:
    """Service pour analyses Claude en background avec job tracking"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.ANTHROPIC_MAX_TOKENS
        
        # Mapping lots
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
    
    async def analyze_dce_async(self, extracted_text: str, job_manager, job_id: str) -> Dict[str, Any]:
        """
        Analyse DCE en background avec suivi de progression
        
        Args:
            extracted_text: Texte extrait du DCE
            job_manager: Instance JobManager pour tracking
            job_id: ID du job
        """
        try:
            text_length = len(extracted_text)
            logger.info(f"🚀 Analyse ASYNC démarrée - Job {job_id} - {text_length} caractères")
            
            job_manager.set_running(job_id, "Analyse en cours...")
            job_manager.set_progress(job_id, 5, "Préparation de l'analyse...")
            
            # Toujours utiliser multi-call pour qualité maximale
            return await self._analyze_multi_call_tracked(extracted_text, job_manager, job_id)
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse async job {job_id}: {e}")
            job_manager.set_failed(job_id, str(e))
            raise
    
    async def _analyze_multi_call_tracked(self, full_text: str, job_manager, job_id: str) -> Dict[str, Any]:
        """
        Analyse multi-call avec tracking de progression
        """
        logger.info("🔍 Multi-call strategy avec tracking")
        
        # Étape 1 : Extraction générale (10%)
        job_manager.set_progress(job_id, 10, "Extraction des informations générales...")
        general_info = await self._extract_general_info_expert(full_text[:200000])
        
        job_manager.set_progress(job_id, 15, "Pause 65s (éviter rate limit API)...")
        await asyncio.sleep(65)
        
        # Étape 2 : Analyse lots (15% → 90%)
        job_manager.set_progress(job_id, 20, "Détection des lots...")
        detected_lots = self._detect_lots_in_text(full_text)
        total_lots = len(detected_lots)
        
        logger.info(f"📦 {total_lots} lots détectés")
        
        lots_results = []
        for idx, lot_num in enumerate(detected_lots):
            try:
                # Calculer progression (20% → 90%)
                progress = int(20 + (70 * (idx / total_lots)))
                job_manager.set_progress(job_id, progress, f"Analyse LOT {lot_num}...")
                
                logger.info(f"🔍 Analyse LOT {lot_num} ({idx+1}/{total_lots})...")
                
                lot_text = self._extract_lot_text(full_text, lot_num)
                lot_analysis = await self._analyze_single_lot_expert(lot_num, lot_text)
                
                lots_results.append(lot_analysis)
                logger.info(f"✅ LOT {lot_num} analysé")
                
                # Pause entre lots (sauf dernier)
                if lot_num != detected_lots[-1]:
                    job_manager.set_progress(job_id, progress + 1, f"Pause 65s avant LOT suivant...")
                    await asyncio.sleep(65)
                
            except Exception as e:
                logger.error(f"❌ Erreur lot {lot_num}: {e}")
                await asyncio.sleep(10)
                continue
        
        # Étape 3 : Assemblage (90% → 100%)
        job_manager.set_progress(job_id, 92, "Assemblage des résultats...")
        final_result = self._assemble_final_result_expert(general_info, lots_results)
        
        job_manager.set_progress(job_id, 95, "Génération du rapport final...")
        logger.info("✅ Multi-call terminé")
        
        return final_result
    
    async def _extract_general_info_expert(self, text: str) -> Dict:
        """Extraction infos générales avec prompt expert"""
        prompt = self._build_general_info_prompt()
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt + f"\n\nTexte:\n{text[:150000]}"}]
            )
            
            response_text = message.content[0].text
            result = self._parse_json_response(response_text)
            
            logger.info("✅ Infos générales extraites (expert)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction générale: {e}")
            return {}
    
    async def _analyze_single_lot_expert(self, lot_num: str, lot_text: str) -> Dict:
        """Analyse détaillée d'un lot avec prompt expert"""
        lot_name = self._get_lot_name(lot_num)
        
        prompt = f"""TU ES : Jean-Pierre MARTINEZ, Expert BTP International

Analyse le LOT {lot_num} - {lot_name} de ce DCE.

MISSION : Extraction ULTRA-DÉTAILLÉE de ce lot

Description du lot (150-250 mots MINIMUM) :
- Vue d'ensemble des travaux (50-70 mots)
- Description technique détaillée (80-120 mots)
- Points clés d'exécution (30-50 mots)

Réponds UNIQUEMENT en JSON :
{{
    "lot_number": "{lot_num}",
    "lot_name": "{lot_name}",
    "description": "...",
    "estimated_amount": null,
    "materials": [],
    "specifications": "..."
}}

Texte du lot :
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
            result = self._parse_json_response(response_text)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse lot {lot_num}: {e}")
            return {
                "lot_number": lot_num,
                "lot_name": lot_name,
                "description": f"Lot {lot_name}",
                "estimated_amount": None,
                "materials": [],
                "specifications": ""
            }
    
    def _detect_lots_in_text(self, text: str) -> List[str]:
        """Détecte les lots présents dans le DCE"""
        detected = set()
        text_lower = text.lower()
        
        # Détecter par patterns
        for lot_num, keywords in self.LOT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.add(lot_num)
                    break
        
        # Détecter par numéros explicites
        patterns = [
            r'lot\s+(\d{1,2})',
            r'lot\s+n[°o]\s*(\d{1,2})',
            r'marché\s+(\d{1,2})'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                num = match.group(1).zfill(2)
                if num in self.LOT_KEYWORDS:
                    detected.add(num)
        
        result = sorted(list(detected))
        
        # Si aucun lot détecté, ajouter lot générique
        if not result:
            result = ["00"]
        
        return result
    
    def _extract_lot_text(self, full_text: str, lot_num: str) -> str:
        """Extrait le texte pertinent pour un lot"""
        lot_name = self._get_lot_name(lot_num).lower()
        keywords = self.LOT_KEYWORDS.get(lot_num, [lot_name])
        
        # Extraire sections pertinentes
        relevant_sections = []
        lines = full_text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Vérifier si la ligne contient des keywords du lot
            if any(kw in line_lower for kw in keywords):
                # Prendre contexte (20 lignes avant/après)
                start = max(0, i - 20)
                end = min(len(lines), i + 20)
                section = '\n'.join(lines[start:end])
                relevant_sections.append(section)
        
        result = '\n\n'.join(relevant_sections)
        
        # Si trop peu de texte, prendre un échantillon du DCE entier
        if len(result) < 5000:
            result = full_text[:100000]
        
        return result[:100000]  # Limiter à 100K chars
    
    def _get_lot_name(self, lot_num: str) -> str:
        """Récupère le nom d'un lot"""
        lot_names = {
            "00": "Prestations générales",
            "01": "Gros œuvre",
            "02": "Charpente - Couverture",
            "03": "Cloisons - Isolation",
            "04": "Menuiseries extérieures",
            "05": "Revêtements",
            "06": "Plomberie - Sanitaires",
            "07": "Électricité",
            "08": "Climatisation - Ventilation",
            "09": "Aménagements intérieurs",
            "10": "Ascenseurs",
            "11": "Serrurerie - Métallerie",
            "12": "VRD - Aménagements extérieurs",
            "13": "Espaces verts"
        }
        return lot_names.get(lot_num, f"Lot {lot_num}")
    
    def _assemble_final_result_expert(self, general_info: Dict, lots_analysis: List[Dict]) -> Dict:
        """Assemble le résultat final"""
        return {
            "project_info": general_info.get("project_info", {}),
            "requirements": general_info.get("requirements", []),
            "technical_constraints": general_info.get("technical_constraints", {}),
            "risks": general_info.get("risks", []),
            "suspended_opinions": general_info.get("suspended_opinions", []),
            "key_dates": general_info.get("key_dates", {}),
            "budget_breakdown": general_info.get("budget_breakdown", {}),
            "lots": lots_analysis
        }
    
    def _build_general_info_prompt(self) -> str:
        """Construit le prompt pour extraction générale"""
        return """TU ES : Jean-Pierre MARTINEZ, Expert BTP

Extrais les informations générales de ce DCE.

Réponds en JSON :
{
    "project_info": {...},
    "requirements": [...],
    "technical_constraints": {...},
    "risks": [...],
    "suspended_opinions": [...],
    "key_dates": {...},
    "budget_breakdown": {...}
}
"""
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parse une réponse JSON"""
        try:
            content_clean = text.strip()
            if content_clean.startswith("```json"):
                content_clean = content_clean[7:]
            if content_clean.startswith("```"):
                content_clean = content_clean[3:]
            if content_clean.endswith("```"):
                content_clean = content_clean[:-3]
            
            return json.loads(content_clean.strip())
        except Exception as e:
            logger.error(f"❌ Erreur parsing JSON: {e}")
            return {}

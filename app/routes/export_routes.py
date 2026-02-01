"""
Routes d'export de documents - VERSION PRO
Génération DOCX COMPLÈTE avec toutes les données extraites
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os
from datetime import datetime

from app.database import get_db, User, DCEAnalysis, GeneratedDocument
from app.routes.auth import get_current_active_user

router = APIRouter()

# ========================================
# UTILITY FUNCTIONS
# ========================================

def add_colored_paragraph(doc, text, color_rgb=(0, 0, 0), bold=False, font_size=11):
    """Ajoute un paragraphe avec couleur personnalisée"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor(*color_rgb)
    if bold:
        run.font.bold = True
    return para

def add_table_row(table, cells_data, is_header=False):
    """Ajoute une ligne à un tableau"""
    row = table.add_row()
    for i, cell_data in enumerate(cells_data):
        cell = row.cells[i]
        cell.text = str(cell_data)
        if is_header:
            cell.paragraphs[0].runs[0].font.bold = True
            # Fond gris clair pour l'en-tête
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), 'E7E7E7')
            cell._element.get_or_add_tcPr().append(shading_elm)

def format_currency(amount):
    """Formate un montant en euros"""
    if amount is None:
        return "Non spécifié"
    return f"{amount:,.2f} €".replace(',', ' ')

def format_date(date_str):
    """Formate une date"""
    if not date_str or date_str == "null":
        return "Non spécifiée"
    try:
        date_obj = datetime.fromisoformat(date_str)
        return date_obj.strftime("%d/%m/%Y")
    except:
        return date_str

# ========================================
# MAIN DOCX GENERATION
# ========================================

def create_docx_from_analysis(analysis_result: dict, project_name: str) -> str:
    """
    Génère un MÉMOIRE TECHNIQUE COMPLET depuis les résultats d'analyse V2
    """
    
    doc = Document()
    
    # Configuration globale
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
    
    project_info = analysis_result.get("project_info", {})
    requirements = analysis_result.get("requirements", [])
    lots = analysis_result.get("lots", [])
    technical_constraints = analysis_result.get("technical_constraints", {})
    suspended_opinions = analysis_result.get("suspended_opinions", [])
    risks = analysis_result.get("risks", [])
    budget_breakdown = analysis_result.get("budget_breakdown", {})
    key_dates = analysis_result.get("key_dates", {})
    
    # ========================================
    # PAGE DE GARDE
    # ========================================
    
    title = doc.add_heading("MÉMOIRE TECHNIQUE", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.runs[0].font.color.rgb = RGBColor(255, 107, 53)  # Orange
    
    subtitle = doc.add_heading(project_name or "Projet BTP", level=1)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Informations du projet
    if project_info.get("client"):
        client_para = doc.add_paragraph(f"Maître d'ouvrage : {project_info['client']}")
        client_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        client_para.runs[0].font.size = Pt(12)
    
    if project_info.get("location"):
        location_para = doc.add_paragraph(f"📍 {project_info['location']}")
        location_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        location_para.runs[0].font.size = Pt(11)
    
    # Date de génération
    date_para = doc.add_paragraph(
        f"\nDocument généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    )
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date_para.runs[0].font.italic = True
    date_para.runs[0].font.size = Pt(10)
    date_para.runs[0].font.color.rgb = RGBColor(107, 114, 128)
    
    doc.add_page_break()
    
    # ========================================
    # SECTION 1 : PRÉSENTATION DE L'ENTREPRISE
    # ========================================
    
    doc.add_heading("1. PRÉSENTATION DE L'ENTREPRISE", level=2)
    
    doc.add_paragraph(
        "Notre entreprise dispose d'une expertise reconnue dans le secteur du BTP et du génie civil. "
        "Forte de nombreuses années d'expérience, nous avons développé un savoir-faire technique qui "
        "nous permet d'appréhender les projets les plus complexes avec rigueur et professionnalisme."
    )
    
    doc.add_paragraph(
        "Nous intervenons sur l'ensemble des corps d'état du bâtiment et disposons des certifications "
        "et qualifications nécessaires pour mener à bien ce type de projet."
    )
    
    # ========================================
    # SECTION 2 : ANALYSE DÉTAILLÉE DU PROJET
    # ========================================
    
    doc.add_heading("2. ANALYSE DÉTAILLÉE DU PROJET", level=2)
    
    # Présentation générale
    doc.add_heading("2.1. Présentation générale", level=3)
    
    description = f"Le projet \"{project_info.get('name', 'à réaliser')}\" "
    
    if project_info.get("project_type"):
        description += f"consiste en {project_info['project_type']}. "
    
    if project_info.get("composition"):
        description += f"Il comprend {project_info['composition']}. "
    
    if project_info.get("typologies"):
        typologies = ', '.join(project_info['typologies'])
        description += f"Les typologies proposées sont : {typologies}. "
    
    doc.add_paragraph(description)
    
    # Caractéristiques principales
    doc.add_heading("2.2. Caractéristiques principales", level=3)
    
    characteristics = []
    
    if project_info.get("total_surface_m2"):
        characteristics.append(f"Surface totale : {project_info['total_surface_m2']} m²")
    
    if project_info.get("structure_type"):
        characteristics.append(f"Type de structure : {project_info['structure_type']}")
    
    if project_info.get("budget_ht"):
        characteristics.append(f"Budget estimé : {format_currency(project_info['budget_ht'])} HT")
    
    if project_info.get("duration_months"):
        characteristics.append(f"Durée d'exécution : {project_info['duration_months']} mois")
    
    if project_info.get("moe"):
        characteristics.append(f"Maître d'Œuvre : {project_info['moe']}")
    
    for char in characteristics:
        doc.add_paragraph(char, style='List Bullet')
    
    # ========================================
    # SECTION 3 : LOTS TECHNIQUES
    # ========================================
    
    if lots and len(lots) > 0:
        doc.add_heading("3. LOTS TECHNIQUES", level=2)
        
        doc.add_paragraph(
            f"Le projet est décomposé en {len(lots)} lots techniques. "
            "Voici le détail de chaque lot :"
        )
        
        for lot in lots:
            doc.add_heading(
                f"Lot {lot.get('number', 'XX')} - {lot.get('name', 'Non spécifié')}",
                level=3
            )
            
            # Description du lot
            if lot.get('description'):
                doc.add_paragraph(lot['description'])
            
            # Matériaux
            if lot.get('materials') and len(lot['materials']) > 0:
                materials_para = doc.add_paragraph("Matériaux principaux : ")
                materials_para.add_run(', '.join(lot['materials'])).italic = True
            
            # Spécifications
            if lot.get('specifications'):
                spec_para = doc.add_paragraph("Spécifications : ")
                spec_para.add_run(lot['specifications']).font.size = Pt(10)
            
            # Budget
            if lot.get('estimated_amount'):
                budget_para = doc.add_paragraph(
                    f"💰 Montant estimé : {format_currency(lot['estimated_amount'])} HT"
                )
                budget_para.runs[0].font.bold = True
                budget_para.runs[0].font.color.rgb = RGBColor(16, 185, 129)  # Vert
    
    # ========================================
    # SECTION 4 : CONTRAINTES TECHNIQUES
    # ========================================
    
    doc.add_heading("4. CONTRAINTES TECHNIQUES", level=2)
    
    # Contraintes climatiques
    if technical_constraints.get('climate'):
        doc.add_heading("4.1. Contraintes climatiques", level=3)
        climate = technical_constraints['climate']
        
        if climate.get('zone'):
            doc.add_paragraph(f"Zone climatique : {climate['zone']}")
        
        if climate.get('wind_speed_ms'):
            doc.add_paragraph(
                f"⚠️ Vent : {climate['wind_speed_ms']} m/s - Nécessite une attention particulière "
                "dans le dimensionnement des structures."
            )
        
        if climate.get('rainfall_intensity'):
            doc.add_paragraph(f"Précipitations : {climate['rainfall_intensity']}")
    
    # Contraintes sismiques
    if technical_constraints.get('seismic'):
        doc.add_heading("4.2. Contraintes sismiques", level=3)
        seismic = technical_constraints['seismic']
        
        if seismic.get('zone'):
            doc.add_paragraph(f"Zone sismique : {seismic['zone']}")
        
        if seismic.get('risk_level'):
            risk_text = f"Niveau de risque : {seismic['risk_level']}"
            risk_para = doc.add_paragraph(risk_text)
            if seismic['risk_level'] in ['Moyen', 'Fort']:
                risk_para.runs[0].font.color.rgb = RGBColor(239, 68, 68)  # Rouge
                risk_para.runs[0].font.bold = True
    
    # Contraintes géotechniques
    if technical_constraints.get('geotechnical'):
        doc.add_heading("4.3. Contraintes géotechniques", level=3)
        geotech = technical_constraints['geotechnical']
        
        if geotech.get('study_available'):
            doc.add_paragraph("✅ Étude géotechnique disponible")
        else:
            doc.add_paragraph("⚠️ Étude géotechnique à prévoir")
        
        if geotech.get('soil_type'):
            doc.add_paragraph(f"Type de sol : {geotech['soil_type']}")
        
        if geotech.get('foundation_type'):
            doc.add_paragraph(f"Type de fondations recommandé : {geotech['foundation_type']}")
        
        if geotech.get('groundwater_level'):
            doc.add_paragraph(f"Niveau de nappe : {geotech['groundwater_level']}")
    
    # Risques spécifiques
    if technical_constraints.get('specific_risks') and len(technical_constraints['specific_risks']) > 0:
        doc.add_heading("4.4. Risques spécifiques", level=3)
        
        for risk in technical_constraints['specific_risks']:
            risk_text = f"⚠️ {risk.get('type', 'Risque')} : {risk.get('description', '')}"
            risk_para = doc.add_paragraph(risk_text)
            
            if risk.get('treatment_required'):
                treatment_para = doc.add_paragraph(
                    f"   → Traitement OBLIGATOIRE à prévoir",
                    style='List Bullet'
                )
                treatment_para.runs[0].font.color.rgb = RGBColor(239, 68, 68)
                treatment_para.runs[0].font.bold = True
    
    # ========================================
    # SECTION 5 : AVIS SUSPENDUS & POINTS DE VIGILANCE
    # ========================================
    
    if suspended_opinions and len(suspended_opinions) > 0:
        doc.add_heading("5. AVIS SUSPENDUS & POINTS DE VIGILANCE", level=2)
        
        add_colored_paragraph(
            doc,
            "⚠️ ATTENTION : Des avis suspendus ont été identifiés dans le DCE. "
            "Ces points devront être clarifiés avant le démarrage des travaux.",
            color_rgb=(239, 68, 68),
            bold=True,
            font_size=11
        )
        
        doc.add_paragraph()  # Ligne vide
        
        for opinion in suspended_opinions:
            # Référence de l'avis
            ref_heading = doc.add_heading(
                f"📌 {opinion.get('reference', 'Avis suspendu')}",
                level=3
            )
            
            # Sujet
            if opinion.get('subject'):
                subject_para = doc.add_paragraph(f"Sujet : ")
                subject_para.add_run(opinion['subject']).font.bold = True
            
            # Description
            if opinion.get('description'):
                doc.add_paragraph(opinion['description'])
            
            # Impact
            if opinion.get('impact'):
                impact_colors = {
                    'critical': (220, 38, 38),
                    'high': (234, 88, 12),
                    'medium': (245, 158, 11),
                    'low': (74, 144, 226)
                }
                impact_color = impact_colors.get(opinion['impact'], (107, 114, 128))
                
                impact_para = doc.add_paragraph()
                impact_run = impact_para.add_run(f"Impact : {opinion['impact'].upper()}")
                impact_run.font.bold = True
                impact_run.font.color.rgb = RGBColor(*impact_color)
            
            # Action requise
            if opinion.get('action_required'):
                action_para = doc.add_paragraph(f"Action requise : {opinion['action_required']}")
                action_para.runs[0].font.italic = True
            
            doc.add_paragraph()  # Ligne vide entre les avis
    
    # ========================================
    # SECTION 6 : EXIGENCES CRITIQUES
    # ========================================
    
    doc.add_heading("6. CONFORMITÉ AUX EXIGENCES", level=2)
    
    eliminatory_reqs = [r for r in requirements if r.get('is_eliminatory')]
    mandatory_reqs = [r for r in requirements if r.get('is_mandatory') and not r.get('is_eliminatory')]
    other_reqs = [r for r in requirements if not r.get('is_eliminatory') and not r.get('is_mandatory')]
    
    # Critères éliminatoires
    if eliminatory_reqs:
        doc.add_heading("6.1. Critères éliminatoires", level=3)
        
        add_colored_paragraph(
            doc,
            f"🔴 {len(eliminatory_reqs)} critère(s) éliminatoire(s) identifié(s). "
            "Le non-respect de ces exigences entraînerait l'élimination automatique de l'offre.",
            color_rgb=(220, 38, 38),
            bold=True
        )
        
        doc.add_paragraph()
        
        for req in eliminatory_reqs:
            # Titre
            title_para = doc.add_paragraph()
            title_run = title_para.add_run(f"🔴 {req.get('title', 'Exigence')}")
            title_run.font.bold = True
            title_run.font.size = Pt(11)
            
            # Catégorie
            if req.get('category'):
                cat_para = doc.add_paragraph(f"Catégorie : {req['category']}", style='List Bullet')
                cat_para.runs[0].font.size = Pt(10)
            
            # Description
            if req.get('description'):
                desc_para = doc.add_paragraph(req['description'])
                desc_para.runs[0].font.size = Pt(10)
            
            # Détails
            if req.get('details'):
                details_para = doc.add_paragraph(f"Détails : {req['details']}")
                details_para.runs[0].font.italic = True
                details_para.runs[0].font.size = Pt(9)
            
            # Référence
            if req.get('reference_number'):
                ref_para = doc.add_paragraph(f"Référence : {req['reference_number']}")
                ref_para.runs[0].font.size = Pt(9)
                ref_para.runs[0].font.color.rgb = RGBColor(107, 114, 128)
            
            # Source
            if req.get('source'):
                source_para = doc.add_paragraph(f"Source : {req['source']}")
                source_para.runs[0].font.size = Pt(9)
                source_para.runs[0].font.color.rgb = RGBColor(107, 114, 128)
            
            doc.add_paragraph()  # Ligne vide
    
    # Critères obligatoires
    if mandatory_reqs:
        doc.add_heading("6.2. Exigences obligatoires", level=3)
        
        for req in mandatory_reqs:
            title_para = doc.add_paragraph()
            title_run = title_para.add_run(f"⚠️ {req.get('title', 'Exigence')}")
            title_run.font.bold = True
            
            if req.get('description'):
                doc.add_paragraph(req['description'])
            
            if req.get('details'):
                doc.add_paragraph(f"Détails : {req['details']}", style='List Bullet')
    
    # Autres exigences
    if other_reqs and len(other_reqs) > 0:
        doc.add_heading("6.3. Autres exigences", level=3)
        
        for req in other_reqs[:10]:  # Limiter à 10 pour ne pas surcharger
            doc.add_paragraph(f"• {req.get('title', 'Exigence')}")
    
    # ========================================
    # SECTION 7 : BUDGET DÉTAILLÉ
    # ========================================
    
    if budget_breakdown.get('by_lot') and len(budget_breakdown['by_lot']) > 0:
        doc.add_heading("7. BUDGET DÉTAILLÉ", level=2)
        
        # Budget total
        if budget_breakdown.get('total_ht'):
            total_para = doc.add_paragraph(
                f"💰 Budget total estimé : {format_currency(budget_breakdown['total_ht'])} HT"
            )
            total_para.runs[0].font.size = Pt(12)
            total_para.runs[0].font.bold = True
            total_para.runs[0].font.color.rgb = RGBColor(16, 185, 129)
        
        doc.add_paragraph()
        
        # Tableau des lots
        table = doc.add_table(rows=1, cols=3)
        table.style = 'Light Grid Accent 1'
        
        # En-tête
        add_table_row(table, ['Lot', 'Désignation', 'Montant HT'], is_header=True)
        
        # Lignes du tableau
        for lot_budget in budget_breakdown['by_lot']:
            lot_number = lot_budget.get('lot_number', '??')
            
            # Trouver le nom du lot
            lot_name = "Non spécifié"
            for lot in lots:
                if lot.get('number') == lot_number:
                    lot_name = lot.get('name', 'Non spécifié')
                    break
            
            amount = format_currency(lot_budget.get('amount_ht'))
            
            row = table.add_row()
            row.cells[0].text = f"Lot {lot_number}"
            row.cells[1].text = lot_name
            row.cells[2].text = amount
    
    # ========================================
    # SECTION 8 : PLANNING PRÉVISIONNEL
    # ========================================
    
    doc.add_heading("8. PLANNING PRÉVISIONNEL", level=2)
    
    # Dates clés
    if any(key_dates.values()):
        doc.add_heading("8.1. Dates clés", level=3)
        
        dates_info = [
            ("Publication", key_dates.get('publication')),
            ("Visite de site", key_dates.get('site_visit')),
            ("Date limite questions", key_dates.get('questions_deadline')),
            ("🔴 Date limite remise offres", key_dates.get('submission_deadline')),
            ("Démarrage travaux", key_dates.get('start_works')),
            ("Fin travaux", key_dates.get('end_works'))
        ]
        
        for label, date in dates_info:
            if date and date != "null":
                formatted_date = format_date(date)
                para = doc.add_paragraph(f"{label} : {formatted_date}", style='List Bullet')
                
                # Mettre en rouge la deadline de soumission
                if "🔴" in label:
                    para.runs[0].font.bold = True
                    para.runs[0].font.color.rgb = RGBColor(220, 38, 38)
    
    # Durée d'exécution
    if project_info.get('duration_months'):
        doc.add_heading("8.2. Durée d'exécution", level=3)
        
        duration_text = (
            f"Sur la base de notre analyse du projet, nous estimons la durée d'exécution à "
            f"{project_info['duration_months']} mois. Ce planning intègre des marges de sécurité "
            f"pour faire face aux aléas climatiques et techniques éventuels."
        )
        doc.add_paragraph(duration_text)
    
    # ========================================
    # SECTION 9 : MÉTHODOLOGIE D'EXÉCUTION
    # ========================================
    
    doc.add_heading("9. MÉTHODOLOGIE D'EXÉCUTION", level=2)
    
    doc.add_paragraph(
        "Notre méthodologie d'exécution repose sur une planification rigoureuse et une coordination "
        "optimale des différents corps d'état. Nous mettons en œuvre les moyens humains et matériels "
        "nécessaires pour garantir le respect des délais et de la qualité attendue."
    )
    
    doc.add_heading("9.1. Organisation du chantier", level=3)
    
    doc.add_paragraph(
        "L'organisation sera structurée autour d'une équipe dédiée comprenant un chef de chantier "
        "expérimenté, des conducteurs de travaux spécialisés et des compagnons qualifiés. "
        "Un suivi hebdomadaire de l'avancement sera assuré avec le maître d'œuvre."
    )
    
    # ========================================
    # SECTION 10 : MOYENS TECHNIQUES ET HUMAINS
    # ========================================
    
    doc.add_heading("10. MOYENS TECHNIQUES ET HUMAINS", level=2)
    
    doc.add_paragraph(
        "Nous disposons d'un parc matériel moderne et régulièrement entretenu, parfaitement adapté "
        "aux exigences de ce type de chantier. Notre personnel est formé aux dernières techniques "
        "et normes de sécurité."
    )
    
    # ========================================
    # SECTION 11 : QUALITÉ, SÉCURITÉ ET ENVIRONNEMENT
    # ========================================
    
    doc.add_heading("11. QUALITÉ, SÉCURITÉ ET ENVIRONNEMENT", level=2)
    
    doc.add_paragraph(
        "La qualité est au cœur de nos préoccupations. Nous disposons des certifications requises "
        "et mettons en place un Plan d'Assurance Qualité (PAQ) adapté à chaque projet."
    )
    
    doc.add_heading("11.1. Démarche environnementale", level=3)
    
    doc.add_paragraph(
        "Nous nous engageons à minimiser l'impact environnemental de nos activités par une gestion "
        "optimisée des déchets, le recours à des matériaux durables lorsque cela est possible, et "
        "le respect scrupuleux de la réglementation environnementale."
    )
    
    # ========================================
    # FOOTER
    # ========================================
    
    doc.add_page_break()
    
    footer_para = doc.add_paragraph(
        "\n\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Mémoire technique généré automatiquement par Bid-Killer Engine V2.0 PRO\n"
        f"Date de génération : {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_para.runs[0].font.size = Pt(8)
    footer_para.runs[0].font.color.rgb = RGBColor(156, 163, 175)
    footer_para.runs[0].font.italic = True
    
    # ========================================
    # SAUVEGARDER
    # ========================================
    
    output_dir = "/tmp/documents" if os.path.exists("/tmp") else "./documents"
    os.makedirs(output_dir, exist_ok=True)
    
    safe_project_name = (project_name or "Projet").replace(' ', '_').replace('/', '_')[:50]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"Memoire_Technique_{safe_project_name}_{timestamp}.docx"
    filepath = os.path.join(output_dir, filename)
    
    doc.save(filepath)
    
    return filepath


# ========================================
# ROUTES
# ========================================

async def _generate_docx(
    analysis_id: int,
    current_user: User,
    db: AsyncSession
):
    """
    Fonction commune de génération DOCX
    """
    
    # Récupérer l'analyse
    result = await db.execute(
        select(DCEAnalysis)
        .where(DCEAnalysis.id == analysis_id)
        .where(DCEAnalysis.user_id == current_user.id)
    )
    
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse non trouvée"
        )
    
    if analysis.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'analyse n'est pas encore terminée"
        )
    
    if not analysis.analysis_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les résultats d'analyse ne sont pas disponibles"
        )
    
    # Vérifier si le document existe déjà
    doc_result = await db.execute(
        select(GeneratedDocument)
        .where(GeneratedDocument.analysis_id == analysis_id)
        .where(GeneratedDocument.document_type == "docx")
    )
    
    existing_doc = doc_result.scalar_one_or_none()
    
    if existing_doc and os.path.exists(existing_doc.file_path):
        # Retourner le document existant
        return FileResponse(
            existing_doc.file_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=os.path.basename(existing_doc.file_path)
        )
    
    # Générer le DOCX
    try:
        filepath = create_docx_from_analysis(
            analysis.analysis_result,
            analysis.project_name or "Projet"
        )
        
        # Enregistrer dans la DB
        generated_doc = GeneratedDocument(
            analysis_id=analysis.id,
            user_id=current_user.id,
            document_type="docx",
            file_path=filepath,
            file_size=os.path.getsize(filepath)
        )
        
        db.add(generated_doc)
        await db.commit()
        
        # Retourner le fichier
        return FileResponse(
            filepath,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=os.path.basename(filepath)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du DOCX: {str(e)}"
        )


@router.get("/{analysis_id}/docx")
async def export_docx(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Exporte l'analyse en DOCX
    Route: /api/export/{analysis_id}/docx
    """
    return await _generate_docx(analysis_id, current_user, db)


@router.get("/docx/{analysis_id}")
async def export_docx_alt(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Exporte l'analyse en DOCX (route alternative)
    Route: /api/export/docx/{analysis_id}
    """
    return await _generate_docx(analysis_id, current_user, db)


@router.get("/{analysis_id}/json")
async def export_json(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Exporte l'analyse en JSON
    """
    
    result = await db.execute(
        select(DCEAnalysis)
        .where(DCEAnalysis.id == analysis_id)
        .where(DCEAnalysis.user_id == current_user.id)
    )
    
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse non trouvée"
        )
    
    return analysis.analysis_result

"""
Routes d'export de documents
Génération DOCX et PDF
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
from datetime import datetime

from app.database import get_db, User, DCEAnalysis, GeneratedDocument
from app.routes.auth import get_current_active_user
from app.services.claude_service import claude_service

router = APIRouter()

# ========================================
# UTILS
# ========================================

def create_docx_from_analysis(analysis_result: dict, project_name: str) -> str:
    """
    Génère un fichier DOCX depuis les résultats d'analyse
    """
    
    doc = Document()
    
    # ========================================
    # EN-TÊTE
    # ========================================
    
    # Titre principal
    title = doc.add_heading("MÉMOIRE TECHNIQUE", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Sous-titre projet
    subtitle = doc.add_heading(project_name or "Projet BTP", level=1)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Date
    date_para = doc.add_paragraph(
        f"Document généré le {datetime.now().strftime('%d/%m/%Y')}"
    )
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Saut de page
    doc.add_page_break()
    
    # ========================================
    # SECTION 1 : PRÉSENTATION
    # ========================================
    
    doc.add_heading("1. PRÉSENTATION DE L'ENTREPRISE", level=2)
    
    doc.add_paragraph(
        "Notre entreprise dispose d'une expertise reconnue dans le secteur du BTP et du génie civil. "
        "Forte de nombreuses années d'expérience, nous avons développé un savoir-faire technique qui "
        "nous permet d'appréhender les projets les plus complexes avec rigueur et professionnalisme."
    )
    
    # ========================================
    # SECTION 2 : ANALYSE DU PROJET
    # ========================================
    
    doc.add_heading("2. ANALYSE DU PROJET", level=2)
    
    project_info = analysis_result.get("project_info", {})
    
    doc.add_paragraph(
        f"Le projet \"{project_info.get('name', 'à réaliser')}\" s'inscrit dans une démarche de qualité "
        f"et de respect des normes en vigueur. Notre analyse détaillée du DCE nous a permis d'identifier "
        f"{len(analysis_result.get('requirements', []))} exigences techniques majeures."
    )
    
    # Budget et durée
    if project_info.get("budget_ht"):
        doc.add_paragraph(
            f"Budget estimé : {project_info['budget_ht']:,.0f} € HT",
            style='List Bullet'
        )
    
    if project_info.get("duration_months"):
        doc.add_paragraph(
            f"Durée d'exécution : {project_info['duration_months']} mois",
            style='List Bullet'
        )
    
    # ========================================
    # SECTION 3 : MÉTHODOLOGIE
    # ========================================
    
    doc.add_heading("3. MÉTHODOLOGIE D'EXÉCUTION", level=2)
    
    doc.add_paragraph(
        "Notre méthodologie d'exécution repose sur une planification rigoureuse et une coordination "
        "optimale des différents corps d'état. Nous mettons en œuvre les moyens humains et matériels "
        "nécessaires pour garantir le respect des délais et de la qualité attendue."
    )
    
    doc.add_paragraph(
        "Organisation du chantier :", style='Heading 3'
    )
    
    doc.add_paragraph(
        "L'organisation sera structurée autour d'une équipe dédiée comprenant un chef de chantier "
        "expérimenté, des conducteurs de travaux spécialisés et des compagnons qualifiés."
    )
    
    # ========================================
    # SECTION 4 : MOYENS TECHNIQUES
    # ========================================
    
    doc.add_heading("4. MOYENS TECHNIQUES ET HUMAINS", level=2)
    
    doc.add_paragraph(
        "Nous disposons d'un parc matériel moderne et régulièrement entretenu, parfaitement adapté "
        "aux exigences de ce type de chantier. Notre personnel est formé aux dernières techniques "
        "et normes de sécurité."
    )
    
    # ========================================
    # SECTION 5 : QUALITÉ & SÉCURITÉ
    # ========================================
    
    doc.add_heading("5. QUALITÉ, SÉCURITÉ ET ENVIRONNEMENT", level=2)
    
    doc.add_paragraph(
        "La qualité est au cœur de nos préoccupations. Nous disposons des certifications requises "
        "et mettons en place un Plan d'Assurance Qualité (PAQ) adapté à chaque projet."
    )
    
    doc.add_paragraph(
        "Démarche environnementale :", style='Heading 3'
    )
    
    doc.add_paragraph(
        "Nous nous engageons à minimiser l'impact environnemental de nos activités par une gestion "
        "optimisée des déchets, le recours à des matériaux durables lorsque cela est possible, et "
        "le respect scrupuleux de la réglementation environnementale."
    )
    
    # ========================================
    # SECTION 6 : PLANNING
    # ========================================
    
    doc.add_heading("6. PLANNING PRÉVISIONNEL", level=2)
    
    duration = project_info.get("duration_months", "XX")
    doc.add_paragraph(
        f"Sur la base de notre analyse du projet, nous estimons la durée d'exécution à {duration} mois. "
        "Ce planning intègre des marges de sécurité pour faire face aux aléas climatiques et techniques éventuels."
    )
    
    # ========================================
    # SECTION 7 : CONFORMITÉ
    # ========================================
    
    doc.add_heading("7. CONFORMITÉ AUX EXIGENCES", level=2)
    
    doc.add_paragraph(
        "Notre entreprise répond à l'ensemble des exigences formulées dans le DCE :"
    )
    
    # Lister les exigences éliminatoires
    requirements = analysis_result.get("requirements", [])
    eliminatory_reqs = [r for r in requirements if r.get("is_eliminatory")]
    
    for req in eliminatory_reqs:
        para = doc.add_paragraph(style='List Bullet')
        para.add_run(f"{req.get('category')} : ").bold = True
        para.add_run(
            f"{req.get('title')} - Nous disposons des qualifications et certifications nécessaires."
        )
    
    # ========================================
    # SAUVEGARDER
    # ========================================
    
    output_dir = "./documents"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"Memoire_Technique_{project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    filepath = os.path.join(output_dir, filename)
    
    doc.save(filepath)
    
    return filepath


# ========================================
# ROUTES
# ========================================

@router.get("/{analysis_id}/docx")
async def export_docx(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Exporte l'analyse en DOCX
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

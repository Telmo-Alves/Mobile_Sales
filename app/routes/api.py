"""
API routes for Mobile Sales application
"""

from flask import Blueprint, request, jsonify, session, render_template, current_app, make_response
from ..utils import login_required
from ..database import artigos_repo, reservas_repo, requisicoes_repo, laboratorio_repo
from ..database.connection import get_db_connection

api_bp = Blueprint('api', __name__)

@api_bp.route('/search_cliente')
@login_required
def search_cliente():
    """API para pesquisar clientes (autocomplete)"""
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT FIRST 10 l.Cliente, l.Nome1, l.Zona
            FROM Locais_Entrega l
            INNER JOIN Clientes c ON c.Cliente = l.Cliente
            WHERE c.Situacao IN ('ACT', 'MANUT')
            AND l.Local_ID = 'SEDE'
            AND (UPPER(l.Nome1) LIKE UPPER(?) OR UPPER(l.Cliente) LIKE UPPER(?))
            ORDER BY l.Nome1
        """, (f'%{q}%', f'%{q}%'))
        
        results = [{'id': row[0], 'nome': row[1], 'localidade': row[2]} 
                  for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(results)
    except Exception as e:
        if conn:
            conn.close()
        return jsonify([])

@api_bp.route('/reservas/<codigo>/<lote>')
@login_required
def lista_reservas(codigo, lote):
    """Lista reservas/encomendas usando ReservasRepository"""
    fornecedor = request.args.get('fornecedor', '')
    
    try:
        # Get product info using ArtigosRepository
        info_artigo = artigos_repo.get_product_info(codigo)
        if info_artigo:
            info_artigo = (codigo, info_artigo['descricao'])  # Convert to tuple format for template
        
        # Get reservations using ReservasRepository
        vendedor = session.get('cd_vend', session.get('vendedor', 0))  # Use cd_vend if available, fallback to vendedor
        reservas = reservas_repo.get_reservations(codigo, lote, fornecedor, vendedor)
        
        return render_template('reservas.html', 
                             reservas=reservas,
                             info_artigo=info_artigo,
                             codigo=codigo, 
                             lote=lote,
                             fornecedor=fornecedor)
                             
    except Exception as e:
        current_app.logger.error(f"Erro na consulta de reservas: {str(e)}")
        return render_template('reservas.html', 
                             reservas=[],
                             info_artigo=None,
                             codigo=codigo, 
                             lote=lote,
                             fornecedor=fornecedor,
                             error=f'Erro ao consultar reservas: {str(e)}')

@api_bp.route('/requisicoes/<codigo>/<lote>')
@login_required
def lista_requisicoes(codigo, lote):
    """Lista requisições usando RequisicoesRepository"""
    fornecedor = request.args.get('fornecedor', '')
    
    try:
        # Get product info using ArtigosRepository
        info_artigo = artigos_repo.get_product_info(codigo)
        if info_artigo:
            info_artigo = (codigo, info_artigo['descricao'])  # Convert to tuple format for template
        
        # Get requisitions using RequisicoesRepository
        requisicoes = requisicoes_repo.get_requisitions(codigo, lote, fornecedor)
        
        # Get supplier name if fornecedor is provided
        nome_fornecedor = ""
        if fornecedor:
            nome_fornecedor = requisicoes_repo.get_supplier_name(fornecedor)
        
        return render_template('requisicoes.html', 
                             requisicoes=requisicoes,
                             info_artigo=info_artigo,
                             codigo=codigo, 
                             lote=lote,
                             fornecedor=fornecedor,
                             nome_fornecedor=nome_fornecedor)
                             
    except Exception as e:
        current_app.logger.error(f"Erro na consulta de requisições: {str(e)}")
        return render_template('requisicoes.html', 
                             requisicoes=[],
                             info_artigo=None,
                             codigo=codigo, 
                             lote=lote,
                             fornecedor=fornecedor,
                             nome_fornecedor="",
                             error=f'Erro ao consultar requisições: {str(e)}')

@api_bp.route('/laboratorio/<codigo>/<lote>')
@login_required
def observacoes_laboratorio(codigo, lote):
    """Lista observações de laboratório usando LaboratorioRepository"""
    
    try:
        # Get product info using ArtigosRepository
        info_artigo = artigos_repo.get_product_info(codigo)
        if info_artigo:
            info_artigo = (codigo, info_artigo['descricao'])  # Convert to tuple format for template
        
        # Get laboratory results using LaboratorioRepository
        lab_data = laboratorio_repo.get_lab_results(codigo, lote)
        
        # Get process type for user (simulate getting from session)
        vendedor = session.get('cd_vend', session.get('vendedor', 0))
        process_type = laboratorio_repo.get_process_type_for_user(vendedor)
        
        return render_template('laboratorio.html', 
                             lab_data=lab_data,
                             info_artigo=info_artigo,
                             codigo=codigo, 
                             lote=lote,
                             process_type=process_type,
                             vendedor=vendedor)
                             
    except Exception as e:
        current_app.logger.error(f"Erro na consulta de observações laboratoriais: {str(e)}")
        return render_template('laboratorio.html', 
                             lab_data=None,
                             info_artigo=None,
                             codigo=codigo, 
                             lote=lote,
                             process_type='O',
                             vendedor=0,
                             error=f'Erro ao consultar observações laboratoriais: {str(e)}')

@api_bp.route('/laboratorio/<codigo>/<lote>/pdf')
@login_required
def laboratorio_pdf(codigo, lote):
    """Generate PDF for laboratory observations"""
    try:
        # Get laboratory results
        lab_data = laboratorio_repo.get_lab_results(codigo, lote)
        
        if not lab_data:
            return jsonify({'error': 'Nenhum resultado laboratorial encontrado'}), 404
        
        # Get product info
        info_artigo = artigos_repo.get_product_info(codigo)
        
        # Get process type for user
        vendedor = session.get('cd_vend', session.get('vendedor', 0))
        process_type = laboratorio_repo.get_process_type_for_user(vendedor)
        
        # Generate RISATEL format PDF
        from flask import make_response
        import io
        from datetime import datetime
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.graphics.shapes import Drawing, Rect
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=14, alignment=1, spaceAfter=10)
        subheader_style = ParagraphStyle('SubHeader', parent=styles['Normal'], fontSize=12, alignment=1, spaceAfter=20)
        
        # Title
        elements.append(Paragraph("ANÁLISE LABORATORIAL", header_style))
        elements.append(Paragraph("RELATÓRIO RESUMO", subheader_style))
        
        # Header info table (matching PDF format)
        header_data = [
            ['Relatório Nº:', str(lab_data.get('nr_relatorio', 'N/A')), 'Data:', str(lab_data.get('data_registo', datetime.now().strftime('%d-%m-%Y')))],
            ['Lote:', str(lab_data.get('lote', lote)), '', ''],
            ['Codigo do artigo:', str(lab_data.get('codigo', codigo)), '', ''],
            ['Descrição:', str(info_artigo.get('descricao', '') if info_artigo else ''), '', '']
        ]
        
        header_table = Table(header_data, colWidths=[3*cm, 4*cm, 2*cm, 3*cm])
        header_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            # Span the description across 3 columns (from column 1 to 3)
            ('SPAN', (1, 3), (3, 3)),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        # Main data table (exactly like RISATEL format)
        fmt = laboratorio_repo.format_lab_value
        
        # Complete data sections using all available fields
        
        # Humidade and Ne section
        humidade_ne_data = [
            ['Humidade Relativa (HR%) :', fmt(lab_data.get('hr')), 'Ne :', fmt(lab_data.get('ne_valor')), 'CV% :', fmt(lab_data.get('ne_cv'))]
        ]
        
        # Características de Uster section
        uster_data = [
            ['Características de Uster', '', '', '', '', ''],
            ['U% :', fmt(lab_data.get('uster_u')), 'CVm% :', fmt(lab_data.get('uster_cvm')), '', ''],
            ['Pontos Finos (-40%) :', fmt(lab_data.get('uster_pnt_finos_40')), 'Pontos Finos (-50%) :', fmt(lab_data.get('uster_pnt_finos')), '', ''],
            ['Pontos Grossos (+35%) :', fmt(lab_data.get('uster_pnt_grossos_35')), 'Pontos Grossos (+50%) :', fmt(lab_data.get('uster_pnt_grossos')), '', ''],
            ['Neps (+140%) :', fmt(lab_data.get('uster_neps_1')), 'Neps (+200%) :', fmt(lab_data.get('uster_neps_2')), '', ''],
            ['Pilosidade (H) :', fmt(lab_data.get('uster_pilosidade')), 'CV% :', fmt(lab_data.get('uster_pilosidade_cv')), '', '']
        ]
        
        # RKM section
        rkm_data = [
            ['RKM (TensoRapid) :', fmt(lab_data.get('rkm_valor')), 'CV% :', fmt(lab_data.get('rkm_cv')), 'RKM (Tenac) :', fmt(lab_data.get('rkm_valor_tenac'))],
            ['Alongamento % :', fmt(lab_data.get('rkm_along_valor')), 'CV% :', fmt(lab_data.get('rkm_along_cv')), '', '']
        ]
        
        # Torção section - only if single thread
        torcao_data = []
        if lab_data.get('nr_fios') == 1:
            torcao_data = [
                ['Torção Z (Singelo)', '', 'Retorção S', '', '', ''],
                ['TPI :', fmt(lab_data.get('torcao_tpi_valor')), 'Alfa :', fmt(lab_data.get('torcao_tpi_alfa')), 'CV% :', fmt(lab_data.get('torcao_tpi_cv'))],
                ['', '', 'TPI :', fmt(lab_data.get('torcao_tpi_valor_s')), 'CV% :', fmt(lab_data.get('torcao_tpi_cv_s'))]
            ]
        
        # Combine all data
        main_data = humidade_ne_data + [['', '', '', '', '', '']] + uster_data + [['', '', '', '', '', '']] + rkm_data
        if torcao_data:
            main_data += [['', '', '', '', '', '']] + torcao_data
        
        main_table = Table(main_data, colWidths=[3*cm, 1.5*cm, 2.5*cm, 1.5*cm, 2*cm, 1.5*cm])
        main_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('ALIGN', (5, 0), (5, -1), 'CENTER'),
        ]))
        elements.append(main_table)
        
        # Observations section - separate from main grid
        elements.append(Spacer(1, 30))
        obs_style = ParagraphStyle('Obs', parent=styles['Normal'], fontSize=10, spaceAfter=10)
        elements.append(Paragraph("<b>Obs.:</b> Os resultados são valores médios actuais após acondicionamento do fio.", obs_style))
        
        # Additional observations if any
        if lab_data.get('observacao'):
            elements.append(Paragraph(f"<b>Observações:</b> {str(lab_data.get('observacao'))}", obs_style))
        
        # Footer
        elements.append(Spacer(1, 40))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, alignment=1)
        elements.append(Paragraph("Laboratório de Controlo da Qualidade", footer_style))
        
        # Build PDF
        doc.build(elements)
        
        # Return PDF response
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="lab_data_{codigo}_{lote}.pdf"'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar PDF: {str(e)}")
        return jsonify({'error': f'Erro ao gerar PDF: {str(e)}'}), 500

@api_bp.route('/laboratorio/<codigo>/<lote>/email', methods=['POST'])
@login_required
def laboratorio_email(codigo, lote):
    """Send laboratory results by email with PDF attachment"""
    try:
        # Get email from request
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email é obrigatório'}), 400
            
        email_to = data['email']
        email_message = data.get('message', '')
        
        # Generate PDF content
        lab_data = laboratorio_repo.get_lab_results(codigo, lote)
        if not lab_data:
            return jsonify({'error': 'Nenhum resultado laboratorial encontrado'}), 404
        
        # Get product info
        info_artigo = artigos_repo.get_product_info(codigo)
        
        # Get process type for user
        vendedor = session.get('cd_vend', session.get('vendedor', 0))
        process_type = laboratorio_repo.get_process_type_for_user(vendedor)
        
        # Generate PDF
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1,  # Center alignment
        )
        
        # Add title
        title = Paragraph(f"Resultados Laboratoriais", title_style)
        elements.append(title)
        
        # Add product info
        if info_artigo:
            product_info = Paragraph(f"<b>Produto:</b> {codigo}<br/><b>Descrição:</b> {info_artigo['descricao']}<br/><b>Lote:</b> {lote}", styles['Normal'])
            elements.append(product_info)
            elements.append(Spacer(1, 20))
        
        # Create table data
        table_data = []
        
        # Ne Value
        table_data.append(['Ne', laboratorio_repo.format_lab_value(lab_data['ne_valor']), 
                          'Cv %', laboratorio_repo.format_lab_value(lab_data['ne_cv'])])
        
        # CVM
        table_data.append(['Cvm %', laboratorio_repo.format_lab_value(lab_data['uster_cvm']), '', ''])
        
        # Points
        table_data.append(['PF -50%', laboratorio_repo.format_lab_value(lab_data['uster_pnt_finos']), '', ''])
        table_data.append(['PG +50%', laboratorio_repo.format_lab_value(lab_data['uster_pnt_grossos']), '', ''])
        
        # Neps based on process type
        if process_type == 'O':
            table_data.append(['N +280%', laboratorio_repo.format_lab_value(lab_data['uster_neps_3']), '', ''])
        else:
            table_data.append(['N +200%', laboratorio_repo.format_lab_value(lab_data['uster_neps_2']), '', ''])
        
        # RKM
        table_data.append(['Rkm', laboratorio_repo.format_lab_value(lab_data['rkm_valor']), 
                          'Cv %', laboratorio_repo.format_lab_value(lab_data['rkm_cv'])])
        
        # Torsion
        if lab_data['nr_fios'] == 1:
            table_data.append(['Torção', laboratorio_repo.format_lab_value(lab_data['torcao_tpi_valor']), 
                              str(lab_data['tipo_torcao'] or ''), ''])
        else:
            table_data.append(['Retorção', laboratorio_repo.format_lab_value(lab_data['torcao_tpi_valor_s']), 
                              str(lab_data['tipo_torcao_s'] or ''), ''])
        
        # Hairiness
        table_data.append(['Pilosidade', laboratorio_repo.format_lab_value(lab_data['uster_pilosidade']), 
                          'Cv %', laboratorio_repo.format_lab_value(lab_data['uster_pilosidade_cv'])])
        
        # Create table
        table = Table(table_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 1*inch])
        
        # Style the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        # For now, return the PDF for download (email functionality would need SMTP configuration)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="resultados_laboratoriais_{codigo}_{lote}.pdf"'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar email: {str(e)}")
        return jsonify({'error': f'Erro ao processar solicitação: {str(e)}'}), 500
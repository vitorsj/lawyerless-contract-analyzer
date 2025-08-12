"""
Contract summary extraction service for Brazilian investment documents.

This module handles extraction of structured contract information ("ficha do contrato")
using rule-based patterns and prepares data for LLM enhancement.
"""

import logging
import re
from typing import List, Optional

from ..models import (
    ContractSummary,
    PartesContrato, 
    DatasContrato,
    ValoresContrato,
    ConversaoTermos,
    DireitosInvestidor,
    ObrigacoesContrato,
    JurisdicaoContrato,
    Empresa,
    Parte,
    Valor,
    TipoInstrumento,
    TipoSocietario,
    TipoPessoa,
    Moeda,
    Indexador,
    PDFExtractionResult,
    ProcessedClause
)

logger = logging.getLogger(__name__)


class ContractExtractionError(Exception):
    """Custom exception for contract extraction errors."""
    pass


class ContractExtractor:
    """
    Contract summary extractor for Brazilian investment documents.
    
    Extracts structured information using rule-based patterns for:
    - Document type identification
    - Party information (company, investors)
    - Financial terms (values, rates, caps)
    - Dates and terms
    - Rights and obligations
    - Jurisdiction information
    """
    
    def __init__(self):
        """Initialize contract extractor with Brazilian patterns."""
        self._compile_extraction_patterns()
    
    def _compile_extraction_patterns(self):
        """Compile regular expressions for contract data extraction."""
        
        # Document type patterns
        self.doc_type_patterns = {
            TipoInstrumento.SAFE: re.compile(
                r'(?:SAFE|Simple\s+Agreement\s+for\s+Future\s+Equity|'
                r'Instrumento\s+Simples\s+para\s+Patrimônio\s+Futuro)',
                re.IGNORECASE
            ),
            TipoInstrumento.MUTUO_CONVERSIVEL: re.compile(
                r'(?:Mútuo\s+Conversível|Empréstimo\s+Conversível|'
                r'Contrato\s+de\s+Mútuo\s+Conversível|Convertible\s+Note)',
                re.IGNORECASE
            ),
            TipoInstrumento.TERM_SHEET: re.compile(
                r'(?:Term\s+Sheet|Termo\s+de\s+Compromisso|'
                r'Carta\s+de\s+Intenções|Memorando\s+de\s+Entendimentos)',
                re.IGNORECASE
            ),
            TipoInstrumento.ACORDO_ACIONISTAS: re.compile(
                r'(?:Acordo\s+de\s+Acionistas|Acordo\s+de\s+Quotistas|'
                r'Shareholders?\s+Agreement|Quotaholders?\s+Agreement)',
                re.IGNORECASE
            ),
            TipoInstrumento.SIDE_LETTER: re.compile(
                r'(?:Side\s+Letter|Carta\s+Adicional|'
                r'Instrumento\s+Particular\s+Adicional)',
                re.IGNORECASE
            )
        }
        
        # Company information patterns
        self.company_patterns = {
            'name': re.compile(
                r'(?:^|\n)\s*(.+?)\s*,?\s*(?:LTDA|S\.?A\.?|EIRELI|Empresário\s+Individual)',
                re.MULTILINE | re.IGNORECASE
            ),
            'cnpj': re.compile(
                r'CNPJ[:\s]*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})',
                re.IGNORECASE
            ),
            'company_type': re.compile(
                r'\b(LTDA|S\.?A\.?|EIRELI|Empresário\s+Individual)\b',
                re.IGNORECASE
            )
        }
        
        # Value patterns (Brazilian currency format)
        self.value_patterns = {
            'currency_value': re.compile(
                r'R\$\s*([\d.,]+)|'
                r'US\$\s*([\d.,]+)|'
                r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:reais?|dólares?)',
                re.IGNORECASE
            ),
            'percentage': re.compile(
                r'(\d+(?:,\d+)?)\s*%',
                re.IGNORECASE
            ),
            'valuation_cap': re.compile(
                r'(?:valuation\s+cap|teto\s+de\s+avaliação|valor\s+máximo)[\s:]*'
                r'R\$\s*([\d.,]+)|US\$\s*([\d.,]+)',
                re.IGNORECASE
            )
        }
        
        # Date patterns (Brazilian format)
        self.date_patterns = {
            'date_br': re.compile(
                r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})',
                re.IGNORECASE
            ),
            'date_extended': re.compile(
                r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
                re.IGNORECASE
            )
        }
        
        # Brazilian months for date parsing
        self.brazilian_months = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        # Investment terms patterns
        self.terms_patterns = {
            'interest_rate': re.compile(
                r'juros?\s+de\s+(\d+(?:,\d+)?)\s*%\s*(?:ao\s+ano|a\.a\.)|'
                r'taxa\s+de\s+juros?\s+(\d+(?:,\d+)?)\s*%',
                re.IGNORECASE
            ),
            'maturity': re.compile(
                r'vencimento[\s:]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})|'
                r'prazo\s+de\s+(\d+)\s+(?:meses?|anos?)',
                re.IGNORECASE
            ),
            'discount': re.compile(
                r'desconto\s+de\s+(\d+(?:,\d+)?)\s*%|'
                r'(\d+(?:,\d+)?)\s*%\s+de\s+desconto',
                re.IGNORECASE
            )
        }
    
    async def extract_contract_summary(
        self, 
        extraction_result: PDFExtractionResult,
        clauses: List[ProcessedClause]
    ) -> ContractSummary:
        """
        Extract structured contract summary from PDF content.
        
        Args:
            extraction_result: PDF extraction result
            clauses: List of processed clauses
        
        Returns:
            ContractSummary with extracted information
        """
        logger.info(f"Starting contract extraction for document {extraction_result.document_id}")
        
        full_text = extraction_result.full_text
        
        try:
            # Extract document type
            doc_type = self._identify_document_type(full_text)
            
            # Extract parties information
            parties = await self._extract_parties(full_text, clauses)
            
            # Extract dates
            dates = self._extract_dates(full_text)
            
            # Extract financial values
            values = self._extract_values(full_text)
            
            # Extract conversion terms
            conversion = self._extract_conversion_terms(full_text)
            
            # Extract rights
            rights = self._extract_rights(full_text)
            
            # Extract obligations
            obligations = self._extract_obligations(full_text)
            
            # Extract jurisdiction
            jurisdiction = self._extract_jurisdiction(full_text)
            
            # Create contract summary
            summary = ContractSummary(
                tipo_instrumento=doc_type,
                partes=parties,
                datas=dates,
                valores=values,
                conversao=conversion,
                direitos=rights,
                obrigacoes=obligations,
                jurisdicao=jurisdiction,
                observacoes=self._generate_observations(full_text)
            )
            
            logger.info(f"Successfully extracted contract summary: {doc_type}")
            return summary
            
        except Exception as e:
            logger.error(f"Contract extraction failed: {str(e)}")
            # Return minimal summary to avoid complete failure
            return self._create_minimal_summary()
    
    def _identify_document_type(self, text: str) -> TipoInstrumento:
        """
        Identify document type based on content patterns.
        
        Args:
            text: Full document text
        
        Returns:
            Document type enum
        """
        for doc_type, pattern in self.doc_type_patterns.items():
            if pattern.search(text):
                logger.info(f"Identified document type: {doc_type}")
                return doc_type
        
        # Default fallback - try to infer from common terms
        text_upper = text.upper()
        
        if any(term in text_upper for term in ['CONVERSÃO', 'CONVERTIBLE', 'JUROS']):
            return TipoInstrumento.MUTUO_CONVERSIVEL
        elif any(term in text_upper for term in ['ACIONISTAS', 'QUOTISTAS', 'SHAREHOLDERS']):
            return TipoInstrumento.ACORDO_ACIONISTAS
        elif any(term in text_upper for term in ['TERM SHEET', 'CARTA DE INTENÇÕES']):
            return TipoInstrumento.TERM_SHEET
        
        logger.warning("Could not identify document type, defaulting to SAFE")
        return TipoInstrumento.SAFE
    
    async def _extract_parties(
        self, 
        text: str, 
        clauses: List[ProcessedClause]
    ) -> PartesContrato:
        """
        Extract parties information from contract text.
        
        Args:
            text: Full document text  
            clauses: List of processed clauses
        
        Returns:
            PartesContrato with company and investor information
        """
        # Look for parties section
        parties_text = self._find_section_text(clauses, ['PARTES', 'QUALIFICAÇÃO'])
        if not parties_text:
            parties_text = text[:2000]  # Use beginning of document as fallback
        
        # Extract company information
        company = self._extract_company_info(parties_text)
        
        # Extract investors
        investors = self._extract_investors_info(parties_text)
        
        # Extract guarantors (less common)
        guarantors = self._extract_guarantors_info(parties_text)
        
        return PartesContrato(
            empresa=company,
            investidores=investors,
            garantidores=guarantors
        )
    
    def _extract_company_info(self, text: str) -> Empresa:
        """Extract company information from text."""
        # Extract company name
        name_match = self.company_patterns['name'].search(text)
        company_name = name_match.group(1).strip() if name_match else "Empresa não identificada"
        
        # Extract CNPJ
        cnpj_match = self.company_patterns['cnpj'].search(text)
        cnpj = cnpj_match.group(1) if cnpj_match else None
        
        # Extract company type
        type_match = self.company_patterns['company_type'].search(text)
        company_type_str = type_match.group(1).upper() if type_match else None
        
        # Map to enum
        company_type = None
        if company_type_str:
            if 'LTDA' in company_type_str:
                company_type = TipoSocietario.LTDA
            elif 'S.A' in company_type_str or 'SA' in company_type_str:
                company_type = TipoSocietario.SA
            elif 'EIRELI' in company_type_str:
                company_type = TipoSocietario.EIRELI
            elif 'EMPRESARIO' in company_type_str:
                company_type = TipoSocietario.EMPRESARIO_INDIVIDUAL
        
        return Empresa(
            nome=company_name,
            tipo=TipoPessoa.PESSOA_JURIDICA,
            tipo_societario=company_type,
            cnpj=cnpj,
            documento=cnpj
        )
    
    def _extract_investors_info(self, text: str) -> List[Parte]:
        """Extract investors information from text."""
        investors = []
        
        # Simple pattern for investor identification
        # This would be enhanced with more sophisticated parsing
        investor_patterns = [
            r'(?:investidor|sócio)[\s:]*(.+?)(?:\n|,|;)',
            r'(.+?)\s+(?:CPF|CNPJ)[\s:]*(\d+[\d.\-/]+)'
        ]
        
        for pattern in investor_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                investor_name = match.group(1).strip()
                if len(investor_name) > 5 and investor_name not in [p.nome for p in investors]:
                    # Determine if it's PF or PJ based on document pattern
                    doc_info = match.group(2) if len(match.groups()) > 1 else None
                    pessoa_type = TipoPessoa.PESSOA_FISICA
                    
                    if doc_info and ('/' in doc_info or len(doc_info.replace('.', '').replace('-', '')) == 14):
                        pessoa_type = TipoPessoa.PESSOA_JURIDICA
                    
                    investors.append(Parte(
                        nome=investor_name,
                        tipo=pessoa_type,
                        documento=doc_info
                    ))
        
        # If no investors found, create a placeholder
        if not investors:
            investors.append(Parte(
                nome="Investidor não identificado",
                tipo=TipoPessoa.PESSOA_FISICA
            ))
        
        return investors
    
    def _extract_guarantors_info(self, text: str) -> List[Parte]:
        """Extract guarantors information from text."""
        # Guarantors are less common, simple extraction
        guarantor_pattern = r'(?:garantidor|fiador|avalista)[\s:]*(.+?)(?:\n|,|;)'
        guarantors = []
        
        matches = re.finditer(guarantor_pattern, text, re.IGNORECASE)
        for match in matches:
            guarantor_name = match.group(1).strip()
            if len(guarantor_name) > 5:
                guarantors.append(Parte(
                    nome=guarantor_name,
                    tipo=TipoPessoa.PESSOA_FISICA  # Default assumption
                ))
        
        return guarantors
    
    def _extract_dates(self, text: str) -> DatasContrato:
        """Extract contract dates from text."""
        dates = {}
        
        # Look for signature date
        signature_patterns = [
            r'assinatura[\s:]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})',
            r'data[\s:]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})',
            r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{4}).*assinatura'
        ]
        
        for pattern in signature_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dates['assinatura'] = self._format_date(match.group(1))
                break
        
        # Look for term/maturity dates
        maturity_patterns = [
            r'vencimento[\s:]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})',
            r'prazo.*?até[\s:]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})',
            r'vigência.*?(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})'
        ]
        
        for pattern in maturity_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dates['vencimento_mutuo'] = self._format_date(match.group(1))
                break
        
        return DatasContrato(**dates)
    
    def _extract_values(self, text: str) -> ValoresContrato:
        """Extract financial values from contract text."""
        # Extract principal amount
        principal = self._extract_principal_amount(text)
        
        # Extract interest rate
        interest_rate = self._extract_interest_rate(text)
        
        # Extract valuation cap
        valuation_cap = self._extract_valuation_cap(text)
        
        # Extract discount percentage
        discount = self._extract_discount_percentage(text)
        
        # Extract indexer
        indexer = self._extract_indexer(text)
        
        return ValoresContrato(
            principal=principal,
            juros_aa=interest_rate,
            indexador=indexer,
            valuation_cap=valuation_cap,
            desconto_percentual=discount
        )
    
    def _extract_principal_amount(self, text: str) -> Valor:
        """Extract principal investment amount."""
        # Look for investment amount patterns
        amount_patterns = [
            r'(?:valor|montante|quantia).*?R\$\s*([\d.,]+)',
            r'(?:investimento|aporte).*?R\$\s*([\d.,]+)',
            r'R\$\s*([\d.,]+).*?(?:investido|aportado)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1)
                try:
                    # Convert Brazilian number format (1.000.000,00)
                    value = float(value_str.replace('.', '').replace(',', '.'))
                    return Valor(moeda=Moeda.BRL, valor=value)
                except ValueError:
                    continue
        
        # Default minimal value
        return Valor(moeda=Moeda.BRL, valor=0.0)
    
    def _extract_interest_rate(self, text: str) -> Optional[float]:
        """Extract annual interest rate."""
        match = self.terms_patterns['interest_rate'].search(text)
        if match:
            rate_str = match.group(1) or match.group(2)
            try:
                return float(rate_str.replace(',', '.'))
            except (ValueError, AttributeError):
                pass
        return None
    
    def _extract_valuation_cap(self, text: str) -> Optional[float]:
        """Extract valuation cap."""
        match = self.value_patterns['valuation_cap'].search(text)
        if match:
            cap_str = match.group(1) or match.group(2)
            try:
                return float(cap_str.replace('.', '').replace(',', '.'))
            except (ValueError, AttributeError):
                pass
        return None
    
    def _extract_discount_percentage(self, text: str) -> Optional[float]:
        """Extract discount percentage."""
        match = self.terms_patterns['discount'].search(text)
        if match:
            discount_str = match.group(1) or match.group(2)
            try:
                return float(discount_str.replace(',', '.'))
            except (ValueError, AttributeError):
                pass
        return None
    
    def _extract_indexer(self, text: str) -> Optional[Indexador]:
        """Extract economic indexer."""
        text_upper = text.upper()
        
        if 'IPCA' in text_upper:
            return Indexador.IPCA
        elif 'SELIC' in text_upper:
            return Indexador.SELIC
        elif 'CDI' in text_upper:
            return Indexador.CDI
        elif 'IGP-M' in text_upper or 'IGP M' in text_upper:
            return Indexador.IGP_M
        
        return None
    
    def _extract_conversion_terms(self, text: str) -> ConversaoTermos:
        """Extract conversion terms."""
        # Simple extraction - would be enhanced with LLM
        return ConversaoTermos()  # Uses defaults
    
    def _extract_rights(self, text: str) -> DireitosInvestidor:
        """Extract investor rights."""
        # Simple extraction - would be enhanced with LLM  
        return DireitosInvestidor()  # Uses defaults
    
    def _extract_obligations(self, text: str) -> ObrigacoesContrato:
        """Extract contract obligations."""
        return ObrigacoesContrato()  # Uses defaults
    
    def _extract_jurisdiction(self, text: str) -> JurisdicaoContrato:
        """Extract jurisdiction information."""
        # Look for forum/jurisdiction clauses
        jurisdiction_patterns = [
            r'foro[\s:]*(.+?)(?:\n|\.)',
            r'jurisdição[\s:]*(.+?)(?:\n|\.)',
            r'comarca[\s:]*(.+?)(?:\n|\.)'
        ]
        
        foro = ""
        for pattern in jurisdiction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                foro = match.group(1).strip()
                break
        
        return JurisdicaoContrato(
            lei_aplicavel="Brasil",
            foro=foro
        )
    
    def _find_section_text(
        self, 
        clauses: List[ProcessedClause], 
        keywords: List[str]
    ) -> str:
        """Find text from clauses matching keywords."""
        for clause in clauses:
            if clause.title:
                title_upper = clause.title.upper()
                if any(keyword.upper() in title_upper for keyword in keywords):
                    return clause.text
        
        return ""
    
    def _format_date(self, date_str: str) -> str:
        """Format Brazilian date string."""
        # Simple date formatting - could be enhanced
        return date_str.replace('/', '-')
    
    def _generate_observations(self, text: str) -> str:
        """Generate observations about the contract."""
        observations = []
        
        if 'arbitragem' in text.lower():
            observations.append("Contrato prevê arbitragem")
        
        if 'garantia' in text.lower():
            observations.append("Contém cláusulas de garantia")
        
        if len(text) > 50000:
            observations.append("Documento extenso - revisar cláusulas detalhadamente")
        
        return "; ".join(observations)
    
    def _create_minimal_summary(self) -> ContractSummary:
        """Create minimal contract summary when extraction fails."""
        return ContractSummary(
            tipo_instrumento=TipoInstrumento.SAFE,
            partes=PartesContrato(
                empresa=Empresa(
                    nome="Empresa não identificada",
                    tipo=TipoPessoa.PESSOA_JURIDICA
                ),
                investidores=[Parte(
                    nome="Investidor não identificado",
                    tipo=TipoPessoa.PESSOA_FISICA
                )]
            ),
            datas=DatasContrato(),
            valores=ValoresContrato(
                principal=Valor(moeda=Moeda.BRL, valor=0.0)
            ),
            conversao=ConversaoTermos(),
            direitos=DireitosInvestidor(),
            obrigacoes=ObrigacoesContrato(),
            jurisdicao=JurisdicaoContrato(),
            observacoes="Extração automática limitada - requer análise manual"
        )
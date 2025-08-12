"""
Agent tools for Brazilian legal contract analysis.

This module contains PydanticAI tools that provide additional functionality
for the contract analysis agent, including legal term lookups, market
comparisons, and clause analysis utilities.
"""

import logging
import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from .prompts import LEGAL_TERMS_GLOSSARY, NEGOTIATION_TEMPLATES

logger = logging.getLogger(__name__)


@dataclass
class MarketBenchmark:
    """Market benchmark data for contract terms."""
    term_type: str
    market_range: Tuple[float, float]
    typical_value: float
    description: str


class LegalTermDatabase:
    """Database of legal terms and market standards for Brazilian investments."""
    
    def __init__(self):
        """Initialize with legal terms and market benchmarks."""
        self.terms_db = LEGAL_TERMS_GLOSSARY
        self.benchmarks = self._initialize_benchmarks()
        self.red_flag_patterns = self._initialize_red_flags()
    
    def _initialize_benchmarks(self) -> Dict[str, MarketBenchmark]:
        """Initialize market benchmarks for common terms."""
        return {
            "juros_mutuo": MarketBenchmark(
                term_type="interest_rate",
                market_range=(8.0, 15.0),
                typical_value=12.0,
                description="Taxa de juros anual para mútuo conversível"
            ),
            "valuation_cap": MarketBenchmark(
                term_type="valuation",
                market_range=(5000000, 50000000),  # R$ 5M - 50M
                typical_value=15000000,  # R$ 15M
                description="Valuation cap típico para SAFE em estágio inicial"
            ),
            "desconto_conversao": MarketBenchmark(
                term_type="discount",
                market_range=(10.0, 30.0),
                typical_value=20.0,
                description="Desconto típico para conversão em rodada futura"
            ),
            "threshold_drag_along": MarketBenchmark(
                term_type="control",
                market_range=(51.0, 75.0),
                typical_value=66.7,
                description="Threshold típico para drag along rights"
            ),
            "preferencia_liquidacao": MarketBenchmark(
                term_type="preference",
                market_range=(1.0, 3.0),
                typical_value=1.0,
                description="Múltiplo de preferência de liquidação"
            )
        }
    
    def _initialize_red_flags(self) -> List[Dict[str, Any]]:
        """Initialize patterns that indicate red flag clauses."""
        return [
            {
                "pattern": r"full\s+ratchet|antidiluição\s+total",
                "severity": "alto",
                "description": "Proteção anti-diluição very restritiva",
                "category": "anti_diluicao"
            },
            {
                "pattern": r"drag\s+along.*?(?:25|30|35)%",
                "severity": "alto", 
                "description": "Threshold muito baixo para drag along",
                "category": "controle"
            },
            {
                "pattern": r"não[\-\s]?concorrência.*?(\d+)\s+anos?",
                "severity": "medio",
                "description": "Cláusula de não-concorrência muito longa",
                "category": "restricoes"
            },
            {
                "pattern": r"múltiplo.*?([3-9]|[1-9]\d)x",
                "severity": "alto",
                "description": "Múltiplo de liquidação excessivo",
                "category": "liquidacao"
            },
            {
                "pattern": r"juros.*?(\d{2,})%",
                "severity": "medio", 
                "description": "Taxa de juros muito alta",
                "category": "financeiro"
            }
        ]


# Global instance
legal_db = LegalTermDatabase()


def define_legal_term(ctx, term: str) -> str:
    """
    Define legal term in Portuguese.
    
    Args:
        term: Legal term to define
    
    Returns:
        Definition in Portuguese or explanation if not found
    """
    term_lower = term.lower().replace(" ", "_").replace("-", "_")
    
    if term_lower in legal_db.terms_db:
        definition = legal_db.terms_db[term_lower]
        logger.info(f"Found definition for term: {term}")
        return f"**{term}**: {definition}"
    
    # Try partial matches
    for key, definition in legal_db.terms_db.items():
        if term_lower in key or key in term_lower:
            return f"**{term}** (termo relacionado): {definition}"
    
    logger.warning(f"Term not found in database: {term}")
    return f"Termo '{term}' não encontrado no glossário. Recomendo consultar assessoria jurídica para definição precisa."


def analyze_clause_risk_factors(ctx, clause_text: str, clause_type: str = "") -> Dict[str, Any]:
    """
    Analyze risk factors in a clause using pattern matching.
    
    Args:
        clause_text: Text of the clause to analyze
        clause_type: Type of clause (optional)
    
    Returns:
        Risk analysis with identified patterns and severity
    """
    analysis = {
        "identified_risks": [],
        "overall_risk": "baixo",
        "recommendations": []
    }
    
    # Check each red flag pattern
    for flag in legal_db.red_flag_patterns:
        pattern = re.compile(flag["pattern"], re.IGNORECASE)
        matches = pattern.findall(clause_text)
        
        if matches:
            risk_item = {
                "pattern": flag["description"],
                "severity": flag["severity"],
                "category": flag["category"],
                "matches": matches
            }
            analysis["identified_risks"].append(risk_item)
            
            # Update overall risk level
            if flag["severity"] == "alto" and analysis["overall_risk"] != "alto":
                analysis["overall_risk"] = "alto"
            elif flag["severity"] == "medio" and analysis["overall_risk"] == "baixo":
                analysis["overall_risk"] = "medio"
    
    # Generate recommendations based on identified risks
    analysis["recommendations"] = generate_risk_recommendations(analysis["identified_risks"])
    
    logger.info(f"Risk analysis completed: {len(analysis['identified_risks'])} risks identified")
    return analysis


def generate_risk_recommendations(risks: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendations based on identified risks."""
    recommendations = []
    
    categories_found = {risk["category"] for risk in risks}
    
    if "anti_diluicao" in categories_found:
        recommendations.extend([
            "Considere negociar weighted average em vez de full ratchet",
            "Proponha um período de carência para a proteção anti-diluição",
            "Exclua emissões para funcionários do cálculo de anti-diluição"
        ])
    
    if "controle" in categories_found:
        recommendations.extend([
            "Negocie um threshold mais alto para direitos de controle (66%+ é mais comum)",
            "Inclua proteções de preço mínimo em mecanismos de drag along",
            "Considere carve-outs para decisões operacionais rotineiras"
        ])
    
    if "liquidacao" in categories_found:
        recommendations.extend([
            "Limite o múltiplo de preferência a 1x-2x",
            "Negocie conversão automática da preferência em IPO",
            "Considere um carve-out para management em eventos de liquidação"
        ])
    
    if "financeiro" in categories_found:
        recommendations.extend([
            "Compare taxa de juros com benchmarks de mercado (8-15% a.a.)",
            "Considere indexação por IPCA ou SELIC em vez de taxa fixa alta",
            "Negocie cap de juros acumulados em caso de conversão"
        ])
    
    return recommendations


def compare_with_market_standards(ctx, term_type: str, value: float) -> Dict[str, Any]:
    """
    Compare a contract term with market standards.
    
    Args:
        term_type: Type of term (e.g., "juros_mutuo", "desconto_conversao")
        value: Value to compare
    
    Returns:
        Comparison analysis with market position
    """
    if term_type not in legal_db.benchmarks:
        return {
            "status": "unknown",
            "message": f"Benchmark não disponível para {term_type}",
            "recommendation": "Consulte assessoria jurídica para avaliação de mercado"
        }
    
    benchmark = legal_db.benchmarks[term_type]
    min_val, max_val = benchmark.market_range
    typical_val = benchmark.typical_value
    
    analysis = {
        "term_type": term_type,
        "your_value": value,
        "market_range": benchmark.market_range,
        "typical_value": typical_val,
        "description": benchmark.description
    }
    
    # Determine market position
    if value < min_val:
        analysis["position"] = "abaixo_mercado"
        analysis["flag"] = "verde" if term_type in ["juros_mutuo"] else "amarelo"
        analysis["message"] = f"Valor abaixo da faixa típica de mercado ({min_val}-{max_val})"
    elif value > max_val:
        analysis["position"] = "acima_mercado"
        analysis["flag"] = "vermelho" if term_type in ["juros_mutuo", "preferencia_liquidacao"] else "amarelo"
        analysis["message"] = f"Valor acima da faixa típica de mercado ({min_val}-{max_val})"
    else:
        analysis["position"] = "dentro_mercado"
        analysis["flag"] = "verde"
        analysis["message"] = f"Valor dentro da faixa de mercado ({min_val}-{max_val})"
    
    # Distance from typical
    distance_from_typical = abs(value - typical_val) / typical_val * 100
    analysis["distance_from_typical_pct"] = distance_from_typical
    
    if distance_from_typical > 50:
        analysis["message"] += f" e significativamente diferente do típico ({typical_val})"
    
    logger.info(f"Market comparison for {term_type}: {analysis['position']}")
    return analysis


def generate_negotiation_questions(ctx, clause_category: str, context: Dict[str, Any] = None) -> List[str]:
    """
    Generate negotiation questions based on clause category.
    
    Args:
        clause_category: Category of the clause (e.g., "anti_diluicao", "drag_along")
        context: Additional context for customization
    
    Returns:
        List of negotiation questions in Portuguese
    """
    if clause_category not in NEGOTIATION_TEMPLATES:
        return [
            "Esta cláusula pode ser simplificada ou ter termos menos restritivos?",
            "Existem exceções ou carve-outs que podemos incluir?",
            "Podemos estabelecer thresholds ou limites para essa disposição?",
            "Como isso funciona em situações específicas do nosso negócio?",
            "Essa cláusula expira ou pode ser reavaliada no futuro?"
        ]
    
    questions = NEGOTIATION_TEMPLATES[clause_category].copy()
    
    # Customize questions with context if provided
    if context:
        for i, question in enumerate(questions):
            if "{valor}" in question and "valor" in context:
                questions[i] = question.format(valor=context["valor"])
            elif "{percentual}" in question and "percentual" in context:
                questions[i] = question.format(percentual=context["percentual"])
            elif "{meses}" in question and "meses" in context:
                questions[i] = question.format(meses=context["meses"])
            elif "{multiplo}" in question and "multiplo" in context:
                questions[i] = question.format(multiplo=context["multiplo"])
            elif "{anos}" in question and "anos" in context:
                questions[i] = question.format(anos=context["anos"])
    
    logger.info(f"Generated {len(questions)} negotiation questions for {clause_category}")
    return questions


def identify_clause_category(ctx, clause_text: str, clause_title: str = "") -> str:
    """
    Identify the category of a clause based on its content.
    
    Args:
        clause_text: Text content of the clause
        clause_title: Title of the clause (optional)
    
    Returns:
        Category identifier
    """
    text_combined = f"{clause_title} {clause_text}".lower()
    
    # Category patterns
    categories = {
        "anti_diluicao": [
            "anti.?diluição", "antidiluição", "proteção.*diluição", 
            "full ratchet", "weighted average", "preço.*conversão"
        ],
        "drag_along": [
            "drag along", "arrastar", "venda.*forçada", "obrigar.*venda"
        ],
        "tag_along": [
            "tag along", "acompanhar", "direito.*venda", "co.?venda"
        ],
        "liquidacao": [
            "liquidação", "preferência", "múltiplo", "distribuição.*recursos",
            "ordem.*pagamento", "waterfall"
        ],
        "pro_rata": [
            "pro.?rata", "subscrição", "manter.*participação", "diluição.*futura"
        ],
        "veto": [
            "veto", "aprovação.*prévia", "consentimento", "matérias.*reservadas"
        ],
        "informacao": [
            "informação", "relatórios", "transparência", "prestação.*contas",
            "demonstrações.*financeiras"
        ],
        "conversao": [
            "conversão", "converter", "transformar", "exercer", "gatilhos"
        ],
        "juros": [
            "juros", "taxa", "remuneração", "correção", "indexação"
        ],
        "prazo": [
            "prazo", "vencimento", "termo", "duração", "vigência"
        ],
        "garantia": [
            "garantia", "penhor", "fiança", "aval", "caução"
        ]
    }
    
    # Score each category
    category_scores = {}
    for category, patterns in categories.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text_combined, re.IGNORECASE))
            score += matches
        category_scores[category] = score
    
    # Return category with highest score
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        if category_scores[best_category] > 0:
            logger.info(f"Identified clause category: {best_category}")
            return best_category
    
    logger.info("Could not identify specific clause category, using 'geral'")
    return "geral"


def extract_numeric_values(ctx, text: str) -> Dict[str, List[float]]:
    """
    Extract numeric values from clause text.
    
    Args:
        text: Clause text to analyze
    
    Returns:
        Dictionary with identified numeric values by type
    """
    values = {
        "percentages": [],
        "monetary_values": [],
        "years": [],
        "days": [],
        "multiples": []
    }
    
    # Extract percentages
    pct_pattern = r'(\d+(?:[,.]\d+)?)\s*%'
    for match in re.finditer(pct_pattern, text):
        value = float(match.group(1).replace(',', '.'))
        values["percentages"].append(value)
    
    # Extract monetary values (Brazilian format)
    money_patterns = [
        r'R\$\s*([\d.,]+)',
        r'reais?\s*([\d.,]+)',
        r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*reais?'
    ]
    
    for pattern in money_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                # Convert Brazilian format to float
                value_str = match.group(1).replace('.', '').replace(',', '.')
                value = float(value_str)
                values["monetary_values"].append(value)
            except (ValueError, IndexError):
                continue
    
    # Extract years
    year_pattern = r'(\d+)\s*anos?'
    for match in re.finditer(year_pattern, text, re.IGNORECASE):
        values["years"].append(float(match.group(1)))
    
    # Extract days
    day_pattern = r'(\d+)\s*dias?'
    for match in re.finditer(day_pattern, text, re.IGNORECASE):
        values["days"].append(float(match.group(1)))
    
    # Extract multiples (e.g., "2x", "1.5x")
    multiple_pattern = r'(\d+(?:[,.]\d+)?)\s*x'
    for match in re.finditer(multiple_pattern, text, re.IGNORECASE):
        value = float(match.group(1).replace(',', '.'))
        values["multiples"].append(value)
    
    # Remove empty lists and log findings
    values = {k: v for k, v in values.items() if v}
    if values:
        logger.info(f"Extracted numeric values: {values}")
    
    return values
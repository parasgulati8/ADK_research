"""
Portfolio Analysis Multi-Agent System

Core module for AI-powered portfolio analysis using 7 specialized agents:
- DataFetcher: Retrieves portfolio data
- RiskAnalyzer: Analyzes portfolio risks
- PerformanceAnalyzer: Evaluates returns
- DiversificationAnalyzer: Checks diversification
- TaxOptimizer: Identifies tax opportunities
- RecommendationEngine: Provides recommendations
- ReportGenerator: Creates executive summary
"""

from .agent import PortfolioAnalysisTeam

__all__ = ["PortfolioAnalysisTeam"]
__version__ = "2.0.0"

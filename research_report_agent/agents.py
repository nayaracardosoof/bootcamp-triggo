from functools import lru_cache

from smolagents import CodeAgent, DuckDuckGoSearchTool

from research_report_agent.config import EVALUATION_MAX_STEPS, GAIA_MAX_STEPS, MAX_STEPS
from research_report_agent.model_factory import create_model


@lru_cache(maxsize=1)
def get_research_agent():
    """Cria e reutiliza o agente principal, com ferramenta de busca web."""
    return CodeAgent(
        tools=[DuckDuckGoSearchTool()],
        model=create_model(),
        max_steps=MAX_STEPS,
        verbosity_level=1,
    )


@lru_cache(maxsize=1)
def get_evaluation_agent():
    """Cria e reutiliza o agente avaliador, sem ferramentas externas."""
    return CodeAgent(
        tools=[],
        model=create_model(),
        max_steps=EVALUATION_MAX_STEPS,
        verbosity_level=1,
    )
    

@lru_cache(maxsize=1)
def get_gaia_agent():
    """Cria e reutiliza o agente GAIA, sem ferramentas externas."""
    return CodeAgent(
        tools=[DuckDuckGoSearchTool()],
        model=create_model(),
        max_steps=GAIA_MAX_STEPS,
        verbosity_level=1,
    )
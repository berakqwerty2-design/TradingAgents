from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent

from tradingagents.agents.utils.core_stock_tools import get_stock_data
from tradingagents.agents.utils.technical_indicators_tools import get_indicators


def create_market_analyst(llm):
    tools = [
        get_stock_data,
        get_indicators,
    ]

    system_prompt = """You are a professional crypto and stock market analyst.
You can use these tools:
- get_stock_data
- get_indicators

Always analyze:
- trend
- momentum
- volatility
- support/resistance
- volume

Return concise but detailed analysis."""

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )

    return agent

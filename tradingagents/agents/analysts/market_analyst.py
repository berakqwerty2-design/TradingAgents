from langchain_core.prompts import ChatPromptTemplate

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    from langchain_core.agents import AgentExecutor
    from langchain.agents import create_tool_calling_agent

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.tools import get_stock_data, get_indicators


def get_verified_market_snapshot(
    symbol: str,
    curr_date: str,
    look_back_days: int = 30,
):
    """
    Compatibility wrapper supaya agent gak error.
    """
    return get_stock_data.invoke(
        {
            "symbol": symbol,
        }
    )


def create_market_analyst(llm):
    tools = [
        get_stock_data,
        get_indicators,
        get_verified_market_snapshot,
    ]

    system_prompt = """
You are a professional crypto and stock market analyst.
You can use these tools:
- get_stock_data
- get_indicators
- get_verified_market_snapshot

Always analyze:
- trend
- momentum
- volatility
- support resistance
- volume

Return concise but detailed analysis.
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(
        llm,
        tools,
        prompt,
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    )

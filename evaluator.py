from typing import List

from council.contexts import (
    AgentContext,
    ScoredChatMessage,
    ChatMessage,
)
from council.runners.budget import Budget
from council.evaluators.evaluator_base import EvaluatorBase

class BasicEvaluatorWithSource(EvaluatorBase):

    """
    A BasicEvaluator that carries along the last Skill source of each Chain ExecutionUnit.
    """

    def execute(self, context: AgentContext, budget: Budget) -> List[ScoredChatMessage]:
        result = []
        for chain_history in context.chainHistory.values():
            chain_result = chain_history[-1].messages[-1]
            score = 1 if chain_result.is_kind_skill and chain_result.is_ok else 0
            result.append(
                ScoredChatMessage(
                    ChatMessage.agent(chain_result.message, chain_result.data, source=chain_result.source, is_error=chain_result.is_error),
                    score,
                )
            )
        return result
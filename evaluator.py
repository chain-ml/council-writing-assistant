from typing import List

from council.contexts import (
    AgentContext,
    ScoredChatMessage,
    ChatMessage,
)
from council.evaluators.evaluator_base import EvaluatorBase


class BasicEvaluatorWithSource(EvaluatorBase):

    """
    A BasicEvaluator that carries along the last Skill source of each Chain ExecutionUnit.
    """

    def _execute(self, context: AgentContext) -> List[ScoredChatMessage]:
        result = []
        for chain_history in context.chains:
            chain_result = chain_history.last_message
            score = 1 if chain_result.is_kind_skill and chain_result.is_ok else 0
            result.append(
                ScoredChatMessage(
                    ChatMessage.agent(chain_result.message, chain_result.data, source=chain_result.source, is_error=chain_result.is_error),
                    score,
                )
            )
        return result

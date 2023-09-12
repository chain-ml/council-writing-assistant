# A (minimally) customized Evaluator

In Council, Evaluators can be used to review the output of Chains and assign scores. Like other Council abstractions, Evaluators are very flexible and you can implement highly customized logic. In this tutorial, however, we'll stick with a very basic Evaluator.

To implement our solution, we needed to add aggregation to the Controller's `select_responses` function. And since we have two different types of responses that may need to be aggregated (Outlines and Articles), we need a convenient way of knowing which Chains produced which responses. An easy solution is to customize the `BasicController` implementation by adding `source=chain_result.source` when packing `ChatMessages` into the Evaluator result.

Here is the full implementation of our Evaluator:

```python
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
```

In the next, we will implement the [Filter](./6_filter.md).

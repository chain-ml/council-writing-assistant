from council.contexts import AgentContext, LLMContext, Monitored, ChatMessage
from council.chains import Chain
from council.llm import LLMMessage, LLMBase
from council.utils import Option
from council.controllers import ControllerBase, ExecutionUnit

import logging
from string import Template
from typing import List, Tuple

logger = logging.getLogger("council")


class AppState:
    iteration: int
    outline: str
    article: str

    def __init__(self):
        self.iteration = 0
        self.outline = ""
        self.article = ""


class WritingAssistantController(ControllerBase):
    """
    A controller that uses an LLM to decide the execution plan
    """

    _llm: Monitored[LLMBase]
    state: AppState

    def __init__(
        self,
        llm: LLMBase,
        chains: List[Chain],
        response_threshold: float = 0,
        top_k_execution_plan: int = 5,
    ):
        """
        Initialize a new instance

        Parameters:
            llm (LLMBase): the instance of LLM to use
            chains (List[Chain]): the chains to use
            response_threshold (float): a minimum threshold to select a response from its score
            top_k_execution_plan (int): maximum number of execution plan returned
        """
        super().__init__(chains)
        self._llm = self.new_monitor("llm", llm)
        self._response_threshold = response_threshold
        self._top_k = top_k_execution_plan

        # Controller state variables
        self.state = AppState()

    def _execute(self, context: AgentContext) -> List[ExecutionUnit]:
        
        """
        Planning phase.
        """

        system_prompt = "You are the Controller module for an AI assistant built to write and revise research articles."

        main_prompt_template = Template("""
        # Task Description
        Your task is to decide how best to write or revise the ARTICLE. Considering the ARTICLE OUTLINE, ARTICLE, and the CONVERSATION HISTORY,
        use your available CHAINS to decide what steps to take next. You are not responsible for writing any sections,
        you are only responsible for deciding what to do next. You will delegate work to other agents via CHAINS.

        # Instructions

        You may delegate work to one or more CHAINS.
        Consider the name and description of each chain and decide whether or how you want to use it. 
        Only give instructions to relevant chains.
        You can decide to invoke the same chain multiple times, with different instructions. 
        Provide chain instructions that are relevant towards completing your TASK.
        If the ARTICLE has fewer than 1500 words, give instructions to expand relevant sections.
        You will also give each chain invocation a score out of 10, so that their execution can be prioritized.

        ## CHAINS (provided as a list of chain names and descriptions)
        $chains

        ## CONVERSATION HISTORY
        $conversation_history

        ## ARTICLE OUTLINE
        $outline

        ## ARTICLE
        $article

        # Controller Decision formatted precisely as: {chain name};{score out of 10};{instructions on a single line}
        """)

        # Increment iteration
        self.state.iteration += 1

        # Get the Chain details
        chain_details = "\n ".join(
            [f"name: {c.name}, description: {c.description}" for c in self.chains]
        )

        # Get the conversation history
        conversation_history = [f"{m.kind}: {m.message}" for m in context.chat_history.messages]

        messages = [
            LLMMessage.system_message(system_prompt),
            LLMMessage.user_message(
                main_prompt_template.substitute(
                    chains=chain_details,
                    outline=self.state.outline,
                    article=self.state.article,
                    conversation_history=conversation_history,
                )
            ),
        ]

        llm_result = self._llm.inner.post_chat_request(
            context=LLMContext.from_context(context, self._llm),
            messages=messages
        )

        response = llm_result.first_choice
        logger.debug(f"controller response: {response}")

        parsed = response.splitlines()
        parsed = [p for p in parsed if len(p) > 0]
        parsed = [self.parse_line(line) for line in parsed]

        filtered = [
            r.unwrap()
            for r in parsed
            if r.is_some() and r.unwrap()[1] > self._response_threshold
        ]
        if (filtered is None) or (len(filtered) == 0):
            return []

        filtered.sort(key=lambda item: item[1], reverse=True)

        result = []
        for chain, score, instruction in filtered: 
            initial_state = ChatMessage.chain(
                message=instruction, data={"article": self.state.article, "outline": self.state.outline, "iteration": self.state.iteration}
            )
            exec_unit = ExecutionUnit(
                chain,
                context.budget,
                initial_state=initial_state,
                name=f"{chain.name}: {instruction}"
            )
            result.append(exec_unit)

        result = result[: self._top_k]
        return result

    def parse_line(self, line: str) -> Option[Tuple[Chain, int, str]]:
        result: Option[Tuple[Chain, int, str]] = Option.none()
        try:
            (name, score, instruction) = line.split(";")[:3]
            chain = next(filter(lambda item: item.name == name, self.chains))
            result = Option.some((chain, int(score), instruction))
        except Exception as e:
            logger.error(f"Controller parsing error: {e}.\n{line}")
        finally:
            return result

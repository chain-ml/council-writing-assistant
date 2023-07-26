# Creating a customized Controller

In Council, **Controllers** are responsible directing application flow. While Council offers built-in Controllers for simpler applications, we are now going to implement a customized Controller that can make full use of the Skills we defined in the previous steps. 

When implementing a custom Controller, the two major functions that require implementation are `get_plan` and `select_responses`.

To start, recall that when we defined both the OutlineWriterSkill and SectionWriterSkill, we implemented `execute` functions that expect specific information to be provided in the `context`. 

This means that at a high level, this means that we'll want our Controller to do two things:
- Manage state variables
- Invoke Chains and their Skills with correctly-packed `initial_states`

Let's dive in.


```python
from council.contexts import AgentContext, ScoredChatMessage, ChatMessage, ChatMessageKind
from council.chains import Chain
from council.llm import LLMMessage, LLMBase
from council.utils import Option
from council.runners import Budget
from council.controllers import ControllerBase, ExecutionUnit

import logging
from string import Template
from typing import List, Tuple

logger = logging.getLogger(__name__)
```

We start by extending the ControllerBase, which just specifies that we need to implement two functions: `get_plan` and `select_responses`. The constructor parameters `llm`, `response_threshold`, and `top_k_execution_plan` are modelled after Council's built-in LLMController. 

For this custom Controller, we add three **state variables** for the Controller to manage: `_article`, `_outline`, and `_iteration`. 


```python
class WritingAssistantController(ControllerBase):
    """
    A controller that uses an LLM to decide the execution plan
    """

    _llm: LLMBase

    def __init__(
        self,
        llm: LLMBase,
        response_threshold: float = 0,
        top_k_execution_plan: int = 5,
    ):
        """
        Initialize a new instance

        Parameters:
            llm (LLMBase): the instance of LLM to use
            response_threshold (float): a minimum threshold to select a response from its score
            top_k_execution_plan (int): maximum number of execution plan returned
        """
        self._llm = llm
        self._response_threshold = response_threshold
        self._top_k = top_k_execution_plan

        # Controller state variables 
        self._article = ""
        self._outline = ""
        self._iteration = 0
```

## `get_plan`

Next, we'll define the `get_plan` function. The signature for this function is as follows.


```python
def get_plan(self, context: AgentContext, chains: List[Chain], budget: Budget) -> List[ExecutionUnit]:
```

As such, Council's only expectation is that our implementation needs to return a list of `ExecutionUnits`.

An `ExecutionUnit` specifies a Chain to be executed, and an **initial state** for the execution. As we'll see, these initial states will allow us to pass the Controller's state variables to the Skills we defined previously.

Let's proceed by definining the prompts that our Controller will use to generate its plan.


```python
system_prompt = "You are the Controller module for an AI assistant built to write and revise research articles."

main_prompt_template = Template("""
# Task Description
Your task is to decide how best to write or revise the ARTICLE. Considering the ARTICLE OUTLINE, ARTICLE, and the CONVERSATION HISTORY,
use your avaiable CHAINS to decide what steps to take next. You are not responsible for writing any sections,
you are only responsible for deciding what to do next. You will delegate work to other agents via CHAINS.

# Instructions

You may delegate work to one or more CHAINS.
Consider the name and description of each chain and decide whether or how you want to use it. 
Only give instructions to relevant chains.
You can decide to invoke the same chain multiple times, with different instructions. 
Provide chain instructions that are relevant towards completing your TASK.
You will also give each chain invocation a score out of 10, so that their execution can be prioritized.

## CHAINS (provided as a list of chain names and descriptions)
$chains

## CONVERSATION HISTORY
$conversation_history

## ARTCILE OUTLINE
$outline

## ARTICLE
$article

# Contoller Decision formatted precisely as: {chain name};{score out of 10};{instructions on a single line}
""")
```

Next, we'll use the `context` and the Controller's state variables to fill in the main prompt template.


```python
# Increment iteration
self._iteration += 1

# Get the Chain details
chain_details = "\n ".join(
    [f"name: {c.name}, description: {c.description}" for c in chains]
)

# Get the conversation history
conversation_history = [f"{m.kind}: {m.message}" for m in context.chatHistory.messages]

messages = [
    LLMMessage.system_message(system_prompt),
    LLMMessage.user_message(
        main_prompt_template.substitute(
            chains=chain_details,
            outline=self._outline,
            article=self._article,
            conversation_history=conversation_history,
        )
    ),
]
```

Next we post a chat request to the LLM with our formatted messages:


```python
response = self._llm.post_chat_request(messages)[0]
```

The next step is to parse the LLM's response and create a plan, i.e. a list of `ExecutionUnits`. 

We'll first define a class-level helper function `parse_line` to parse each line of the LLM's response:


```python
@staticmethod
def parse_line(line: str, chains: List[Chain]) -> Option[Tuple[Chain, int, str]]:
    result: Option[Tuple[Chain, int]] = Option.none()
    try:
        (name, score, instruction) = line.split(";")[:3]
        chain = next(filter(lambda item: item.name == name, chains))
        result = Option.some((chain, int(score), instruction))
    except Exception as e:
        logger.error(f"Controller parsing error: {e}.\n{line}")
    finally:
        return result
```

And we proceed with the implementation of the `get_plan` function:


```python
parsed = response.splitlines()
parsed = [p for p in parsed if len(p) > 0]
parsed = [self.parse_line(line, chains) for line in parsed] 
```

After parsing each line in of the LLM's response, we filter responses based on the Controllers response threshold:


```python
filtered = [
    r.unwrap() for r in parsed if r.is_some() and r.unwrap()[1] > self._response_threshold
]

if (filtered is None) or (len(filtered) == 0):
    return []
```

If the filtered, parsed responses are non-empty, we complete the implementation by creating a list of `ExecutionUnits`.

Notice, in particular, how we are preparing `initial_state`. Since every ChatMessage has a required `message` parameter, we'll use this to carry the Controller's instructions for each Chain in its plan. We can then pack the other state variables into the `data` parameter using a dictionary.

In your own custom Controller, you could choose to use the `message` and `data` fields differently. For example, you could choose to include the instructions in the `data` object instead of using `message`. 


```python
filtered.sort(key=lambda item: item[1], reverse=True)

result = []
for chain, score, instruction in filtered: 

    # Prepare initial state to be readable by
    # first Skills in an invoked chain.
    initial_state = ChatMessage.chain(
        message=instruction, 
        data={
            "article": self._article, 
            "outline": self._outline, 
            "iteration": self._iteration
        }
    )

    exec_unit = ExecutionUnit(
        chain,
        budget,
        initial_state,
        name=f"{chain.name}: {instruction}"
    )
    result.append(exec_unit)

result = result[: self._top_k]
return result
```

## `select_responses`

Now we will implement the `select_responses` function. This function will be invoked automatically after a plan has been executed and the responses have been evaluated. This function defines the last step performed by an Agent before either: 
1. A response is returned to the calling agent or user
2. No response is selected and the Agent will continue handling the request by generating a new plan

In this example application, we'll leverage Council's flexibility to add highly customized logic here. Since we may be invoking the same Chain multiple times in parallel using different instructions, each response may contain a different part of the article we want to return to the user. To work towards a complete article, we can add logic here to not only select, but also *aggregate* multiple responses. 

We'll start by accessing all the reponses from the most recent evaluation round and filter down to the ones that were generated *in the most recent Controller iteration*.


```python
def select_responses(self, context: AgentContext) -> List[ScoredChatMessage]:

    """
    Aggregation phase. 

    Get latest iteration results from Evaluator and aggregate if applicable.
    """

    all_eval_results = sorted(context.evaluationHistory[-1], key=lambda x: x.score, reverse=True)
    current_iteration_results = []
    for scored_result in all_eval_results:
        message = scored_result.message
        if message.data['iteration'] == self._iteration:
            current_iteration_results.append(message)
```

Next, we'll define two aggregation steps, one for article outlines and another for article sections. First we partition responses based on the Skill that generated them.


```python
## If multiple outlines or articles were generated in the last iteration, 
## use LLM calls to aggregate them.

outlines = []
articles = []
chat_history = [f"{m.kind}: {m.message}" for m in context.chatHistory.messages]

for message in current_iteration_results:
    source = message.source
    if source == "SectionWriterSkill":
        articles.append(message.data['article'])
    elif source == "OutlineWriterSkill":
        outlines.append(message.data['outline'])
```

Then we use an LLM call to aggregate outlines, if there were more than one.

### Outline Aggregation


```python
system_prompt = """You are an expert-level AI writing editor. 
Your role is to aggregate multiple suggestions for an article outline into a single one."""

main_prompt_template = Template("""
# Task Description
Your task is to combine one or more article outlines into a single one written in markdown format.

# Instructions
Read the CHAT HISTORY and POSSIBLE OUTLINES. Then respond with a single article outline that best matches what is being requested in the CHAT HISTORY.

## CHAT HISTORY
$chat_history

## POSSIBLE OUTLINES
$possible_outlines

## OUTLINE
""")

if len(outlines) > 1:
    messages = [
        LLMMessage.system_message(system_prompt),
        LLMMessage.user_message(
            main_prompt_template.substitute(
                chat_history=chat_history,
                possible_outlines = outlines
            )
        ),
    ]
    response = self._llm.post_chat_request(messages)[0]
    self._outline = response
elif len(outlines) == 1:
    self._outline = outlines[0]
```

And we use another LLM call to aggregate article sections, if there were more than one.

### Article Aggregation


```python
system_prompt = "You are an expert-level AI writing editor. Your role is to aggregate multiple partial articles into a single, complete article."
main_prompt_template = Template("""
# Task Description
Your task is to combine one or more partial articles into a single one written in markdown format.

# Instructions
Read the CHAT HISTORY and PARTIAL ARTICLES. Then respond with a single article that best matches what is being requested in the CHAT HISTORY.

## CHAT HISTORY
$chat_history

## PARTIAL ARTICLES
$partial_articles

## ARTICLE
""")

if len(articles) > 1:
    messages = [
        LLMMessage.system_message(system_prompt),
        LLMMessage.user_message(
            main_prompt_template.substitute(
                chat_history=chat_history,
                partial_articles = articles
            )
        ),
    ]
    response = self._llm.post_chat_request(messages)[0]
    self._article = response
elif len(articles) == 1:
    self._article = articles[0]
```

The final step in our implementation of `select_responses` is to determine whether to return the (aggregated) article to the user or to go for another iteration. 

### Iteration Decision


```python
### Decide whether to keep iterating or to return the article
### to the user for review.

system_prompt = """You are an expert-level AI writing editor. 
Your role is to decide whether to keep editing the ARTICLE."""

main_prompt_template = Template("""
# Task Description
Your task is to decide whether:
1. To keep editing the ARTICLE, or
2. To return the article to the requesting agent.

# Instructions
Read the ARTICLE and CHAT HISTORY then consider the following instructions:
- If the ARTICLE still has placeholders or empty sections, KEEP EDITING.
- If the ARTICLE is incoherent, KEEP EDITING.
- If the ARTICLE does not include everything being requested in the CHAT HISTORY, KEEP EDITING.
- If the ARTICLE does not include every section in ARTICLE OUTLINE, KEEP EDITING.
- The ARTICLE is only COMPLETE when it covers every section and subsection in the ARTICLE OUTLINE.
- If the ARTICLE is COMPLETE, RETURN TO REQUESTING AGENT.

## ARTCILE OUTLINE
$outline

## ARTICLE
$article

## CHAT HISTORY
$chat_history

# Your Response (exactly one of ["KEEP EDITING", "RETURN TO REQUESTING AGENT"])
""")

messages = [
    LLMMessage.system_message(system_prompt),
    LLMMessage.user_message(
        main_prompt_template.substitute(
            article=self._article,
            outline=self._outline,
            chat_history=chat_history,
        )
    ),
]

response = self._llm.post_chat_request(messages)[0]
logger.debug(f"llm response: {response}")

if "KEEP EDITING" in response:
    return []
else:
    return [ScoredChatMessage(ChatMessage(message=self._article, kind=ChatMessageKind.Agent), 1.0)]
```

## Complete Controller implementation


```python
from council.contexts import AgentContext, ScoredChatMessage, ChatMessage, ChatMessageKind
from council.chains import Chain
from council.llm import LLMMessage, LLMBase
from council.utils import Option
from council.runners import Budget
from council.controllers import ControllerBase, ExecutionUnit

import logging
from string import Template
from typing import List, Tuple

logger = logging.getLogger(__name__)

class WritingAssistantController(ControllerBase):
    """
    A controller that uses an LLM to decide the execution plan
    """

    _llm: LLMBase

    def __init__(
        self,
        llm: LLMBase,
        response_threshold: float = 0,
        top_k_execution_plan: int = 5,
    ):
        """
        Initialize a new instance

        Parameters:
            llm (LLMBase): the instance of LLM to use
            response_threshold (float): a minimum threshold to select a response from its score
            top_k_execution_plan (int): maximum number of execution plan returned
        """
        self._llm = llm
        self._response_threshold = response_threshold
        self._top_k = top_k_execution_plan

        # Controller state variables 
        self._article = ""
        self._outline = ""
        self._iteration = 0

    def get_plan(
        self, context: AgentContext, chains: List[Chain], budget: Budget
    ) -> List[ExecutionUnit]:
        
        """
        Planning phase.
        """

        system_prompt = "You are the Controller module for an AI assistant built to write and revise research articles."

        main_prompt_template = Template("""
        # Task Description
        Your task is to decide how best to write or revise the ARTICLE. Considering the ARTICLE OUTLINE, ARTICLE, and the CONVERSATION HISTORY,
        use your avaiable CHAINS to decide what steps to take next. You are not responsible for writing any sections,
        you are only responsible for deciding what to do next. You will delegate work to other agents via CHAINS.

        # Instructions

        You may delegate work to one or more CHAINS.
        Consider the name and description of each chain and decide whether or how you want to use it. 
        Only give instructions to relevant chains.
        You can decide to invoke the same chain multiple times, with different instructions. 
        Provide chain instructions that are relevant towards completing your TASK.
        You will also give each chain invocation a score out of 10, so that their execution can be prioritized.

        ## CHAINS (provided as a list of chain names and descriptions)
        $chains

        ## CONVERSATION HISTORY
        $conversation_history

        ## ARTCILE OUTLINE
        $outline

        ## ARTICLE
        $article

        # Contoller Decision formatted precisely as: {chain name};{score out of 10};{instructions on a single line}
        """)

        # Increment iteration
        self._iteration += 1

        # Get the Chain details
        chain_details = "\n ".join(
            [f"name: {c.name}, description: {c.description}" for c in chains]
        )

        # Get the conversation history
        conversation_history = [f"{m.kind}: {m.message}" for m in context.chatHistory.messages]

        messages = [
            LLMMessage.system_message(system_prompt),
            LLMMessage.user_message(
                main_prompt_template.substitute(
                    chains=chain_details,
                    outline=self._outline,
                    article=self._article,
                    conversation_history=conversation_history,
                )
            ),
        ]

        response = self._llm.post_chat_request(messages)[0]
        logger.debug(f"llm response: {response}")

        parsed = response.splitlines()
        parsed = [p for p in parsed if len(p) > 0]
        parsed = [self.parse_line(line, chains) for line in parsed]

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
                message=instruction, data={"article": self._article, "outline": self._outline, "iteration": self._iteration}
            )
            exec_unit = ExecutionUnit(
                chain,
                budget,
                initial_state=initial_state,
                name=f"{chain.name}: {instruction}"
            )
            result.append(exec_unit)

        result = result[: self._top_k]
        return result

    @staticmethod
    def parse_line(line: str, chains: List[Chain]) -> Option[Tuple[Chain, int, str]]:
        result: Option[Tuple[Chain, int]] = Option.none()
        try:
            (name, score, instruction) = line.split(";")[:3]
            chain = next(filter(lambda item: item.name == name, chains))
            result = Option.some((chain, int(score), instruction))
        except Exception as e:
            print(e)
            logger.error(f"Controller parsing error: {e}.\n{line}")
        finally:
            return result
        
    def select_responses(self, context: AgentContext) -> List[ScoredChatMessage]:

        """
        Aggregation phase. 

        Get latest iteration results from Evaluator and aggregate if applicable.
        """

        all_eval_results = sorted(context.evaluationHistory[-1], key=lambda x: x.score, reverse=True)
        current_iteration_results = []
        for scored_result in all_eval_results:
            message = scored_result.message
            if message.data['iteration'] == self._iteration:
                current_iteration_results.append(message)

        ## If multiple outlines or articles were generated in the last iteration, 
        ## use LLM calls to aggregate them.

        outlines = []
        articles = []
        conversation_history = [f"{m.kind}: {m.message}" for m in context.chatHistory.messages]

        for message in current_iteration_results:
            source = message.source
            if source == "SectionWriterSkill":
                articles.append(message.data['article'])
            elif source == "OutlineWriterSkill":
                outlines.append(message.data['outline'])

        ### Outline Aggregation

        system_prompt = "You are an expert-level AI writing editor. Your role is to aggregate multiple suggestions for an article outline into a single one."
        main_prompt_template = Template("""
        # Task Description
        Your task is to combine one or more article outlines into a single one written in markdown format.

        # Instructions
        Read the CHAT HISTORY and POSSIBLE OUTLINES. Then respond with a single article outline that best matches what is being requested in the CHAT HISTORY.

        ## CONVERSATION HISTORY
        $conversation_history

        ## POSSIBLE OUTLINES
        $possible_outlines

        ## OUTLINE
        """)

        if len(outlines) > 1:
            messages = [
                LLMMessage.system_message(system_prompt),
                LLMMessage.user_message(
                    main_prompt_template.substitute(
                        conversation_history=conversation_history,
                        possible_outlines = outlines
                    )
                ),
            ]
            response = self._llm.post_chat_request(messages)[0]
            self._outline = response

        ### Article Aggregation

        system_prompt = "You are an expert-level AI writing editor. Your role is to aggregate multiple partial articles into a single, complete article."
        main_prompt_template = Template("""
        # Task Description
        Your task is to combine one or more partial articles into a single one written in markdown format.

        # Instructions
        Read the CHAT HISTORY and PARTIAL ARTICLES. Then respond with a single article that best matches what is being requested in the CHAT HISTORY.

        ## CONVERSATION HISTORY
        $conversation_history

        ## PARTIAL ARTICLES
        $partial_articles

        ## ARTICLE
        """)

        if len(articles) > 1:
            messages = [
                LLMMessage.system_message(system_prompt),
                LLMMessage.user_message(
                    main_prompt_template.substitute(
                        conversation_history=conversation_history,
                        partial_articles = articles
                    )
                ),
            ]
            response = self._llm.post_chat_request(messages)[0]
            self._article = response

        ### Decide whether to keep iterating or to return the article
        ### to the user for review.

        system_prompt = "You are an expert-level AI writing editor. Your role is to decide whether to keep editing the ARTICLE."
        main_prompt_template = Template("""
        # Task Description
        Your task is to decide whether:
        1. To keep editing the ARTICLE, or
        2. To return the article to the requesting agent.

        # Instructions
        Read the ARTICLE and CHAT HISTORY then consider the following instructions:
        - If the ARTICLE still has placeholders or empty sections, KEEP EDITING.
        - If the ARTICLE is incoherent, KEEP EDITING.
        - If the ARTICLE does not include everything being requested in the CHAT HISTORY, KEEP EDITING.
        - If the ARTICLE does not include every section in ARTICLE OUTLINE, KEEP EDITING.
        - The ARTICLE is only COMPLETE when it covers every section and subsection in the ARTICLE OUTLINE.
        - If the ARTICLE is COMPLETE, RETURN TO REQUESTING AGENT.

        ## ARTCILE OUTLINE
        $outline

        ## ARTICLE
        $article

        ## CONVERSATION HISTORY
        $conversation_history

        # Your Response (exactly one of ["KEEP EDITING", "RETURN TO REQUESTING AGENT"])
        """)

        messages = [
            LLMMessage.system_message(system_prompt),
            LLMMessage.user_message(
                main_prompt_template.substitute(
                    article=self._article,
                    outline=self._outline,
                    conversation_history=conversation_history,
                )
            ),
        ]

        response = self._llm.post_chat_request(messages)[0]
        logger.debug(f"llm response: {response}")

        if "KEEP EDITING" in response:
            return []
        else:
            return [ScoredChatMessage(ChatMessage(message=self._article, kind=ChatMessageKind.Agent), 1.0)]
```
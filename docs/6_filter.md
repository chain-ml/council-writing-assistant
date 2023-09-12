# Creating a customized Filter

In Council, **Filters** are responsible to filter the previously evaluated/scored message, i.e. for unwanted content. 

However, for your use case, we will use the filter as an opportunity to consolidate the different section of the article, provided by the different chains, into on one response.
While this is not the intended use of the filter, our implementation will still follow the same contract.

We start by extending the FilterBase, which specifies we need to implement one function: `_execute`.
Note that `AppState` parameter in the constructor, which is used to share state variable between the filter and the controller.

```python
import logging
from string import Template
from typing import List

from council.contexts import AgentContext, ChatMessage, ChatMessageKind, LLMContext, ScoredChatMessage
from council.filters import FilterBase
from council.llm import LLMBase, LLMMessage

from controller import AppState

logger = logging.getLogger("council")


class WritingAssistantFilter(FilterBase):
    def __init__(self, llm: LLMBase, state: AppState):
        super().__init__()
        self.state = state
        self._llm = self.new_monitor("llm", llm)
```


## `execute`

This function will be invoked automatically after a plan has been executed and the responses have been evaluated. This function defines the last step performed by an Agent before either: 
1. A response is returned to the calling agent or user
2. No response is selected and the Agent will continue handling the request by generating a new plan

In this example application, we'll leverage Council's flexibility to add highly customized logic here. Since we may be invoking the same Chain multiple times in parallel using different instructions, each response may contain a different part of the article we want to return to the user. To work towards a complete article, we can add logic here to not only select, but also *aggregate* multiple responses. 

We'll start by accessing all the reponses from the most recent evaluation round and filter down to the ones that were generated *in the most recent Controller iteration*.


```python
def _execute(self, context: AgentContext) -> List[ScoredChatMessage]:

    """
    Aggregation phase.

    Get latest iteration results from Evaluator and aggregate if applicable.
    """

    all_eval_results = sorted(context.evaluation, key=lambda x: x.score, reverse=True)
    current_iteration_results = []
    for scored_result in all_eval_results:
        message = scored_result.message
        if message.data['iteration'] == self.state.iteration:
            current_iteration_results.append(message)
```

Next, we'll define two aggregation steps, one for article outlines and another for article sections. First we partition responses based on the Skill that generated them.


```python
## If multiple outlines or articles were generated in the last iteration,
## use LLM calls to aggregate them.

outlines = []
articles = []
conversation_history = [f"{m.kind}: {m.message}" for m in context.chat_history.messages]

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
Read the CHAT HISTORY, EXISTING OUTLINE, and POSSIBLE OUTLINES. Then respond with a single article outline that best combines the POSSIBLE OUTLINES.

## CONVERSATION HISTORY
$conversation_history

## EXISTING OUTLINE
$existing_outline

## POSSIBLE OUTLINES
$possible_outlines

## OUTLINE
```markdown
""")

if len(outlines) > 0:
    messages = [
        LLMMessage.system_message(system_prompt),
        LLMMessage.user_message(
            main_prompt_template.substitute(
                conversation_history=conversation_history,
                existing_outline=self.state.outline,
                possible_outlines=outlines
            )
        ),
    ]
    llm_result = self._llm.inner.post_chat_request(
        LLMContext.from_context(context, self._llm),
        messages=messages
    )
    response = llm_result.first_choice
    self.state.outline = response
```

And we use another LLM call to aggregate article sections, if there were more than one.

### Article Aggregation


```python
system_prompt = "You are an expert-level AI writing editor. Your role is to aggregate multiple partial articles into a single, complete article."
main_prompt_template = Template("""
# Task Description
Your task is to combine one or more partial articles into a single one written in markdown format.

# Instructions
Read the CHAT HISTORY, ARTICLE OUTLINE, EXISTING ARTICLE, and PARTIAL ARTICLES. 
Then respond with a single article that best combines and expands the PARTIAL ARTICLES.
The resulting ARTICLE should include all sections and subsections in the ARTICLE OUTLINE.

## CONVERSATION HISTORY
$conversation_history

## ARTICLE OUTLINE
$article_outline
                                
## EXISTING ARTICLE
$existing_article
                                
## PARTIAL ARTICLES
$partial_articles

## ARTICLE
```markdown
""")

if len(articles) > 0:
    messages = [
        LLMMessage.system_message(system_prompt),
        LLMMessage.user_message(
            main_prompt_template.substitute(
                conversation_history=conversation_history,
                article_outline=self.state.outline,
                existing_article=self.state.article,
                partial_articles=articles
            )
        ),
    ]
    llm_result = self._llm.inner.post_chat_request(
        context=LLMContext.from_context(context, self._llm),
        messages=messages)
    self.state.article = llm_result.first_choice
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

You will use a CHECK LIST to determine whether to KEEP EDITING.

# Instructions
Consider every item in the CHECK LIST.
If any item is true, KEEP EDITING.
You must be careful and accurate when completing the CHECK LIST.                    

# CHECK LIST
- If the ARTICLE still has placeholders or empty sections, KEEP EDITING.
- If the ARTICLE is incoherent, KEEP EDITING.
- If there are ARTICLE subsections with fewer than three paragraphs, KEEP EDITING.
- If the ARTICLE does not include everything being requested in the CHAT HISTORY, KEEP EDITING.
- If the ARTICLE does not include every section and subsection in ARTICLE OUTLINE, KEEP EDITING.
- WORD COUNT: What is the ARTICLE's word count?
- If the WORD COUNT is less than 1500 words, KEEP EDITING.
- SECTIONS and SUBSECTIONS: Does the ARTICLE contain every section and subsection in the ARTICLE OUTLINE?
- If the ARTICLE is missing SECTIONS or SUBSECTIONS from the ARTICLE OUTLINE, KEEP EDITING.
- If the ARTICLE has any sections or subsections with fewer than three detailed paragraphs, KEEP EDITING.

## ARTICLE OUTLINE
$outline

## ARTICLE
<article>
$article
</article>
                                
## CONVERSATION HISTORY
$conversation_history

# Your Response (a list of all CHECK LIST results followed by exactly one of ["KEEP EDITING", "RETURN TO REQUESTING AGENT"])
""")

messages = [
    LLMMessage.system_message(system_prompt),
    LLMMessage.user_message(
        main_prompt_template.substitute(
            article=self.state.article,
            outline=self.state.outline,
            conversation_history=conversation_history,
        )
    ),
]

llm_result = self._llm.inner.post_chat_request(
    context=LLMContext.from_context(context, self._llm),
    messages=messages)
response = llm_result.first_choice
logger.debug(f"outline: {self.state.outline}")
logger.debug(f"article: {self.state.article}")
logger.debug(f"controller editing decision: {response}")

if "KEEP EDITING" in response and context.iteration_count < 2:
    return []
else:
    return [ScoredChatMessage(ChatMessage(message=self.state.article, kind=ChatMessageKind.Agent), 1.0)]
```

## Complete Filter implementation


```python
        messages = [
            LLMMessage.system_message(system_prompt),
            LLMMessage.user_message(
                main_prompt_template.substitute(
                    article=self.state.article,
                    outline=self.state.outline,
                    conversation_history=conversation_history,
                )
            ),
        ]

        llm_result = self._llm.inner.post_chat_request(
            context=LLMContext.from_context(context, self._llm),
            messages=messages)
        response = llm_result.first_choice
        logger.debug(f"outline: {self.state.outline}")
        logger.debug(f"article: {self.state.article}")
        logger.debug(f"controller editing decision: {response}")

        if "KEEP EDITING" in response and context.iteration_count < 2:
            return []
        else:
            return [ScoredChatMessage(ChatMessage(message=self.state.article, kind=ChatMessageKind.Agent), 1.0)]
```

## Next Steps

In the next and final section, we'll put everything together into an [Agent](./7_agent.md).

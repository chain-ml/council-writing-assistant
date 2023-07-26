# Advanced Tutorial: Creating a research writing assistant with Council

**Heads up!** If you want to skip to the end and try out the finished code, you can find it in this [repository](https://github.com/chain-ml/council-writing-assistant).

Council is an agent-based framework for composable AI. It provides an opinionated but flexible set of abstractions that encourages the division of AI tasks into more specialized functions and roles. This tutorial is the first in a series that will explore how Council can be used to create a powerful research assistant. Over the next few weeks, we will extend the tutorial with lots of new features. If you haven't read the **Getting Started** material, we recommend going back to read those first. 

## Motivation
Suppose that you want to ask an LLM to "Write a research article about the history of video games." This is quite a high-level goal to give an LLM. That said, GPT-4 will handle this by writing a coherent article with around 10 top level sections consisting of one paragaraph each. While certainly impressive, we think that GPT-4 and other LLMs can do better and go further with a little bit of *planning*. Using Council, and especially the **Controller** abstraction, we can implement a custom agent that leverages planning to write more detailed articles. 

## Solution Architecture

In this first tutorial, we're going to start relatively simply and build a single Agent with just two Chains (with only one skill each) - one for writing article outlines (planning) and another for writing article sections (writing). For now, we won't define any additional skills that could be useful for research (e.g. web search) - but we'll add these later in this tutorial series, so stay tuned. Instead, we're going to focus on leveraging the **Controller** abstraction to enable iterative planning and refinement. 

As such, our solution will have these components:
- Two Skills: `OutlineWriterSkill` and `SectionWriterSkill`
- Two Chains (with one Skill each): `outline_chain` and `writer_chain`
- A customized Controller: `WritingAssistantController`
- A (minimally) customized Evaluator: `BasicEvaluatorWithSource`

Before diving into the code, let's take a look at our solution architecture. Dotted lines indicate conditional/flexible flow, while solid lines always execute.

<img src="img/mermaid-diagram-2023-07-25-145533.svg" alt="SVG Image" width=600>

**User Messages** will first be handled by the Controller - specifically its `get_plan` function. It uses an LLM call to create an execution plan that involves its Chains. In contrast to Council's built-in LLMController, our custom Controller will generate an execution plan that includes **instructions** and other **state values**. In other words, the Controller will decide not only which Chains to add to the execution plan, but also *how* to execute them. 

For example, in an Agent's first iteration of handling a User Message, it may only return a plan to invoke `ArticleOutlineWriter`. In the second iteration, the Controller may return a plan to invoke the `ArticleSectionWriter` many times, each with instructions for different sections to write. 

After Chains and their underlying Skills have been executed according to the Controller's plan, they will passed into an Evaluator. In this tutorial installment, we're using a very minimally customized `BasicEvaluator` - the small change will be explained later. As such, the Evaluator is effectively a pass-through for now. In the coming weeks, we'll show how customized Evalutors can significantly increase the quality of generated articles - so stay tuned for that, too!

After Evaluation is complete, the Controller's `select_responses` function is always invoked. This function is responsible for interpreting the Evaluator's input and deciding whether to return a result to the "requesting agent" (which could be a human user or another Council agent). In this solution, an LLM call is used to review all of the progress made so far and decide whether to `KEEP EDITING` or to `RETURN ARTICLE`. 

## Examples

## Next Steps

The remainder of this tutorial breaks down the [solution](https://github.com/chain-ml/council-writing-assistant) sequentially:
1. Outline Writer Skill
2. Section Writer Skill
3. Controller
4. Evaluator
5. Agent App
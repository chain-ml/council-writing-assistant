# council-writing-assistant

A customized Research Writing Assistant implemented in [Council](https://github.com/chain-ml/council).

## Overview

This repository provides a reference implementation of a Research Writing Assistant implemented as an Agent in [Council](https://github.com/chain-ml/council).

### What does this Agent do?

Given a high-level research task, e.g.

```
> Write a detailed research article about the history of box manufacturing.
```
the Agent produces a complete [article](./docs/example_article.md) in response. Compare this to an [article](./docs/example_article_gpt4.md) produced by GPT-4 using the same prompt.

## Tutorial

For a complete tutorial that breaks down the design and implementation of the Research Writing Assistant, please visit the [docs](./docs) directory.

## Requirements

A Python environment with council 0.0.11 installed, i.e.
`pip install council-ai==0.0.11`

Rename the file `.env.example` to `.env` and fill in your **OpenAI API key** and required **budget** in seconds for a single agent run.

## Running the Agent

### Jupyter Notebook
Create and interact with an Agent using `run_agent.ipynb`. This notebook implements the Agent developed in the [tutorial](./docs).

### Command Line App
Interact with a ResearchWritingAssistant Agent on your command line by running `python run_agent.py`

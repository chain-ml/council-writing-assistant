# council-writing-assistant

A customized Research Writing Assistant implemented in [Council](https://github.com/chain-ml/council).

## Overview

This repository provides a reference implementation of a Research Writing Assistant implemented as an Agent in [Council](https://github.com/chain-ml/council).

### What does this Agent do?

Given a high-level research task, e.g.

```
> Write a detailed research article about the history of video games.
```
the Agent produces a complete [article](./docs/example_article.md) in response.

## Tutorial

For a complete tutorial that breaks down the design and implementation of the Research Writing Assistant, please visit the [docs](./docs) directory.

## Requirements

A Python environment with council 0.0.7 installed, i.e.
`pip install council-ai==0.0.7`

Rename the file `.env.example` to `.env` and fill in your OpenAI API key.

## Running the Agent

Create and interact with an Agent using `run_agent.ipynb`. This notebook implements the Agent developed in the [tutorial](./docs).

A standalone Python CLI app will be added soon!
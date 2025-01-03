# MinMod Dashboard

<div align="center">

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/usc-isi-i2/minmod-webapp.svg)](https://github.com/usc-isi-i2/minmod-webapp/issues)
[![Docker](https://img.shields.io/docker/automated/jrottenberg/ffmpeg.svg?maxAge=2592000)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/usc-isi-i2/minmod-webapp/blob/main/LICENSE)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)

</div>

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)

## Introduction

The MinMod Dashboard is a web app for analyzing and visualizing mineral site data. It features tools to view site statistics, map distributions, explore grade tonnage models, and download data. Users can review mineral data in tables or perform advanced searches with SPARQL queries. This platform simplifies decision-making and resource management with an all-in-one solution.


<!-- For more documentation, please see [not available yet](). -->

## Installation

```bash
pip install poetry
poetry install
```

## Usage

Install [docker](https://docs.docker.com/engine/installation/) and build the image:

```bash
docker compose build
```

The container of the dashboard will be created and run from the [ta2-minmod-kg](https://github.com/DARPA-CRITICALMAAS/ta2-minmod-kg/blob/main/docker-compose.yml) docker compose.

Otherwise, for the standalone web service:

```bash
source activate .venv/bin/activate
python app.py
```

Visit [http://localhost:8050](http://localhost:8050)


## Tests

```
To Do.
```

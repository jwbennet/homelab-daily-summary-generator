# Daily Summary Generator

This project pulls information from the Microsoft Graph API and the [Weather API](https://www.weatherapi.com/) to generate a JSON file containing a summary of my daily activities. This file is then uploaded to a GCP storage bucket for use by the rendering process.

## Requirements

* Python 3.9 or newer
* Pipenv version 2022.1.8 or newer

## Building the project

The Makefile in the project contains helpers for typical building scenarios.

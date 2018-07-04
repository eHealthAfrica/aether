---
title: Aether - API - Introduction
permalink: documentation/developers/api.html
---


# Using the Aether API

Both the Kernel and the ODK module use the [Django REST Framework](http://www.django-rest-framework.org/) to provide a number of REST API endpoints that can be used for CRUD operations on the data they handle. When accessed from the browser, these endpoints provide a simple UI that can be useful for testing API calls, or for direct access and manipulation of the data.

## Authentication

You have two options for authentication: Basic (username/password) or Token. It is best practice to create a special API user, which you can do by accessing the default Django admin screens. For this, you will need the admin password. Admin passwords for each server (in this case, Kernel and ODK) are set at deploy time with environment variables. Using this password, access the admin area for the server you're interested in and create new user called `api`. You can then use the credentials for basic auth or, if you prefer, generate a token for this user. Bear in mind that if you want to access API endpoints on both servers, you will need to create two separate users.

## Endpoints

### Kernel



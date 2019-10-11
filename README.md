<p align="center">
  <a href="https://github.com/torchbox/wagtail-grapple">
    <img src="https://github.com/torchbox/wagtail-grapple/raw/master/.github/wagtail-grapple.svg?sanitize=true" alt="A red g with a grapple hook" width="80" height="80">
  </a>

  <h3 align="center">Wagtail Grapple <a href="https://pypi.org/project/wagtail-grapple/"><img src="https://img.shields.io/pypi/v/wagtail-grapple.svg"></a> <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg"></a></h3>

  <p align="center">
    A library to build GraphQL endpoints easily so you can grapple your Wagtail data from anywhere!
    <br />
    <br/>
    <a href="https://wagtail-grapple.readthedocs.io/en/latest/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/torchbox/wagtail-grapple#about-the-project">View Demo</a>
    ·
    <a href="https://github.com/torchbox/wagtail-grapple/issues">Report Bug</a>
    ·
    <a href="https://github.com/torchbox/wagtail-grapple/issues">Request Feature</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
* [Contributing](#contributing)
* [Compatibility](#compatibility)
* [License](#license)
* [Contact](#contact)
* [Acknowledgements](#inspired-by)



<!-- ABOUT THE PROJECT -->
## About The Project

![GraphQL Preview Demo](docs/demo.gif)

There is a range of GraphQL packages for Python and specifically Django.
However, getting these packages to work out of the box with an existing infrastructure
without errors isn't as easy to come by.

The purpose of Grapple is to be able to build GraphQL endpoints on a model by model
basis as quickly as possible. The setup and configuration have been designed
to be as simple but also provide the best features;
No complex serializers need to be written - just add a `graphql_fields` list
to your model and away you go (although if you want to go deeper you can!).

#### Features:
* Easily create GraphQL types by adding a small annotation in your models.
* Supports traditional Wagtail models:
    - Pages (including Streamfield & Orderables)
    - Snippets
    - Images
    - Documents
    - Settings
    - Search (on all models)
* Custom Image & Document model support
* Advanced headless preview functionality buit using GraphQL Subscriptions to enable Page previews on any device!
* Gatsby Image support (both base64 and SVG tracing)! :fire:


### Built With
This library is an abstraction upon and relies heavily on Graphene & Graphene Django.
We also use Django Channels and the Potrace image library.
* [Graphene](https://github.com/graphql-python/graphene)
* [Graphene Django](https://github.com/graphql-python/graphene)
* [Django Channels](https://github.com/django/channels)
* [Potrace](https://github.com/skyrpex/potrace)


## Getting Started

Getting Grapple installed is designed to be as simple as possible!

### Prerequisites
```
Django  >= 2.2, <2.3
wagtail >= 2.5, <2.7
```

### Installation
`pip install wagtail_grapple`

<br />

Add the following to the `installed_apps` list in your Wagtail settings file:

```python
installed_apps = [
    ...
    "grapple",
    "graphene_django",
    "channels",
    ...
]
```

<br />

Add the following to the bottom of the same settings file, where each key is the app you want to this library to scan and the value is the prefix you want to give to GraphQL types (you can usually leave this blank):

```python
# Grapple Config:
GRAPHENE = {"SCHEMA": "grapple.schema.schema"}
GRAPPLE_APPS = {
    "home": ""
}
```

<br />

Add the GraphQL URLs to your `urls.py`:

```python
from grapple import urls as grapple_urls
...
urlpatterns = [
    ...
    url(r"", include(grapple_urls)),
    ...
]
```

<br/>
Done! Now you can proceed onto configuring your models to generate GraphQL types that adopt their stucture :tada:
_Your graphql endpoint is available at http://localhost:8000/graphql/_
<br/>

## Usage

Here is a GraphQL model configuration for the default page from the Wagtail docs:
```python
...
from grapple.models import (
    GraphQLString,
    GraphQLStreamfield,
)

class BlogPage(Page):
    author = models.CharField(max_length=255)
    date = models.DateField("Post date")
    body = StreamField(
        [
            ("heading", blocks.CharBlock(classname="full title")),
            ("paraagraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
        ]
    )

    content_panels = Page.content_panels + [
        FieldPanel("author"),
        FieldPanel("date"),
        StreamFieldPanel("body"),
    ]

    # Note these fields below:
    graphql_fields = [
        GraphQLString("heading"),
        GraphQLString("date"),
        GraphQLString("author"),
        GraphQLStreamfield("body"),
    ]
```

_For more examples, please refer to the [Documentation](https://wagtail-grapple.readthedocs.io/en/latest/)_



## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Local development

 - In the python environment of your choice, navigate to `/examples`
 - Run `pip install -r requirements.txt`
 - Delete the `db.sqlite3` file and run `./manage.py migrate`
 - Run server `./manage.py runserver`


## Compatibility

Wagtail Grapple supports:

- Django 2.2.x
- Python 3.6 and 3.7
- Wagtail >= 2.5

## License

Distributed under the MIT License. See `LICENSE` for more information.



## Contact

Nathan Horrigan
- [@NathHorrigan](https://github.com/NathHorrigan)
- NathHorrigan@gmail.com

Project Link: [https://github.com/torchbox/wagtail-grapple](https://github.com/torchbox/wagtail-grapple)


<!-- ACKNOWLEDGEMENTS -->
## Inspired by
* [@tr11](https://github.com/tr11)
* [@tmkn](https://github.com/tmkn)

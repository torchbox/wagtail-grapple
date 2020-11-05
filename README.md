<p align="center">
  <a href="https://github.com/GrappleGQL/wagtail-grapple">
    <img src="https://github.com/GrappleGQL/wagtail-grapple/raw/master/.github/wagtail-grapple.svg?sanitize=true" alt="A red g with a grapple hook" width="80" height="80">
  </a>

  <h3 align="center">Wagtail Grapple <a href="https://pypi.org/project/wagtail-grapple/"><img src="https://img.shields.io/pypi/v/wagtail-grapple.svg"></a> <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg"></a> <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white"></a></h3>

  <p align="center">
    A library to build GraphQL endpoints easily so you can grapple your Wagtail data from anywhere!
    <br />
    <br/>
    <a href="https://wagtail-grapple.readthedocs.io/en/latest/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/GrappleGQL/wagtail-grapple#about-the-project">View Demo</a>
    ·
    <a href="https://github.com/GrappleGQL/wagtail-grapple/issues">Report Bug</a>
    ·
    <a href="https://github.com/GrappleGQL/wagtail-grapple/issues">Request Feature</a>
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
    - Media
    - Settings
    - Redirects
    - Search (on all models)
* Custom Image & Document model support
* Pagination support
* Advanced headless preview functionality built using GraphQL Subscriptions to enable Page previews on any device!


### Built With
This library is an abstraction upon and relies heavily on Graphene & Graphene Django.
We also use Django Channels and the Potrace image library.
* [Graphene](https://github.com/graphql-python/graphene)
* [Graphene Django](https://github.com/graphql-python/graphene)
* [Potrace](https://github.com/skyrpex/potrace)
* [Django Channels](https://github.com/django/channels) when installed with `wagtail_grapple[channels]`


## Getting Started

Getting Grapple installed is designed to be as simple as possible!

### Prerequisites
```
Django  >= 2.2, <3.1 (<2.3 if using channels)
wagtail >= 2.5, <2.11
```

### Installation

```bash
pip install wagtail_grapple
```

Add the following to the `installed_apps` list in your Wagtail settings file:

```python
installed_apps = [
    ...
    "grapple",
    "graphene_django",
    ...
]
```

For GraphQL Subscriptions with Django Channels, run `pip install wagtail_grapple[channels]`  and add
`channels` to installed apps:

```python
installed_apps = [
    ...
    "grapple",
    "graphene_django",
    "channels",
    ...
]
```


Add the following to the bottom of the same settings file, where each key is the app you want to this library to scan and the value is the prefix you want to give to GraphQL types (you can usually leave this blank):

```python
# Grapple Config:
GRAPHENE = {"SCHEMA": "grapple.schema.schema"}
GRAPPLE_APPS = {
    "home": ""
}
```

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

Done! Now you can proceed onto configuring your models to generate GraphQL types that adopt their structure :tada:
_Your GraphQL endpoint is available at http://localhost:8000/graphql/_

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
            ("paragraph", blocks.RichTextBlock()),
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

 - In the python environment of your choice, navigate to `/example`
 - Run `pip install -r requirements.txt`
 - Delete the `db.sqlite3` file and run `./manage.py migrate`
 - Run server `./manage.py runserver`


## Compatibility

Wagtail Grapple supports:

- Django 2.2.x, 3.0.x
- Python 3.6, 3.7, 3.8 and 3.9
- Wagtail >= 2.5, < 2.11

## License

Distributed under the MIT License. See `LICENSE` for more information.



## Contact

Nathan Horrigan
- [@NathHorrigan](https://github.com/NathHorrigan)
- nathan.horrigan@torchbox.com

Project Link: [https://github.com/GrappleGQL/wagtail-grapple](https://github.com/GrappleGQL/wagtail-grapple)


<!-- ACKNOWLEDGEMENTS -->
## Inspired by
* [@tr11](https://github.com/tr11)
* [@tmkn](https://github.com/tmkn)

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/NathHorrigan"><img src="https://avatars3.githubusercontent.com/u/13197111?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Nathan Horrigan</b></sub></a><br /><a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=NathHorrigan" title="Code">💻</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/issues?q=author%3ANathHorrigan" title="Bug reports">🐛</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=NathHorrigan" title="Documentation">📖</a> <a href="#infra-NathHorrigan" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-NathHorrigan" title="Maintenance">🚧</a></td>
    <td align="center"><a href="https://github.com/jafacakes2011"><img src="https://avatars3.githubusercontent.com/u/4086447?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Cameron Lamb</b></sub></a><br /><a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=jafacakes2011" title="Code">💻</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/issues?q=author%3Ajafacakes2011" title="Bug reports">🐛</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=jafacakes2011" title="Documentation">📖</a> <a href="#infra-jafacakes2011" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-jafacakes2011" title="Maintenance">🚧</a></td>
    <td align="center"><a href="https://zerolab.org/"><img src="https://avatars0.githubusercontent.com/u/31622?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Dan Braghis</b></sub></a><br /><a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=zerolab" title="Code">💻</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/issues?q=author%3Azerolab" title="Bug reports">🐛</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=zerolab" title="Documentation">📖</a> <a href="#infra-zerolab" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-zerolab" title="Maintenance">🚧</a></td>
    <td align="center"><a href="https://github.com/ruisaraiva19"><img src="https://avatars2.githubusercontent.com/u/7356098?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Rui Saraiva</b></sub></a><br /><a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=ruisaraiva19" title="Code">💻</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/issues?q=author%3Aruisaraiva19" title="Bug reports">🐛</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=ruisaraiva19" title="Documentation">📖</a> <a href="#infra-ruisaraiva19" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-ruisaraiva19" title="Maintenance">🚧</a></td>
    <td align="center"><a href="https://github.com/tbrlpld"><img src="https://avatars1.githubusercontent.com/u/24797493?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Tibor</b></sub></a><br /><a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=tbrlpld" title="Code">💻</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/issues?q=author%3Atbrlpld" title="Bug reports">🐛</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=tbrlpld" title="Documentation">📖</a></td>
    <td align="center"><a href="https://github.com/timmysmalls"><img src="https://avatars2.githubusercontent.com/u/48223453?v=4?s=100" width="100px;" alt=""/><br /><sub><b>timmysmalls</b></sub></a><br /><a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=timmysmalls" title="Code">💻</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/issues?q=author%3Atimmysmalls" title="Bug reports">🐛</a></td>
    <td align="center"><a href="https://wagtail.io/"><img src="https://avatars0.githubusercontent.com/u/15543?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Tom Dyson</b></sub></a><br /><a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=tomdyson" title="Code">💻</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=tomdyson" title="Documentation">📖</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://fabien.cool/"><img src="https://avatars1.githubusercontent.com/u/1702255?v=4?s=100" width="100px;" alt=""/><br /><sub><b>fabienheureux</b></sub></a><br /><a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=fabienheureux" title="Code">💻</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/issues?q=author%3Afabienheureux" title="Bug reports">🐛</a> <a href="https://github.com/GrappleGQL/wagtail-grapple/commits?author=fabienheureux" title="Documentation">📖</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!

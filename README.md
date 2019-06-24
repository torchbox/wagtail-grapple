<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/NathHorrigan/wagtail-grapple">
    <img src="https://github.com/othneildrew/Best-README-Template/raw/master/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Wagtail Grapple</h3>

  <p align="center">
    A library to easily build GraphQL endpoints so you can grapple your wagtail data from anywhere!
    <br />
    <br/>
    <a href="https://github.com/NathHorrigan/wagtail-grapple"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/NathHorrigan/wagtail-grapple">View Demo</a>
    ·
    <a href="https://github.com/NathHorrigan/wagtail-grapple/issues">Report Bug</a>
    ·
    <a href="https://github.com/NathHorrigan/wagtail-grapple/issues">Request Feature</a>
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
* [License](#license)
* [Contact](#contact)
* [Acknowledgements](#acknowledgements)



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

There is a range of GraphQL packages for Python and sepcifically Django. 
However, Getting these packages to work out of the box with an existing infrastructure 
without errors isn't as easy to come by.

The purpose of Grapple is to be able to build GraphQL endpoints on a model by model
basis as quickly as possible. The setup and configuration have been designed 
to be as simple but also provide the best features;
No complex serliazers need to be written just add a `graphql_fields` list 
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


<!-- GETTING STARTED -->
## Getting Started

Getting Grapple installed is designed to be as simple as possible!

### Prerequisites
```
Django  >= 2.2, <2.3
wagtail >= 2.5, <2.6
```

### Installation
`pip install wagtail_grapple`

<br />

Add the following to the `installed_apps` list in your wagtail settings file:

```
installed_apps = [
    ...
    "grapple",
    "graphene_django",
    "channels",
    ...
]
```

<br />

Add the following to the bottom of the same settings file where each key is the app you want to this library to scan and the value is the prefix you want to give to GraphQL types (you can usually leave this blank):

```
# Grapple Config:
GRAPHENE = {"SCHEMA": "grapple.schema.schema"}
GRAPPLE_APPS = {
    "home": ""
}
```

<br />

Add the GraphQL urls to your `urls.py`:

```
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


<!-- USAGE EXAMPLES -->
## Usage

Here is a GraphQL model configuration for the default page from the wagtail docs:
```
class BlogPage(GrapplePageMixin, Page):
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

_For more examples, please refer to the [Documentation](https://example.com)_



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Nathan Horrigan 
- [@NathHorrigan](https://github.com/NathHorrigan) 
- NathHorrigan@gmail.com

Project Link: [https://github.com/NathHorrigan/wagtail-grapple](https://github.com/NathHorrigan/wagtail-grapple)



<!-- ACKNOWLEDGEMENTS -->
## Inspired by
* [@tr11](https://github.com/tr11)
* [@tmkn](https://github.com/tmkn)

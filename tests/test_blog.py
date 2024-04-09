import datetime
import decimal
import json

import wagtail_factories

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.test import override_settings
from django.test.client import RequestFactory
from test_grapple import BaseGrappleTest
from testapp.blocks import (
    ButtonBlock,
    CarouselBlock,
    ImageGalleryBlock,
    ImageGalleryImages,
)
from testapp.factories import (
    AdvertFactory,
    BlogPageFactory,
    PersonFactory,
    TextWithCallableBlockFactory,
)
from wagtail.blocks import CharBlock, StreamValue
from wagtail.blocks.list_block import ListBlock, ListValue
from wagtail.embeds.blocks import EmbedValue
from wagtail.rich_text import RichText


class BlogTest(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        # FIXME: change back to setUpTestData once https://github.com/wagtail/wagtail/issues/9788 is fixed
        self.richtext_sample = (
            f'Text with a \'link\' to <a linktype="page" id="{self.home.id}">Home</a>'
        )
        self.richtext_sample_rendered = (
            f"Text with a 'link' to <a href=\"{self.home.url}\">Home</a>"
        )

        objectives_list = ListValue(
            ListBlock(CharBlock()), values=["Read all of article!"]
        )
        buttons_list = ListValue(
            ListBlock(ButtonBlock()),
            values=[
                {
                    "button_text": "btn",
                    "button_link": "https://www.graphql.com/",
                }
            ],
        )
        self.empty_buttons_list = ListValue(ListBlock(ButtonBlock()), values=[])

        # Add a Blog post
        self.blog_page = BlogPageFactory(
            body=[
                ("heading", "Test heading 1"),
                (
                    "paragraph",
                    RichText(self.richtext_sample),
                ),
                ("heading", "Test heading 2"),
                ("image", wagtail_factories.ImageFactory()),
                ("decimal", decimal.Decimal(1.2)),
                ("date", datetime.date.today()),
                ("datetime", datetime.datetime.now()),
                (
                    "carousel",
                    StreamValue(
                        stream_block=CarouselBlock(),
                        stream_data=[
                            ("image", wagtail_factories.ImageChooserBlockFactory()),
                            ("image", wagtail_factories.ImageChooserBlockFactory()),
                        ],
                    ),
                ),
                (
                    "gallery",
                    {
                        "title": "Gallery title",
                        "images": StreamValue(
                            stream_block=ImageGalleryImages(),
                            stream_data=[
                                (
                                    "image",
                                    {
                                        "image": wagtail_factories.ImageChooserBlockFactory()
                                    },
                                ),
                                (
                                    "image",
                                    {
                                        "image": wagtail_factories.ImageChooserBlockFactory()
                                    },
                                ),
                            ],
                        ),
                    },
                ),
                ("callout", {"text": RichText(self.richtext_sample)}),
                ("objectives", objectives_list),
                (
                    "video",
                    {
                        "youtube_link": EmbedValue(
                            "https://www.youtube.com/watch?v=_U79Wc965vw"
                        )
                    },
                ),
                (
                    "text_and_buttons",
                    {
                        "text": "Button text",
                        "buttons": buttons_list,
                        "mainbutton": {
                            "button_text": "Take me to the source",
                            "button_link": "https://wagtail.io/",
                        },
                    },
                ),
                (
                    "block_with_name",
                    {
                        "name": "Test Name",
                    },
                ),
                ("text_with_callable", TextWithCallableBlockFactory()),
            ],
            parent=self.home,
            summary=self.richtext_sample,
            extra_summary=self.richtext_sample,
        )

    def test_blog_page(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    title
                }
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.blog_page.id})

        # Check title.
        self.assertEqual(executed["data"]["page"]["title"], self.blog_page.title)

    def test_related_author_page(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    author {
                        ... on AuthorPage {
                            name
                        }
                    }
                }
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.blog_page.id})
        page = executed["data"]["page"]["author"]
        self.assertTrue(
            isinstance(page["name"], str) and page["name"] == self.blog_page.author.name
        )

    def get_blocks_from_body(self, block_type, block_query="rawValue", page_id=None):
        query = f"""
        query($id: ID) {{
            page(id: $id) {{
                ... on BlogPage {{
                    body {{
                        blockType
                        ... on {block_type} {{
                            {block_query}
                        }}
                    }}
                }}
            }}
        }}
        """

        executed = self.client.execute(
            query, variables={"id": page_id or self.blog_page.id}
        )

        # Print the error response
        if not executed.get("data"):
            print(executed)  # noqa: T201

        blocks = []
        for block in executed["data"]["page"]["body"]:
            if block["blockType"] == block_type:
                blocks.append(block)
        return blocks

    def test_blog_body_charblock(self):
        block_type = "CharBlock"
        query_blocks = self.get_blocks_from_body(block_type)

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEqual(query_blocks[count]["rawValue"], block.value)
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEqual(len(query_blocks), count)

    def test_streamfield_richtextblock(self):
        block_type = "RichTextBlock"
        query_blocks = self.get_blocks_from_body(block_type)

        # Check the raw value.
        count = 0
        for streamfield_block in self.blog_page.body:
            if type(streamfield_block.block).__name__ == block_type:
                self.assertEqual(
                    query_blocks[count]["rawValue"], streamfield_block.value.source
                )
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEqual(len(query_blocks), count)

        # Check value.
        query_blocks = self.get_blocks_from_body(block_type, block_query="value")
        count = 0
        for streamfield_block in self.blog_page.body:
            if type(streamfield_block.block).__name__ == block_type:
                self.assertEqual(
                    query_blocks[count]["value"], self.richtext_sample_rendered
                )
                count += 1

        with override_settings(GRAPPLE={"RICHTEXT_FORMAT": "raw"}):
            query_blocks = self.get_blocks_from_body(block_type, block_query="value")
            count = 0
            for streamfield_block in self.blog_page.body:
                if type(streamfield_block.block).__name__ == block_type:
                    self.assertEqual(query_blocks[count]["value"], self.richtext_sample)

    def test_richtext(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    summary
                    stringSummary
                    extraSummary
                }
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.blog_page.id})

        # Check summary declared as GraphQLRichText
        self.assertEqual(
            executed["data"]["page"]["summary"], self.richtext_sample_rendered
        )

        # Check summary declared as GraphQLString, with custom name
        self.assertEqual(
            executed["data"]["page"]["stringSummary"], self.richtext_sample_rendered
        )

        # Check rich text field declared as GraphQLString, default field name
        self.assertEqual(
            executed["data"]["page"]["extraSummary"], self.richtext_sample_rendered
        )

        with override_settings(GRAPPLE={"RICHTEXT_FORMAT": "raw"}):
            executed = self.client.execute(query, variables={"id": self.blog_page.id})
            self.assertEqual(executed["data"]["page"]["summary"], self.richtext_sample)
            self.assertEqual(
                executed["data"]["page"]["stringSummary"], self.richtext_sample
            )
            self.assertEqual(
                executed["data"]["page"]["extraSummary"], self.richtext_sample
            )

    def test_blog_body_imagechooserblock(self):
        block_type = "ImageChooserBlock"
        query_blocks = self.get_blocks_from_body(
            block_type,
            block_query="""
            image {
                id
                src
            }
            """,
        )

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEqual(
                    query_blocks[count]["image"]["id"], str(block.value.id)
                )
                self.assertEqual(
                    query_blocks[count]["image"]["src"],
                    settings.BASE_URL + block.value.file.url,
                )
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEqual(len(query_blocks), count)

    def test_blog_body_imagechooserblock_in_streamblock(self):
        block_type = "CarouselBlock"
        query_blocks = self.get_blocks_from_body(
            block_type,
            block_query="""
                blocks {
                    ...on ImageChooserBlock {
                        image {
                            src
                        }
                    }
                }
            """,
        )

        # Get first image url
        url = query_blocks[0]["blocks"][0]["image"]["src"]

        # Check that src is valid url
        validator = URLValidator()
        try:
            # Run validator, If no exception thrown then we pass test
            validator(url)
        except ValidationError:
            self.fail(f"{url} is not a valid url")

    def test_blog_body_calloutblock(self):
        block_type = "CalloutBlock"
        query_blocks = self.get_blocks_from_body(block_type, block_query="text")

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                html = query_blocks[0]["text"]
                self.assertIsInstance(html, str)
                self.assertEqual(html, self.richtext_sample_rendered)

        with override_settings(GRAPPLE={"RICHTEXT_FORMAT": "raw"}):
            query_blocks = self.get_blocks_from_body(block_type, block_query="text")
            for block in self.blog_page.body:
                if type(block.block).__name__ == block_type:
                    html = query_blocks[0]["text"]
                    self.assertIsInstance(html, str)
                    self.assertEqual(html, self.richtext_sample)

    def test_blog_body_decimalblock(self):
        block_type = "DecimalBlock"
        query_blocks = self.get_blocks_from_body(block_type)

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEqual(query_blocks[count]["rawValue"], str(block.value))
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEqual(len(query_blocks), count)

    def test_blog_body_dateblock(self):
        block_type = "DateBlock"
        query_blocks = self.get_blocks_from_body(block_type)

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEqual(query_blocks[count]["rawValue"], str(block.value))
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEqual(len(query_blocks), count)

    def test_blog_body_datetimeblock(self):
        block_type = "DateTimeBlock"
        date_format_string = "%Y-%m-%d %H:%M:%S"
        query_blocks = self.get_blocks_from_body(
            block_type,
            block_query=f'value(format: "{date_format_string}")',
        )

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEqual(
                    query_blocks[count]["value"],
                    block.value.strftime(date_format_string),
                )
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEqual(len(query_blocks), count)

    def test_blog_body_imagegalleryblock(self):
        block_type = "ImageGalleryBlock"
        query_blocks = self.get_blocks_from_body(
            block_type,
            block_query="""
            title
            images {
                image {
                    id
                    src
                }
            }
            """,
        )

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEqual(
                    query_blocks[count]["title"], str(block.value["title"])
                )
                for key, image in enumerate(query_blocks[count]["images"]):
                    self.assertEqual(
                        image["image"]["id"],
                        str(block.value["images"][key].value["image"].id),
                    )
                    self.assertEqual(
                        image["image"]["src"],
                        settings.BASE_URL
                        + str(block.value["images"][key].value["image"].file.url),
                    )
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEqual(len(query_blocks), count)

    def test_blog_body_objectives(self):
        block_type = "ListBlock"
        query_blocks = self.get_blocks_from_body(
            block_type,
            block_query="""
            field
            items {
                ...on CharBlock {
                    value
                }
            }
            """,
        )
        # Check we have exactly one value
        self.assertEqual(len(query_blocks), 1)
        # Check that first value matches hardcoded value
        first_block = query_blocks[0]
        first_item = first_block.get("items", [])[0]
        first_value = first_item.get("value")
        self.assertEqual(first_value, "Read all of article!")

    def test_blog_embed(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    body {
                        blockType
                        ...on VideoBlock {
                            youtubeLink {
                                url
                                embed
                                rawEmbed
                                rawValue
                            }
                        }
                    }
                }
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.blog_page.id})
        body = executed["data"]["page"]["body"]

        raw_embed = {
            "title": "Wagtail Space 2018",
            "type": "video",
            "thumbnail_url": "https://i.ytimg.com/vi/_U79Wc965vw/hqdefault.jpg",
            "width": 200,
            "height": 113,
            "html": '<iframe width="200" height="113" src="https://www.youtube.com/embed/_U79Wc965vw?feature=oembed" '
            'frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; '
            'picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen '
            'title="Wagtail Space 2018"></iframe>',
        }
        for block in body:
            if block["blockType"] == "VideoBlock":
                embed = block["youtubeLink"]
                expected_raw_value = "<div>\n    {}\n</div>\n".format(embed["embed"])
                self.assertTrue(isinstance(embed["url"], str))
                self.assertEqual(embed["embed"], raw_embed["html"])
                self.assertEqual(embed["rawEmbed"], json.dumps(raw_embed))
                self.assertEqual(embed["rawValue"], expected_raw_value)
                return

        self.fail("VideoBlock type not instantiated in Streamfield")

    def test_blog_body_pagechooserblock(self):
        another_blog_post = BlogPageFactory(
            body=[("page", self.blog_page)], parent=self.home
        )
        block_type = "PageChooserBlock"
        block_query = """
        page {
            ... on BlogPage {
                date
                authors
            }
        }
        """
        query_blocks = self.get_blocks_from_body(
            block_type, block_query=block_query, page_id=another_blog_post.id
        )

        # Check output.
        count = 0
        for block in another_blog_post.body:
            if type(block.block).__name__ != block_type:
                continue

            # Test the values
            page_data = query_blocks[count]["page"]
            page = block.value
            self.assertEqual(page_data["date"], str(page.date))
            self.assertEqual(
                page_data["authors"],
                list(page.authors.values_list("person__name", flat=True)),
            )
            # Increment the count
            count += 1
        # Check that we test all blocks that were returned.
        self.assertEqual(len(query_blocks), count)

    def test_blog_body_snippetchooserblock_advert(self):
        url = "https://http.cat"
        text = "cats"
        blog_page = BlogPageFactory(
            parent=self.home,
            body=[
                (
                    "advert",
                    AdvertFactory(url=url, text=text, rich_text=self.richtext_sample),
                ),
            ],
        )
        block_type = "SnippetChooserBlock"
        block_query = """
        snippet {
            ... on Advert {
                url
                text
            }
        }
        """
        query_blocks = self.get_blocks_from_body(
            block_type, block_query=block_query, page_id=blog_page.id
        )
        block = query_blocks[0]
        self.assertEqual(block["snippet"]["url"], url)
        self.assertEqual(block["snippet"]["text"], text)

    def test_blog_body_snippetchooserblock_advert_rich_text(self):
        blog_page = BlogPageFactory(
            parent=self.home,
            body=[
                (
                    "advert",
                    AdvertFactory(
                        rich_text=self.richtext_sample,
                        extra_rich_text=self.richtext_sample,
                    ),
                ),
            ],
        )
        block_type = "SnippetChooserBlock"
        block_query = """
        snippet {
            ... on Advert {
                richText
                stringRichText
                extraRichText
            }
        }
        """
        query_blocks = self.get_blocks_from_body(
            block_type, block_query=block_query, page_id=blog_page.id
        )
        block = query_blocks[0]

        # Declared as GraphQLRichText
        self.assertEqual(block["snippet"]["richText"], self.richtext_sample_rendered)

        # Declared as GraphQLString, custom name/source
        self.assertEqual(
            block["snippet"]["stringRichText"], self.richtext_sample_rendered
        )

        # Declared as GraphQLString, default name
        self.assertEqual(
            block["snippet"]["extraRichText"], self.richtext_sample_rendered
        )

        with override_settings(GRAPPLE={"RICHTEXT_FORMAT": "raw"}):
            query_blocks = self.get_blocks_from_body(
                block_type, block_query=block_query, page_id=blog_page.id
            )
            block = query_blocks[0]
            self.assertEqual(block["snippet"]["richText"], self.richtext_sample)
            self.assertEqual(block["snippet"]["stringRichText"], self.richtext_sample)
            self.assertEqual(block["snippet"]["extraRichText"], self.richtext_sample)

    def test_blog_body_snippetchooserblock_person(self):
        name = "Jane Citizen"
        job = "Frobnicator"
        blog_page = BlogPageFactory(
            parent=self.home,
            body=[
                ("person", PersonFactory(name=name, job=job)),
            ],
        )
        block_type = "SnippetChooserBlock"
        block_query = """
        snippet {
            ... on Person {
                name
                job
            }
        }
        """
        query_blocks = self.get_blocks_from_body(
            block_type, block_query=block_query, page_id=blog_page.id
        )
        block = query_blocks[0]
        self.assertEqual(block["snippet"]["name"], name)
        self.assertEqual(block["snippet"]["job"], job)

    # Next 2 tests are used to test the Collection API, both ForeignKey and nested field extraction.
    def test_blog_page_related_links(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    relatedLinks {
                        url
                    }
                }
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.blog_page.id})

        links = executed["data"]["page"]["relatedLinks"]
        self.assertEqual(len(links), 5)
        for link in links:
            url = link.get("url", None)
            self.assertTrue(isinstance(url, str))

    def test_blog_page_related_urls(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    relatedUrls
                }
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.blog_page.id})

        links = executed["data"]["page"]["relatedUrls"]
        self.assertEqual(len(links), 5)
        for url in links:
            self.assertTrue(isinstance(url, str))

    def test_blog_page_paginated_authors(self):
        page = 1
        per_page = 5

        query = """
        query ($id: ID, $page: PositiveInt, $perPage: PositiveInt) {
            page(id: $id) {
                ... on BlogPage {
                    paginatedAuthors(page: $page, perPage: $perPage) {
                        items {
                            role
                            person {
                                name
                                job
                            }
                        }
                        pagination {
                            total
                            count
                            perPage
                            currentPage
                            prevPage
                            nextPage
                            totalPages
                        }
                    }
                }
            }
        }
        """

        executed = self.client.execute(
            query,
            variables={"id": self.blog_page.id, "page": page, "perPage": per_page},
        )

        authors = executed["data"]["page"]["paginatedAuthors"]["items"]
        pagination = executed["data"]["page"]["paginatedAuthors"]["pagination"]
        self.assertEqual(len(authors), 5)
        for author in authors:
            self.assertTrue(isinstance(author["role"], str))
            self.assertTrue(isinstance(author["person"]["name"], str))
            self.assertTrue(isinstance(author["person"]["job"], str))
        self.assertTrue(isinstance(pagination["total"], int))
        self.assertTrue(isinstance(pagination["count"], int))
        self.assertTrue(isinstance(pagination["perPage"], int))
        self.assertTrue(isinstance(pagination["currentPage"], int))
        self.assertTrue(pagination["prevPage"] is None)
        self.assertTrue(isinstance(pagination["nextPage"], int))
        self.assertTrue(isinstance(pagination["totalPages"], int))
        self.assertEqual(pagination["total"], 8)
        self.assertEqual(pagination["count"], 5)
        self.assertEqual(pagination["perPage"], per_page)
        self.assertEqual(pagination["currentPage"], page)
        self.assertEqual(pagination["prevPage"], None)
        self.assertEqual(pagination["nextPage"], 2)
        self.assertEqual(pagination["totalPages"], 2)

        page = 2
        executed = self.client.execute(
            query,
            variables={"id": self.blog_page.id, "page": page, "perPage": per_page},
        )

        authors = executed["data"]["page"]["paginatedAuthors"]["items"]
        pagination = executed["data"]["page"]["paginatedAuthors"]["pagination"]
        self.assertEqual(len(authors), 3)
        for author in authors:
            self.assertTrue(isinstance(author["role"], str))
            self.assertTrue(isinstance(author["person"]["name"], str))
            self.assertTrue(isinstance(author["person"]["job"], str))
        self.assertTrue(isinstance(pagination["total"], int))
        self.assertTrue(isinstance(pagination["count"], int))
        self.assertTrue(isinstance(pagination["perPage"], int))
        self.assertTrue(isinstance(pagination["currentPage"], int))
        self.assertTrue(isinstance(pagination["prevPage"], int))
        self.assertTrue(pagination["nextPage"] is None)
        self.assertTrue(isinstance(pagination["totalPages"], int))
        self.assertEqual(pagination["total"], 8)
        self.assertEqual(pagination["count"], 3)
        self.assertEqual(pagination["perPage"], per_page)
        self.assertEqual(pagination["currentPage"], page)
        self.assertEqual(pagination["prevPage"], 1)
        self.assertEqual(pagination["nextPage"], None)
        self.assertEqual(pagination["totalPages"], 2)

    def test_structvalue_block(self):
        block_type = "TextAndButtonsBlock"
        query_blocks = self.get_blocks_from_body(
            block_type,
            block_query="""
                buttons {
                    ... on ButtonBlock {
                        buttonText
                        buttonLink
                    }
               }
            """,
        )

        # Check HTML is string
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                buttons = query_blocks[0]["buttons"]
                self.assertEqual(buttons[0]["buttonText"], "btn")
                self.assertEqual(buttons[0]["buttonLink"], "https://www.graphql.com/")

    def test_nested_structvalue_block(self):
        block_type = "TextAndButtonsBlock"
        query_blocks = self.get_blocks_from_body(
            block_type,
            block_query="""
                mainbutton {
                    ... on ButtonBlock {
                        buttonText
                        buttonLink
                    }
               }
            """,
        )

        # Check HTML is string
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                button = query_blocks[0]["mainbutton"]
                self.assertEqual(button["buttonText"], "Take me to the source")
                self.assertEqual(button["buttonLink"], "https://wagtail.io/")

    def test_nested_structvalue_block_id(self):
        block_type = "CarouselBlock"
        query_blocks = self.get_blocks_from_body(
            block_type,
            block_query="""
                blocks {
                    ...on ImageChooserBlock {
                        id
                    }
                }
            """,
        )

        blocks = query_blocks[0]["blocks"]

        # Check that the id returned matches the original block's ID
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                for i, image_block in enumerate(block.value):
                    self.assertEqual(blocks[i]["id"], image_block.id)

    def test_block_with_name(self):
        block_type = "BlockWithName"
        block_query = "name"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                result = query_blocks[0][block_query]
                self.assertEqual("Test Name", result)

    def test_empty_list_in_structblock(self):
        another_blog_post = BlogPageFactory(
            body=[("text_and_buttons", {"buttons": self.empty_buttons_list})],
            parent=self.home,
        )
        block_type = "TextAndButtonsBlock"
        block_query = """
        buttons {
            ... on ButtonBlock {
                buttonText
                buttonLink
            }
        }
        """
        query_blocks = self.get_blocks_from_body(
            block_type, block_query=block_query, page_id=another_blog_post.id
        )
        self.assertEqual(
            query_blocks, [{"blockType": "TextAndButtonsBlock", "buttons": []}]
        )

    def test_singular_blog_page_query(self):
        query = """
        {
            firstPost {
                id
            }
        }
        """

        # add a new blog post
        another_post = BlogPageFactory()
        factory = RequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()
        results = self.client.execute(query, context_value=request)

        self.assertNotIn("errors", results)
        self.assertTrue("firstPost" in results["data"])
        self.assertEqual(int(results["data"]["firstPost"]["id"]), self.blog_page.id)

        query = """
        {
            firstPost(order: "-id") {
                id
            }
        }
        """
        results = self.client.execute(query, context_value=request)

        self.assertTrue("firstPost" in results["data"])
        self.assertEqual(int(results["data"]["firstPost"]["id"]), another_post.id)

    def test_blog_page_tags(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    tags {
                        id
                        name
                    }
                }
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.blog_page.id})

        tags = executed["data"]["page"]["tags"]
        self.assertEqual(len(tags), 3)
        for idx, tag in enumerate(tags, start=1):
            self.assertTrue(isinstance(tag["name"], str))
            self.assertEqual(tag["name"], f"Tag {idx}")

    def test_graphqlstring_property_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "simpleString"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                result = query_blocks[0][block_query]
                self.assertEqual("A simple string property.", result)

    def test_graphqlstring_method_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "simpleStringMethod"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Ensure TextWithCallableBlock.simple_string_method not called.
                result = query_blocks[0][block_query]

                # Ensure TextWithCallableBlock.get_simple_string_method called.
                self.assertIsInstance(result, str)
                self.assertIn("text-with-callable", result)

    def test_graphqlint_property_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "simpleInt"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                result = query_blocks[0][block_query]
                self.assertEqual(5, result)

    def test_graphqlint_method_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "simpleIntMethod"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Ensure TextWithCallableBlock.simple_int_method not called.
                result = query_blocks[0][block_query]

                # Ensure TextWithCallableBlock.get_simple_int_method called.
                self.assertIsInstance(result, int)

    def test_graphqlfloat_property_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "simpleFloat"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                result = query_blocks[0][block_query]
                self.assertEqual(0.1, result)

    def test_graphqlfloat_method_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "simpleFloatMethod"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Ensure TextWithCallableBlock.simple_float_method not called.
                result = query_blocks[0][block_query]

                # Ensure TextWithCallableBlock.get_simple_float_method called.
                self.assertIsInstance(result, float)

    def test_graphqlboolean_property_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "simpleBoolean"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                result = query_blocks[0][block_query]
                self.assertEqual(1, result)

    def test_graphqlboolean_method_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "simpleBooleanMethod"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Ensure TextWithCallableBlock.simple_boolean_method not called.
                result = query_blocks[0][block_query]

                # Ensure TextWithCallableBlock.get_simple_boolean_method called.
                self.assertIsInstance(result, bool)

    def test_graphqlfield_property_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "fieldProperty"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                result = query_blocks[0][block_query]
                self.assertEqual("A field property.", result)

    def test_graphqlfield_method_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query = "fieldMethod"
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Ensure TextWithCallableBlock.field_method not called.
                result = query_blocks[0][block_query]

                # Ensure TextWithCallableBlock.get_field_method called.
                self.assertIn("text-with-callable", result)

    def test_streamfield_callable_resolver_using_graphqlinfo(self):
        site_two = wagtail_factories.SiteFactory(
            hostname="grapple.localhost", site_name="Grapple test site", port=80
        )

        slug = self.blog_page.slug
        site_two_post = BlogPageFactory(
            parent=site_two.root_page,
            title="post on grapple test site",
            slug=slug,  # same slug as self.blog_page which is on the default site
        )

        the_post = BlogPageFactory(
            parent=site_two.root_page,
            title="the blog post on grapple test site",
            slug="the-blog-post",
            body=[
                (
                    "text_with_callable",
                    TextWithCallableBlockFactory(page=site_two_post),
                ),
                (
                    "text_with_callable",
                    TextWithCallableBlockFactory(page=self.blog_page),
                ),
            ],
        )

        query = """
        query($hostname: String, $id: ID) {
            site(hostname: $hostname) {
                page(id: $id) {
                    title
                    ... on BlogPage {
                        body {
                            ...on TextWithCallableBlock {
                                linkUrl
                            }
                        }
                    }
                }
            }
        }
        """

        query_variables = {
            "hostname": site_two.hostname,
            "id": the_post.id,
        }
        results = self.client.execute(query, variables=query_variables)

        data = results["data"]["site"]["page"]
        self.assertEqual(data["title"], the_post.title)
        self.assertEqual(
            data["body"][0]["linkUrl"], f"http://grapple.localhost/{slug}/"
        )
        # expeting the full url since we are not passing the request context
        self.assertEqual(data["body"][1]["linkUrl"], f"http://localhost/{slug}/")

        # now pass on the request context
        request = RequestFactory().request(server_name=site_two.hostname)
        results = self.client.execute(
            query, variables=query_variables, context_value=request
        )

        data = results["data"]["site"]["page"]
        self.assertEqual(data["title"], the_post.title)
        self.assertEqual(
            data["body"][0]["linkUrl"], f"http://grapple.localhost/{slug}/"
        )
        self.assertEqual(data["body"][1]["linkUrl"], f"/{slug}/")

    def test_graphqlfield_method_with_extra_arg_in_structblock(self):
        block_type = "TextWithCallableBlock"
        block_query_field = "fieldMethodWithExtraArg"
        extra_arg = "hello"
        block_query = f'{block_query_field}(extraArg: "{extra_arg}")'
        query_blocks = self.get_blocks_from_body(block_type, block_query=block_query)

        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Ensure TextWithCallableBlock.field_method not called.
                result = query_blocks[0][block_query_field]

                # Ensure TextWithCallableBlock.get_field_method_with_extra_arg called with right argument.
                self.assertIn(extra_arg, result)

    def test_custom_property(self):
        query = """
        query($id: ID) {
            page(id: $id) {
                ... on BlogPage {
                    customProperty
                }
            }
        }
        """
        executed = self.client.execute(query, variables={"id": self.blog_page.id})

        # Check custom property.
        self.assertEqual(
            json.loads(executed["data"]["page"]["customProperty"]),
            self.blog_page.custom_property,
        )

    def test_stream_block_description(self):
        """
        A StreamBlock with a graphql_description field in its Metaclass should have that value exposed
        """

        query = """
            query {
              __type(name: "ImageGalleryImages") {
                description
              }
            }
        """
        response = self.client.execute(query)
        self.assertEqual(
            ImageGalleryImages._meta_class.graphql_description,
            response["data"]["__type"]["description"],
        )

    def test_stream_block_no_description(self):
        query = """
            query {
              __type(name: "CarouselBlock") {
                description
              }
            }
        """
        response = self.client.execute(query)
        self.assertIsNone(response["data"]["__type"]["description"])

    def test_struct_block_description(self):
        """
        A StructBlock with a graphql_description field in its Metaclass should have that value exposed
        """

        query = """
            query {
              __type(name: "ImageGalleryBlock") {
                description
              }
            }
        """
        response = self.client.execute(query)
        self.assertEqual(
            ImageGalleryBlock._meta_class.graphql_description,
            response["data"]["__type"]["description"],
        )

    def test_struct_block_no_description(self):
        query = """
            query {
              __type(name: "ButtonBlock") {
                description
              }
            }
        """
        response = self.client.execute(query)
        self.assertIsNone(response["data"]["__type"]["description"])

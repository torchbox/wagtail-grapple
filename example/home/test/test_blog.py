import datetime
import decimal

import wagtail_factories
from django.conf import settings
from wagtail.core.blocks import BoundBlock, StreamValue, StructValue
from wagtail.core.rich_text import RichText

from example.tests.test_grapple import BaseGrappleTest
from home.blocks import ImageGalleryImage, ImageGalleryImages
from home.factories import BlogPageFactory, ImageGalleryImageFactory


class BlogTest(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        self.blog_page = BlogPageFactory(
            body=[
                ("heading", "Test heading 1"),
                ("paragraph", RichText("This is a paragraph.")),
                ("heading", "Test heading 2"),
                ("image", wagtail_factories.ImageFactory()),
                ("decimal", decimal.Decimal(1.2)),
                ("date", datetime.date.today()),
                ("datetime", datetime.datetime.now()),
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
            ]
        )

    def test_blog_page(self):
        query = """
        {
            page(id:%s) {
                ... on BlogPage {
                    title
                }
            }
        }
        """ % (
            self.blog_page.id
        )
        executed = self.client.execute(query)

        # Check title.
        self.assertEquals(executed["data"]["page"]["title"], self.blog_page.title)

    def get_blocks_from_body(self, block_type, block_query="rawValue"):
        query = """
        {
            page(id:%s) {
                ... on BlogPage {
                    body {
                        blockType
                        ... on %s {
                            %s
                        }
                    }
                }
            }
        }
        """ % (
            self.blog_page.id,
            block_type,
            block_query,
        )
        executed = self.client.execute(query)

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
                self.assertEquals(query_blocks[count]["rawValue"], block.value)
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEquals(len(query_blocks), count)

    def test_blog_body_richtextblock(self):
        block_type = "RichTextBlock"
        query_blocks = self.get_blocks_from_body(block_type)

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEquals(
                    query_blocks[count]["rawValue"], block.value.__html__()
                )
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEquals(len(query_blocks), count)

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
                self.assertEquals(
                    query_blocks[count]["image"]["id"], str(block.value.id)
                )
                self.assertEquals(
                    query_blocks[count]["image"]["src"],
                    settings.BASE_URL + block.value.file.url,
                )
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEquals(len(query_blocks), count)

    def test_blog_body_decimalblock(self):
        block_type = "DecimalBlock"
        query_blocks = self.get_blocks_from_body(block_type)

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEquals(query_blocks[count]["rawValue"], str(block.value))
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEquals(len(query_blocks), count)

    def test_blog_body_dateblock(self):
        block_type = "DateBlock"
        query_blocks = self.get_blocks_from_body(block_type)

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEquals(query_blocks[count]["rawValue"], str(block.value))
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEquals(len(query_blocks), count)

    def test_blog_body_datetimeblock(self):
        block_type = "DateTimeBlock"
        date_format_string = "%Y-%m-%d %H:%M:%S"
        query_blocks = self.get_blocks_from_body(
            block_type, block_query=f'value(format: "{date_format_string}")'
        )

        # Check output.
        count = 0
        for block in self.blog_page.body:
            if type(block.block).__name__ == block_type:
                # Test the values
                self.assertEquals(
                    query_blocks[count]["value"],
                    block.value.strftime(date_format_string),
                )
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEquals(len(query_blocks), count)

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
                self.assertEquals(
                    query_blocks[count]["title"], str(block.value["title"])
                )
                for key, image in enumerate(query_blocks[count]["images"]):
                    self.assertEquals(
                        image["image"]["id"],
                        str(block.value["images"][key].value["image"].id),
                    )
                    self.assertEquals(
                        image["image"]["src"],
                        settings.BASE_URL
                        + str(block.value["images"][key].value["image"].file.url),
                    )
                # Increment the count
                count += 1
        # Check that we test all blocks that were returned.
        self.assertEquals(len(query_blocks), count)

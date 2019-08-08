from wagtail.core import blocks


from wagtail.images.blocks import ImageChooserBlock


class ImageGalleryImage(blocks.StructBlock):
    image = ImageChooserBlock()


class ImageGalleryImages(blocks.StreamBlock):
    image = ImageGalleryImage()

    class Meta:
        min_num = 2
        max_num = 15


class ImageGalleryBlock(blocks.StructBlock):
    title = blocks.CharBlock(classname="full title")
    images = ImageGalleryImages()


class StreamFieldBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(classname="full title")
    paraagraph = blocks.RichTextBlock()
    image = ImageChooserBlock()
    decimal = blocks.DecimalBlock()
    date = blocks.DateBlock()
    datetime = blocks.DateTimeBlock()
    gallery = ImageGalleryBlock()

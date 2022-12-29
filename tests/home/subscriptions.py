import asyncio

import graphene


class Subscription(graphene.ObjectType):
    hello = graphene.String()

    async def resolve_hello(root, info):
        await asyncio.sleep(3.0)
        yield "hello world!"

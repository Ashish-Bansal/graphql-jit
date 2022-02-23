import graphene
import timeit


class User(object):
    def __init__(self, id):
        self.id = id
        self.name = "Ashish"


users = [User(index) for index in range(0, 100000)]


class UserQuery(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String(required=True)


class Query(graphene.ObjectType):
    users = graphene.List(UserQuery)
    user = graphene.Field(UserQuery, index=graphene.Int())

    def resolve_users(root, info):
        return users

    def resolve_user(root, info, index):
        return users[index]


schema = graphene.Schema(query=Query)
query = '{ user(index: 1) { id name } }'
variables = {"index": 1}

def default_backend():
    print("Without fast backend")
    print(schema.execute(query, variables=variables))
    print(timeit.timeit(lambda: schema.execute(query, variables=variables), number=1))


def fast_backend():
    from graphql_jit.backend import GraphQLFastBackend

    backend = GraphQLFastBackend()
    document = backend.document_from_string(schema, query)
    print("With fast backend")
    print(timeit.timeit(lambda: print(document.execute(variables=variables)), number=1))


def main():
    default_backend()
    fast_backend()


if __name__ == '__main__':
    main()

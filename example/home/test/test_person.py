from home.factories import PersonFactory

from example.tests.test_grapple import BaseGrappleTest


class PersonTest(BaseGrappleTest):
    def setUp(self):
        super().setUp()
        # Create person
        self.person1 = PersonFactory(name="Chuck Norris", job="Roundhouse Kicker")
        self.person2 = PersonFactory(name="Rory", job="Dog")

    def validate_person(self, person):
        # Check all the fields
        self.assertTrue(isinstance(person["id"], str))
        self.assertTrue(isinstance(person["name"], str))
        self.assertTrue(isinstance(person["job"], str))

    def test_people_query(self):
        query = """
        {
            people {
                id
                name
                job
            }
        }
        """
        executed = self.client.execute(query)
        person = executed["data"]["people"][0]

        # Check all the fields
        self.validate_person(person)

    def test_people_paginated_query(self):
        query = """
        {
           peoplePaginated {
                items {
                    id
                    name
                    job
                }
                pagination {
                    total
                    count
                }
            }
        }
        """
        executed = self.client.execute(query)
        person = executed["data"]["peoplePaginated"]["items"][0]

        # Check all the fields
        self.validate_person(person)

    def test_people_query_fields(self):
        query = """
        query($job: String) {
            people(job: $job) {
                id
                name
                job
            }
        }
        """
        executed = self.client.execute(query, variables={"job": self.person1.job})
        person = executed["data"]["people"][0]

        # Check all the fields
        self.validate_person(person)
        self.assertEqual(person["name"], self.person1.name)

    def test_people_paginated_query_fields(self):
        query = """
        query($job: String) {
           peoplePaginated(job: $job) {
                items {
                    id
                    name
                    job
                }
                pagination {
                    total
                    count
                }
            }
        }
        """
        executed = self.client.execute(query, variables={"job": self.person2.job})
        person = executed["data"]["peoplePaginated"]["items"][0]

        # Check all the fields
        self.validate_person(person)
        self.assertEqual(person["name"], self.person2.name)

    def test_person_single_query(self):
        query = """
        query($name: String) {
            person(name: $name) {
                id
                name
                job
            }
        }
        """
        executed = self.client.execute(query, variables={"name": self.person1.name})
        person = executed["data"]["person"]

        # Check all the fields
        self.validate_person(person)
        self.assertEqual(person["name"], self.person1.name)

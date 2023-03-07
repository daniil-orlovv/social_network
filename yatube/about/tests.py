from http import HTTPStatus

from django.test import TestCase, Client


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_pages_used_templates(self):
        static_pages = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }

        for address, template in static_pages.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_static_pages_url_exists_at_desired_location(self):
        static_pages = (
            '/about/author/',
            '/about/tech/'
        )

        for url in static_pages:
            with self.subTest(address=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

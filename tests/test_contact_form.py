from django.test import TestCase, Client
from django.urls import reverse
from core.models import ContactMessage

class ContactFormTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_contact_form_submission_saves_to_db(self):
        data = {
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': '123 Street',
            'message': 'Hello from the test suite!'
        }
        response = self.client.post(reverse('contact_submit'), data)
        self.assertEqual(response.status_code, 302)  # redirected to home
        self.assertEqual(ContactMessage.objects.count(), 1)
        message = ContactMessage.objects.first()
        self.assertEqual(message.email, data['email'])
        self.assertEqual(message.phone, data['phone'])
        self.assertEqual(message.address, data['address'])
        self.assertEqual(message.message, data['message'])
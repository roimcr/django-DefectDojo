import sys
import datetime
sys.path.append('..')
from dojo.models import Product
from dojo.models import Engagement
from dojo.models import Test_Type
from dojo.models import Test
from dojo.models import Finding
from dojo.models import Finding_Template
from dojo.finding import views
from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from custom_field.models import CustomFieldValue, CustomField
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponseRedirect
from django.http import HttpResponse

class FindingTemplateTestUtil:

    def __init__(self):
        pass

    @staticmethod
    def create_user(is_staff):
        user_count = User.objects.count()
        user = User()
        user.is_staff = is_staff
        user.username = 'TestUser' + str(user_count)
        user.save()
        return user

    @staticmethod
    def create_get_request(user, path):
        rf = RequestFactory()
        get_request = rf.get(path)
        get_request.user = user
        get_request.session = dict()

        return get_request

    @staticmethod
    def create_post_request(user, path, data):
        rf = RequestFactory()
        post_request = rf.post(path, data=data)
        post_request.user = user
        post_request.session = dict()
        messages = FallbackStorage(post_request)
        setattr(post_request, '_messages', messages)

        return post_request


class TestApplyFindingTemplate(TestCase):

    apply_template_url = 'finding/1/1/apply_template_to_finding'

    def setUp(self):
        p = Product()
        p.Name = 'Test Product'
        p.Description = 'Product for Testing Apply Template functionality'
        p.save()

        e = Engagement()
        e.product = p
        e.target_start = datetime.datetime.now().date()
        e.target_end = e.target_start + datetime.timedelta(days=5)
        e.save()

        tt = Test_Type()
        tt.name = 'Temporary Test'
        tt.save()

        t = Test()
        t.engagement = e
        t.test_type = tt
        t.target_start = datetime.datetime.now().date()
        t.target_end = t.target_start + datetime.timedelta(days=5)
        t.save()

        user = FindingTemplateTestUtil.create_user(True)

        f = Finding()
        f.title = 'Finding for Testing Apply Template functionality'
        f.severity = 'High'
        f.description = 'Finding for Testing Apply Template Functionality'
        f.test = t
        f.reporter = user
        f.last_reviewed = datetime.datetime.now()
        f.last_reviewed_by = user
        f.save()

        tmp = Finding_Template()
        tmp.title = 'Finding Template for Testing Apply Template functionality'
        tmp.cwe = 0
        tmp.severity = 'Low'
        tmp.description = 'Finding Template for Testing Apply Template functionality'
        tmp.mitigation = 'Finding Template Mitigation'
        tmp.impact = 'Finding Template Impact'
        tmp.save()

    def make_request(self, user_is_staff, finding_id, template_id, data=None):
        user = FindingTemplateTestUtil.create_user(user_is_staff)

        if data:
            request = FindingTemplateTestUtil.create_post_request(user, self.apply_template_url, data)
        else:
            request = FindingTemplateTestUtil.create_get_request(user, self.apply_template_url)

        v = views.apply_template_to_finding(request, finding_id, template_id)

        return v

    def test_nothing(self):
        self.assertTrue(True==True)

    def test_apply_template_to_finding_with_data_does_not_display_error_success(self):
        result = self.make_request(True, 1, 1,
                                   {'title':'Finding for Testing Apply Template functionality',
                                    'cwe':'89',
                                    'severity':'High',
                                    'description':'Finding for Testing Apply Template Functionality',
                                    'mitigation':'template mitigation',
                                    'impact':'template impact'})
        self.assertNotContains(result, 'There appears to be errors on the form', 302)

    def test_apply_template_to_finding_with_data_returns_to_view_success(self):
        result = self.make_request(True, 1, 1,
                                   {'title':'Finding for Testing Apply Template functionality',
                                    'cwe':'89',
                                    'severity':'High',
                                    'description':'Finding for Testing Apply Template Functionality',
                                    'mitigation':'template mitigation',
                                    'impact':'template impact'})
        self.assertIsNotNone(result)
        self.assertEqual(302, result.status_code)
        self.assertEqual('/finding/1', result.url)

    def test_apply_template_to_finding_with_data_saves_success(self):
        test_title = 'Finding for Testing Apply Template functionality'
        test_cwe = 89
        test_severity = 'High'
        test_description = 'Finding for Testing Apply Template Functionality'
        test_mitigation = 'template mitigation'
        test_impact = 'template impact'

        result = self.make_request(True, 1, 1,
                                   {'title': test_title,
                                    'cwe': test_cwe,
                                    'severity': test_severity,
                                    'description': test_description,
                                    'mitigation': test_mitigation,
                                    'impact': test_impact})

        f = Finding.objects.get(id=1)
        self.assertEqual(test_title, f.title)
        self.assertEqual(test_cwe, f.cwe)
        self.assertEqual(test_severity, f.severity)
        self.assertEqual(test_description, f.description)
        self.assertEqual(test_mitigation, f.mitigation)
        self.assertEquals(test_impact, f.impact)

    def test_unauthorized_apply_template_to_finding_fails(self):
        result = self.make_request(False, 1, 1,
                                   {'title':'Finding for Testing Apply Template functionality',
                                    'cwe':'89',
                                    'severity':'High',
                                    'description':'Finding for Testing Apply Template Functionality',
                                    'mitigation':'template mitigation',
                                    'impact':'template impact'}
                                   )
        self.assertEqual(302, result.status_code)
        self.assertIn('login', result.url)

    def test_apply_template_to_finding_with_illegal_finding_fails(self):
        with self.assertRaises(Exception):
            result = self.make_request(True, None, 1)

    def test_apply_template_to_finding_with_illegal_template_fails(self):
        with self.assertRaises(Exception):
            result = self.make_request(True, 1, None)

    def test_apply_template_to_finding_with_no_data_returns_view_success(self):
        result = self.make_request(True, 1, 1, None)
        self.assertIsNotNone(result)
        self.assertEqual(302, result.status_code)
        self.assertEqual('/finding/1', result.url)

    def test_apply_template_to_finding_without_required_field_displays_field_title_success(self):
        result = self.make_request(True, 1, 1,
                                   {'title':'',
                                    'cwe':'89',
                                    'severity':'High',
                                    'description':'Finding for Testing Apply Template Functionality',
                                    'mitigation':'template mitigation',
                                    'impact':'template impact'})
        self.assertContains(result, 'The title is required.')

    def test_apply_template_to_finding_without_required_field_displays_error_success(self):
        result = self.make_request(True, 1, 1,
                                   {'title':'',
                                    'cwe':'89',
                                    'severity':'High',
                                    'description':'Finding for Testing Apply Template Functionality',
                                    'mitigation':'template mitigation',
                                    'impact':'template impact'})
        self.assertContains(result, 'There appears to be errors on the form')


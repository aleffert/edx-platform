"""
Tests for the Badges app models.
"""
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.test import TestCase
from django.test.utils import override_settings
from mock import patch
from nose.plugins.attrib import attr
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory

from badges.models import CourseCompleteImageConfiguration, validate_badge_image, BadgeClass, BadgeAssertion
from badges.tests.factories import BadgeClassFactory, BadgeAssertionFactory, RandomBadgeClassFactory
from certificates.tests.test_models import TEST_DATA_ROOT
from student.tests.factories import UserFactory


class ImageFetchingMixin(object):
    """
    Provides the ability to grab a badge image from the test data root.
    """
    def get_image(self, name):
        """
        Get one of the test images from the test data directory.
        """
        return ImageFile(open(TEST_DATA_ROOT / 'badges' / name + '.png'))


@attr('shard_1')
class BadgeImageConfigurationTest(TestCase, ImageFetchingMixin):
    """
    Test the validation features of BadgeImageConfiguration.
    """

    def test_no_double_default(self):
        """
        Verify that creating two configurations as default is not permitted.
        """
        CourseCompleteImageConfiguration(mode='test', icon=self.get_image('good'), default=True).save()
        self.assertRaises(
            ValidationError,
            CourseCompleteImageConfiguration(mode='test2', icon=self.get_image('good'), default=True).full_clean
        )

    def test_runs_validator(self):
        """
        Verify that the image validator is triggered when cleaning the model.
        """
        self.assertRaises(
            ValidationError,
            CourseCompleteImageConfiguration(mode='test2', icon=self.get_image('unbalanced')).full_clean
        )


class DummyBackend(object):
    """
    Dummy badge backend, used for testing.
    """


class BadgeClassTest(TestCase, ImageFetchingMixin):
    """
    Test BadgeClass functionality
    """
    # Need full path to make sure class names line up.
    @override_settings(BADGING_BACKEND='lms.djangoapps.badges.tests.test_models.DummyBackend')
    def test_backend(self):
        """
        Verify the BadgeClass fetches the backend properly.
        """
        self.assertIsInstance(BadgeClass().backend, DummyBackend)

    def test_get_badge_class_preexisting(self):
        """
        Verify fetching a badge first grabs existing badges.
        """
        premade_badge_class = BadgeClassFactory.create()
        # Ignore additional parameters. This class already exists.
        badge_class = BadgeClass.get_badge_class(
            slug='test_slug', issuing_component='test_component', description='Attempted override',
            criteria='test', display_name='Testola', image_file_handle=self.get_image('good')
        )
        # These defaults are set on the factory.
        self.assertEqual(badge_class.criteria, 'https://example.com/syllabus')
        self.assertEqual(badge_class.display_name, 'Test Badge')
        self.assertEqual(badge_class.description, "Yay! It's a test badge.")
        # File name won't always be the same.
        self.assertEqual(badge_class.image.path, premade_badge_class.image.path)

    def test_get_badge_class_create(self):
        """
        Verify fetching a badge creates it if it doesn't yet exist.
        """
        badge_class = BadgeClass.get_badge_class(
            slug='new_slug', issuing_component='new_component', description='This is a test',
            criteria='https://example.com/test_criteria', display_name='Super Badge',
            image_file_handle=self.get_image('good')
        )
        # This should have been saved before being passed back.
        self.assertTrue(badge_class.id)
        self.assertEqual(badge_class.slug, 'new_slug')
        self.assertEqual(badge_class.issuing_component, 'new_component')
        self.assertEqual(badge_class.description, 'This is a test')
        self.assertEqual(badge_class.criteria, 'https://example.com/test_criteria')
        self.assertEqual(badge_class.display_name, 'Super Badge')
        self.assertEqual(badge_class.image.name.rsplit('/', 1)[-1], 'good.png')

    def test_get_badge_class_nocreate(self):
        """
        Test returns None if the badge class does not exist.
        """
        badge_class = BadgeClass.get_badge_class(
            slug='new_slug', issuing_component='new_component', description=None,
            criteria=None, display_name=None,
            image_file_handle=None, create=False
        )
        self.assertIsNone(badge_class)
        # Run this twice to verify there wasn't a background creation of the badge.
        badge_class = BadgeClass.get_badge_class(
            slug='new_slug', issuing_component='new_component', description=None,
            criteria=None, display_name=None,
            image_file_handle=None, create=False
        )
        self.assertIsNone(badge_class)

    def test_get_badge_class_validate(self):
        """
        Verify handing a broken image to get_badge_class raises a validation error upon creation.
        """
        self.assertRaises(
            ValidationError,
            BadgeClass.get_badge_class,
            slug='new_slug', issuing_component='new_component', description='This is a test',
            criteria='https://example.com/test_criteria', display_name='Super Badge',
            image_file_handle=self.get_image('unbalanced')
        )

    def test_get_for_user(self):
        """
        Make sure we can get an assertion for a user if there is one.
        """
        user = UserFactory.create()
        badge_class = BadgeClassFactory.create()
        self.assertIsNone(badge_class.get_for_user(user))
        assertion = BadgeAssertionFactory.create(badge_class=badge_class, user=user)
        self.assertEqual(badge_class.get_for_user(user), assertion)

    @override_settings(BADGING_BACKEND='lms.djangoapps.badges.backends.badgr.BadgrBackend', BADGR_API_TOKEN='test')
    @patch('lms.djangoapps.badges.backends.badgr.BadgrBackend.award')
    def test_award(self, mock_award):
        """
        Verify that the award command calls the award function on the backend with the right parameters.
        """
        user = UserFactory.create()
        badge_class = BadgeClassFactory.create()
        badge_class.award(user, evidence_url='http://example.com/evidence')
        self.assertTrue(mock_award.called)
        mock_award.assert_called_with(badge_class, user, evidence_url='http://example.com/evidence')

    def test_runs_validator(self):
        """
        Verify that the image validator is triggered when cleaning the model.
        """
        self.assertRaises(
            ValidationError,
            BadgeClass(
                slug='test', issuing_component='test2', criteria='test3',
                description='test4', image=self.get_image('unbalanced')
            ).full_clean
        )


class BadgeAssertionTest(ModuleStoreTestCase):
    """
    Tests for the BadgeAssertion model
    """
    def test_assertions_for_user(self):
        """
        Verify that grabbing all assertions for a user behaves as expected.
        """
        user = UserFactory()
        assertions = [BadgeAssertionFactory.create(user=user) for _i in range(3)]
        course = CourseFactory.create()
        course_key = course.location.course_key
        course_badges = [RandomBadgeClassFactory(course_id=course_key) for _i in range(3)]
        course_assertions = [
            BadgeAssertionFactory.create(user=user, badge_class=badge_class) for badge_class in course_badges
        ]
        assertions.extend(course_assertions)
        self.assertItemsEqual(BadgeAssertion.assertions_for_user(user), assertions)
        self.assertItemsEqual(BadgeAssertion.assertions_for_user(user, course_id=course_key), course_assertions)


class ValidBadgeImageTest(TestCase, ImageFetchingMixin):
    """
    Tests the badge image field validator.
    """
    def test_good_image(self):
        """
        Verify that saving a valid badge image is no problem.
        """
        validate_badge_image(self.get_image('good'))

    def test_unbalanced_image(self):
        """
        Verify that setting an image with an uneven width and height raises an error.
        """
        unbalanced = ImageFile(self.get_image('unbalanced'))
        self.assertRaises(ValidationError, validate_badge_image, unbalanced)

    def test_large_image(self):
        """
        Verify that setting an image that is too big raises an error.
        """
        large = self.get_image('large')
        self.assertRaises(ValidationError, validate_badge_image, large)
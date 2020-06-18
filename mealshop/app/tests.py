import datetime
import pytz
from unittest.mock import patch
from unittest.mock import MagicMock
from django.test import TestCase
from django.utils.timezone import now, localtime, timedelta
from django.test.utils import setup_test_environment
from django.test import Client
from django.urls import reverse
from .models import (Menu, MenuOption, MenuOptionCustomization, Order,
                     User, OrderCustomization, Profile)
from . import views
from . import services


class MenuViewTests(TestCase):

    fixtures = ['mealshop.json']

    def setUp(self):
        self.client = Client()

    @patch(views.__name__+'._get_datetime_today_range')
    def test_time_before_restricted(self, mock):
        '''
        Create a menu with date now and mock today_max
        that has to be greater that now() to get a menu response
        '''
        # GIVEN: a valid datetime to view a menu
        mock.return_value = self._mock_return_valid_date_menu()
        menu = Menu(pub_date=now())
        menu.save()

        # AND: user is authenticated
        self.client.login(username='joaco', password='1234corner')

        # WHEN: a user navigates to choose_menu url
        response = self.client.get(reverse('mealshop:choose_menu',
                                           args=[menu.id]))

        # THEN:
        self.assertIn('menu', response.context)

    @patch(views.__name__+'._get_datetime_today_range')
    def test_view_order_created_by_employee(self, mock):
        # GIVEN: order with a menu and menu option
        mock.return_value = self._mock_return_valid_date_menu()
        menu = Menu.objects.filter().latest('pub_date')
        user = User.objects.get(username='joaco')
        menu_option = MenuOption(name='Testing menu option')
        menu_option.save()
        order = Order.objects.create(user=user, menu=menu,
                                     purchased_date=now(),
                                     menu_option=menu_option)
        order.save()

        # AND: user is loggend in
        self.client.login(username='joaco', password='1234corner')

        # WHEN: user gets mealshop:choose_menu url
        response = self.client.get(reverse('mealshop:choose_menu',
                                           args=[menu.id]))

        # THEN: order is added to response context
        self.assertIn('order', response.context)

    @patch(views.__name__+'._get_datetime_today_range')
    def test_orders_of_others_employees(self, mock):
        # GIVEN: order with a menu and menu option
        mock.return_value = self._mock_return_valid_date_menu()
        menu = Menu.objects.filter().latest('pub_date')
        user = User.objects.get(username='duce')
        menu_option = MenuOption(name='Testing menu option')
        menu_option.save()
        order = Order.objects.create(user=user, menu=menu,
                                     purchased_date=now(),
                                     menu_option=menu_option)
        order.save()

        # AND: user is loggend in
        self.client.login(username='joaco', password='1234corner')

        # WHEN: user gets mealshop:choose_menu url
        response = self.client.get(reverse('mealshop:choose_menu',
                                           args=[menu.id]))

        # THEN: order is added to response context
        self.assertIsNot('order', response.context)

    def _mock_return_valid_date_menu(self):
        menu = Menu(pub_date=now())
        menu.save()
        t_max = now() + timedelta(days=1)
        return ((t_max, t_max))


class OrdersTest(TestCase):
    fixtures = ['mealshop.json']

    def setUp(self):
        self.client = Client()

    def test_view_orders_for_logged_in_user(self):
        # GIVEN: nora authenticated
        self.client.login(username='nora', password='1234corner')

        # WHEN: nora navigates to view orders
        response = self.client.get(reverse('mealshop:view_orders'))

        # THEN: get a 200 response with order object in context
        self.assertEqual(response.status_code, 200)
        self.assertIn('orders', response.context)

    def test_view_orders_for_anonymous(self):
        # WHEN: anonymous user navigates to view orders
        response = self.client.get(reverse('mealshop:view_orders'))

        # THEN: user is redirected with 302 status code
        self.assertEqual(response.status_code, 302)

    def test_add_orders_authenticated_user(self):
        # GIVEN: a employee with menu and menu options
        menu = Menu.objects.filter().latest('pub_date')
        user = User.objects.get(username='joaco')
        menu_option = MenuOption(name='Testing menú option')
        menu_option.save()

        # AND: user is authenticated
        self.client.login(username='joaco', password='1234corner')

        # WHEN: adding a order
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(user=user, menu=menu)
        response = self.client.post('/{}/add_order'.format(menu.id),
                                    {'menu_option_id': menu_option.id})

        # THEN: a new order is created
        order = Order.objects.get(user=user, menu=menu)
        self.assertIsNotNone(order)
        self.assertEqual(response.status_code, 302)

    def test_add_orders_anonymous_user(self):
        # GIVEN: a employee with a menu and menu options
        menu = Menu.objects.filter().latest('pub_date')
        user = User.objects.get(username='joaco')
        menu_option = MenuOption(name='Testing menú option')
        menu_option.save()

        # WHEN: adding a order
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(user=user, menu=menu)
        response = self.client.post('/{}/add_order'.format(menu.id),
                                    {'menu_option_id': menu_option.id})

        # THEN: a new order is not created
        with self.assertRaises(Order.DoesNotExist):
            order = Order.objects.get(user=user, menu=menu)
            self.assertIsNone(order)
        self.assertEqual(response.status_code, 302)


class OrderCustomizationTest(TestCase):
    fixtures = ['mealshop.json']

    def setUp(self):
        self.client = Client()

    def test_add_updates_orders_customization(self):
        # GIVEN:  menu option with an order to add customizations
        menu = Menu.objects.get(pk=1)
        menu_option = MenuOption.objects.filter(menu=menu).first()
        user = User.objects.get(username='joaco')
        order = Order(user=user, menu_option=menu_option,
                      menu=menu)
        order.save()

        # AND: user is authenticated
        self.client.login(username='joaco', password='1234corner')

        # WHEN: adding an customization to an order
        customization = MenuOptionCustomization.objects.filter(
            menu_option=menu_option).first()
        menu_option_custom = 'menu_option_customization_{}'.\
            format(customization.id)

        response = self.client.post(
            '/{}/add_order_customizations'.format(order.id),
            {menu_option_custom: customization.id})

        # THEN: customizations are set to the order
        query_id = set(map(lambda x: x.menu_option_custom.id,
                           OrderCustomization.objects.filter(order=order)))

        self.assertEqual(query_id, {customization.id})

        # WHEN: Updating same order change customization
        customization_update = MenuOptionCustomization.objects.filter(
            menu_option=menu_option).last()
        self.assertNotEqual(customization, customization_update)
        menu_option_custom = 'menu_option_customization_{}'.\
            format(customization_update.id)
        response = self.client.post(
            '/{}/add_order_customizations'.format(order.id),
            {menu_option_custom: customization_update.id})

        # THEN: customizations should be updated
        query_id = set(map(lambda x: x.menu_option_custom.id,
                           OrderCustomization.objects.filter(order=order)))

        self.assertEqual(query_id, {customization_update.id})


class ServiceTest(TestCase):
    fixtures = ['mealshop.json']

    def setUp(self):
        self.client = Client()

    @patch(services.__name__+'.WebClient.api_call')
    def test_send_reminder_all_users(self, mock):
        # GIVEN: a menu
        menu = Menu.objects.latest('pub_date')
        profiles = Profile.objects.exclude(slack_user__exact='')

        # WHEN: _send a reminder
        services._send_reminder(menu)

        # THEN: call slack API
        self.assertEqual(mock.call_count, len(profiles))

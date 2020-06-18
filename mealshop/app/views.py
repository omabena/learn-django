import uuid
import logging
import pytz
import datetime
from django.utils.formats import get_format
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.urls import reverse
from django.utils.timezone import localtime, now, get_current_timezone
from django.contrib.auth.decorators import permission_required, login_required
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date
from .models import (
    Menu, MenuOption, MenuOptionCustomization, User, Order, OrderCustomization
)
from .forms import MenuForm
from .services import create_reminder_async, _send_reminder


@require_http_methods(['GET'])
def index(request):
    """
    Landing view for all users, no authentication is required

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponse object
    """
    today_min, today_max = _get_datetime_today_range()
    try:
        menu = (Menu.objects
                .filter(pub_date__gte=today_min, pub_date__lte=today_max)
                .latest('pub_date'))
    except Menu.DoesNotExist:
        return render(request, 'app/index.html')

    return render(request, 'app/index.html', {'menu': menu})


@require_http_methods(['GET'])
@permission_required('app.add_menu', login_url='/')
def create_menu(request):
    """
    View to create a new daily menu by Persona Nora

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponse object

    Context {
        menu_options: all created menu options
        pub_date: current time
    }
    """
    menu_options = MenuOption.objects.all()
    pub_date = now()
    return render(request, 'app/create_menu.html', {
        'menu_options': menu_options,
        'pub_date': pub_date
    })


@permission_required('app.add_menu', login_url='/')
@require_http_methods(['POST'])
def add_menu(request):
    """
     Creates a new daily menu

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponse object with template as content
    """
    str_date = request.POST.get('pub_date')
    tz = get_current_timezone()
    dt = tz.localize(datetime.datetime.strptime(str_date + " 01:00:00",
                                                '%m/%d/%Y  %H:%M:%S'))
    menu = Menu(pub_date=dt)
    menu.save()
    request.user.menu.add(menu)

    try:
        for option in MenuOption.objects.all():
            if request.POST.get('menu_option_' + str(option.id)):
                menu.menu_options.add(option)
    except KeyError:
        return create_menu(request)
    else:
        menu.save()
        return HttpResponseRedirect(reverse('mealshop:daily_menu'))


@permission_required('app.add_menu', login_url='/')
@require_http_methods(['GET'])
def create_reminder(request, menu_id):
    """
    Sends a async slack reminder to all employees of current menu

    Parameters:
    request (HttpReqest): object that contains metadata about the request
    menu_id (int): id to reference menu to send a reminder

    Returns
    HttpResponse object with template as content
    """
    menu = Menu.objects.get(pk=menu_id)
    create_reminder_async(menu)
    return HttpResponseRedirect(reverse('mealshop:daily_menu'))


@permission_required('app.add_menu', login_url='/')
@require_http_methods(['GET'])
def daily_menu(request):
    """
    Render current daily menu created, with a link to create a new
    one if still does not exists

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponse object with template as content
    """
    try:
        today_min, today_max = _get_datetime_today_range()
        menu = (Menu.objects
                .filter(pub_date__gte=today_min, pub_date__lte=today_max)
                .latest('pub_date'))
    except Menu.DoesNotExist:
        return render(request, 'app/daily_menu.html')
    return render(request, 'app/daily_menu.html', {'menu': menu})


@permission_required('app.change_menu', login_url='/')
@require_http_methods(['GET'])
def update_daily_menu(request, menu_id):
    """
    Upate daily menu

    Parameters:
    request (HttpReqest): object that contains metadata about the request
    menu_id (int): id to reference menu to be updated

    Returns:
    Return a HttpResponse object with template as content
    """
    menu = get_object_or_404(Menu, pk=menu_id)
    form = MenuForm()
    return render(request, 'app/menu_update.html', {
        'menu': menu, 'form': form
    })


@permission_required('app.add_menuoption', login_url='/')
@require_http_methods(['GET'])
def menu_options(request):
    """
    List menu options to create a menu (this are dishes)

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponse object with template as content
    Context {
        menu_options: (list-> MenuOption)
    }
    """
    menu_options = MenuOption.objects.all()
    return render(request, 'app/list_menu_options.html',
                  {'menu_options': menu_options})


@permission_required('app.add_menuoption', login_url='/')
@require_http_methods(['POST'])
def add_menu_option(request):
    """
    Updates a menu option object

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponseRedirect to list of menu options
    """
    try:
        menu_option = MenuOption(name=request.POST['menu_option_name'])
    except (KeyError):
        return render(request, 'app/menu_option.html', {
            'error_message': 'Name cannot be empty'
        })
    else:
        menu_option.save()
        return HttpResponseRedirect(reverse('mealshop:menu_options'))


@permission_required('app.change_menuoption', login_url='/')
@require_http_methods(['GET'])
def menu_option(request, menu_option_id):
    """
    A menu option listing is associated customizations

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponse object with template as content
    Context {
        menu_option: (MenuOption)
    }
    """
    try:
        menu_option = MenuOption.objects.get(pk=menu_option_id)
    except MenuOption.DoesNotExist:
        raise Http404('Opción de menú no existente')
    return render(request, 'app/menu_option.html',
                  {'menu_option': menu_option})


@permission_required('app.change_menuoption', login_url='/')
@require_http_methods(['POST'])
def add_customization(request, menu_option_id):
    """
    Add customizations to a menu option

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponseRedirect to menu option view
    """
    menu_option = get_object_or_404(MenuOption, pk=menu_option_id)
    try:
        customization = MenuOptionCustomization(
            name=request.POST['menu_option_customization'],
            menu_option=menu_option)
    except (KeyError, MenuOptionCustomization.DoesNotExist):
        return render(request, 'app/menu_option.html', {
            'menu_option': menu_option,
            'error_message': "Name cannot be empty",
        })
    else:
        customization.save()
        return HttpResponseRedirect(reverse(
            'mealshop:menu_option', args=(menu_option_id,)))


@require_http_methods(['GET'])
def menu(request, uuid):
    today_min, today_max = _get_datetime_today_range()
    context = {}
    if now() <= today_max:
        try:
            menu = Menu.objects.filter(uuid=uuid, pub_date__lte=today_max)\
                .first()
            context['menu'] = menu
        except Menu.DoesNotExist:
            return HttpResponseRedirect(reverse(
                'mealshop:index'))

    return render(request, 'app/menu.html', context)


@login_required(login_url='/login/')
@require_http_methods(['GET'])
def choose_menu(request, menu_id):
    """
     View of daily menu for employees to order,
    only a menu will be displayed that corresponds do the date of today
    is available to make orders until 11:00 am with timezone set on settings.py

    If a user already created an order, it will be displayed below
    with the option to update.

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponse object with template as content
    Context {
        menu: (Menu),
        order: (Order) If it exsists
    }
    """
    context = {}
    today_min, today_max = _get_datetime_today_range()
    if now() <= today_max:
        try:
            menu = Menu.objects.get(pk=menu_id, pub_date__lte=today_max)
            context = {'menu': menu}
            if request.user.is_authenticated:
                order = Order.objects.filter(user=request.user, menu=menu)
                if order.exists():
                    order = order.first()
                    customizations = order.ordercustomization_set.all()
                    context['order'] = order
                    context['customization_user'] = customizations\
                        .values_list('menu_option_custom__id', flat=True)

        except Menu.DoesNotExist:
            return HttpResponseRedirect(reverse(
                'mealshop:index'))

    return render(request, 'app/choose_menu.html', context)


@login_required(login_url='/login/')
@require_http_methods(['POST'])
def add_order(request, menu_id):
    """
    Create a new order from daily menu it has a link to add customizations
    to the selected menu option

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponseRedirect to choose_menu view template
    """
    try:
        menu_option_id = request.POST['menu_option_id']
        menu = get_object_or_404(Menu, pk=menu_id)
        menu_option = get_object_or_404(MenuOption, pk=menu_option_id)
    except Exception:
        return HttpResponseRedirect(reverse(
            'mealshop:choose_menu', args=[menu_id]))
    else:
        obj, created = Order.objects.update_or_create(
            user=request.user, menu=menu, defaults={
                'user': request.user, 'menu': menu,
                'purchased_date': now(), 'menu_option': menu_option
            }
        )
        OrderCustomization.objects.filter(order=obj).delete()
        return HttpResponseRedirect(reverse(
            'mealshop:choose_menu', args=[menu_id]))


@login_required(login_url='/login/')
@require_http_methods(['POST'])
def add_order_customizations(request, order_id):
    """
    Set order customizations for the menu option selected

    Parameters:
    request (HttpReqest): object that contains metadata about the request
    order_id (int): order to set menu customizations

    Returns:
    Return a HttpResponseRedirect to choose_menu view template
    """
    try:
        order = get_object_or_404(Order, pk=order_id)
        menu_option = order.menu_option
        customizations = menu_option.menuoptioncustomization_set.all()

        # TODO: find a better way to update Manty-to-one relationship
        # consider not deleting but updating status of field if it is created
        OrderCustomization.objects.filter(order=order).delete()
        for customization in customizations:
            if request.POST.get('menu_option_customization_'
                                + str(customization.id)):
                OrderCustomization.objects.update_or_create(
                    order=order, menu_option_custom=customization,
                    defaults={'order': order,
                              'menu_option_custom': customization}
                )
    except KeyError:
        return HttpResponseRedirect(reverse(
            'mealshop:choose_menu', args=[order.menu.id]))
    else:
        return HttpResponseRedirect(reverse(
            'mealshop:choose_menu', args=[order.menu.id]))


@require_http_methods(['GET'])
@permission_required('app.view_order', login_url='/')
def view_orders(request):
    """
    View a list of orders taken for a day

    Parameters:
    request (HttpReqest): object that contains metadata about the request

    Returns:
    Return a HttpResponseRedirect to view_orders view template
    """
    today_min, today_max = _get_datetime_today_range(max_hour=23,
                                                     max_second=59)
    orders = Order.objects.filter(purchased_date__lte=today_max,
                                  purchased_date__gte=today_min)

    return render(request, 'app/view_orders.html', {
        'orders': orders
    })


# TODO: remove this burn out setting of hours
def _get_datetime_today_range(max_hour=11, max_second=0):
    assert max_hour >= 0 and max_hour < 24, \
        'Max hour has to be between [0,24)'
    assert max_second >= 0 and max_second < 60,\
        'Max seconds has to be between [0,60)'
    tz = pytz.timezone("America/Santiago")
    today_min = datetime.datetime.combine(localtime(now()).date().today(),
                                          datetime.time(hour=0, tzinfo=tz))
    today_max = datetime.datetime.combine(localtime(now()).date().today(),
                                          datetime.time(hour=max_hour,
                                                        second=max_second,
                                                        tzinfo=tz))

    return (today_min, today_max)

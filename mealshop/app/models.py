import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now


class MenuOption(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField()

    def __str__(self):
        return self.name


class MenuOptionCustomization(models.Model):
    name = models.CharField(max_length=250)
    menu_option = models.ForeignKey(MenuOption, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Menu(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='menu', null=True)
    menu_options = models.ManyToManyField(MenuOption)
    pub_date = models.DateTimeField('date published', default=now)
    slack_url = models.CharField(max_length=300)

    def __str__(self):
        return str(self.pub_date)


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='order', null=True)
    menu_option = models.ForeignKey(
        MenuOption, on_delete=models.CASCADE, default=None)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, null=False)
    purchased_date = models.DateTimeField(
        'purchased date', default=now)

    def __str__(self):
        return 'user {} option {} on date {}'.format(
            self.user, self.menu_option, self.purchased_date)


class OrderCustomization(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_option_custom = models.ForeignKey(
        MenuOptionCustomization, on_delete=models.CASCADE)

    def __str__(self):
        return 'order {} \nmenu_option_custom {}'.format(
            self.order, self.menu_option_custom)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    slack_user = models.CharField(max_length=100, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

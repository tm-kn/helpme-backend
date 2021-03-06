from decimal import Decimal
import math

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


DEFAULT_RADIUS_MILES = getattr(settings, 'HELPME_DEFAULT_RADIUS_MILES',
                               float(5))
EQUATORIAL_CIRCUMFERENCE = 24901
POLAR_CIRCUMFERENCE = 24860
ONE_MILE_LATITUDE_DEGREES = float(360) / float(EQUATORIAL_CIRCUMFERENCE)
ONE_MILE_LONGITUDE_DEGREES = float(360) / float(POLAR_CIRCUMFERENCE)


class HelpRequestQuerySet(models.query.QuerySet):
    def location(self, latitude, longitude, radius=DEFAULT_RADIUS_MILES):
        """
        This method takes latitude, longitude and radius in miles as
        parameters and shows help requests which are in the given radius.
        """
        # Convert values to floating point type
        latitude = float(latitude)
        longitude = float(longitude)
        radius = float(radius)

        # Calculate boundaries of supplied coordinates according to radius
        # supplied in miles
        max_val = {
            'north': latitude + (ONE_MILE_LATITUDE_DEGREES * radius),
            'south': latitude - (ONE_MILE_LATITUDE_DEGREES * radius),
            'east': longitude + (ONE_MILE_LONGITUDE_DEGREES * radius),
            'west': longitude - (ONE_MILE_LONGITUDE_DEGREES * radius)
        }

        return self.filter(
            location_lat__range=(max_val['south'], max_val['north']),
            location_lon__range=(max_val['west'], max_val['east'])
        )

    def not_closed(self):
        """
        Returns only requests which hasn't been closed yet
        """
        return self.filter(is_closed=False)

    def only_future_meetings(self):
        """
        Returns only help requests which meeting time is in the future
        """
        return self.filter(meeting_datetime__gt=timezone.now())


class HelpRequestManager(models.Manager):
    def get_queryset(self):
        return HelpRequestQuerySet(self.model, using=self._db)

    def location(self, latitude, longitude, radius=DEFAULT_RADIUS_MILES):
        return self.get_queryset().location(latitude, longitude, radius)

    def not_closed(self):
        return self.get_queryset().not_closed()

    def only_future_meetings(self):
        return self.get_queryset().only_future_meetings()


class HelpRequest(models.Model):
    title = models.CharField(_('title'), max_length=50)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='help_requests',
                               verbose_name=_('author'))
    datetime = models.DateTimeField(_('datetime'), default=timezone.now)
    meeting_datetime = models.DateTimeField(_('meeting datetime'))
    location_name = models.CharField(_('meeting location name'), max_length=50)
    location_lat = models.FloatField(_('meeting location latitude'), blank=True, null=True)
    location_lon = models.FloatField(_('meeting location longitude'), blank=True, null=True)
    content = models.TextField(_('content'))
    is_closed = models.BooleanField(_('is closed'), default=False)
    objects = HelpRequestManager()

    class Meta:
        verbose_name = _('help request')
        verbose_name_plural = _('help requests')
        ordering = ['meeting_datetime']

    def __str__(self):
        return self.title

    @property
    def author_name(self):
        return self.author.get_full_name()

    def get_distance(self, user_longitude, user_latitude):
        # Convert given coordinated to floating point
        user_longitude = float(user_longitude)
        user_latitude = float(user_latitude)

        # Use the formula for distance between two points
        x = math.pow(user_longitude - self.longitude, 2)
        y = math.pow(user_latitude - self.latitude, 2)
        return math.sqrt(x + y)


class HelpRequestReply(models.Model):
    help_request = models.ForeignKey('HelpRequest', related_name='help_request_replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='help_request_replies')
    datetime = models.DateTimeField(_('datetime'), default=timezone.now)
    content = models.TextField(_('content'))

    class Meta:
        verbose_name = _('help request reply')
        verbose_name_plural = _('help request replies')
        ordering = ['datetime']

    def __str__(self):
        return "Reply to %s by %s" % (self.help_request, self.author)

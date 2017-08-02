from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from .couchdb_helpers import delete_user, generate_db_name


class MobileUser(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return 'MobileUser: ' + self.email


class DeviceDB(models.Model):
    mobileuser = models.ForeignKey(MobileUser,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   related_name='devices')
    device_id = models.TextField(unique=True)

    # used to log the sync execution
    last_synced_date = models.DateTimeField(null=True)
    last_synced_seq = models.TextField(null=True, default=0)
    last_synced_log_message = models.TextField(null=True)

    @property
    def db_name(self):
        ''' Returns the device's db name. '''
        return generate_db_name(self.device_id)


@receiver(pre_delete, sender=MobileUser)
def mobile_user_pre_delete(sender, instance, *args, **kwargs):
    ''' When a Mobile User is deleted, delete the CouchDB users to revoke sync access '''
    devices = instance.devices.all()
    for device in devices:
        delete_user(device.device_id)

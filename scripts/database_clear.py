import hotspot.models as m

m.ClusterModel.objects.all().delete()
m.HotspotModel.objects.all().delete()
m.HotspotScoreModel.objects.all().delete()

from django.contrib.auth.models import UserManager, User

User.objects.all().delete()
User.objects.create_superuser(username="root", email="todo@test.com", password="Master123")
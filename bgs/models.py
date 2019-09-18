from django.db import models
from time import time

class Game(models.Model):
    # should we get them all from the geek
    name = models.CharField(max_length=200)

class Wishlist(models.Model):
    #game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)
    priority = models.IntegerField()

class Shop(models.Model):
    name = models.CharField(max_length=200, unique=True)
    scrapetime = models.IntegerField(default=int(time()))

class GameProduct(models.Model):
    name = models.CharField(max_length=200, null=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    stock = models.CharField(max_length=10, default="Unknown")
    price = models.CharField(max_length=20, default="Unknown")
    class Meta:
        unique_together = ('name', 'shop')
# end Database stuff


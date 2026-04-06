from django.contrib.auth.models import User, AbstractUser
from django.db import models
class NewsModel(models.Model):
    title = models.CharField(max_length=100)
    text = models.TextField()
    image = models.ImageField(upload_to='images/')
    pub_date = models.DateTimeField('date published')
    def __str__(self):
        return self.title
    class Meta:
        verbose_name = 'news'
        verbose_name_plural = 'news'




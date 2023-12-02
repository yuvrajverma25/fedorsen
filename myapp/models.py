from django.contrib.auth.models import User 
from django.db import models 
from django.utils import timezone 
 
class AccessCode(models.Model): 
    user = models.OneToOneField(User,on_delete=models.CASCADE) 
    code = models.CharField(max_length=10,unique=True,primary_key=True) 
    expiration_date = models.DateTimeField(default=timezone.now()+ timezone.timedelta(days=30)) 
     
    def is_valid(self): 
        return self.expiration_date >= timezone.now()
    
    def __str__(self):
        return f'user_{self.code}'
    

class AllowedCode(models.Model): 
    code = models.CharField(max_length=10,unique=True,primary_key=True) 

    def __str__(self):
        return self.code

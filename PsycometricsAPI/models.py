from django.db import models

class HR(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10)
    company = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Test(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)

    def __str__(self):
        return f"Test {self.id}"

class Candidate(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    hr = models.ForeignKey(HR, on_delete=models.CASCADE, related_name='candidates')
    code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Result(models.Model):
    duration = models.PositiveIntegerField()
    conflicts = models.FloatField()
    tolerance = models.FloatField()
    savic = models.FloatField()
    health = models.FloatField()
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='results')
    hr = models.ForeignKey(HR, on_delete=models.CASCADE, related_name='results')
    candidate = models.ForeignKey('Candidate', on_delete=models.CASCADE, related_name='results')

    def __str__(self):
        return f"Result {self.id} for Test {self.test.id}"

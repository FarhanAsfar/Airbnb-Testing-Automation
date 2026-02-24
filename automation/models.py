from django.db import models


class TestResult(models.Model):
    testCase = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    passed = models.BooleanField(default=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.testCase}"


class Listing(models.Model):
    title = models.CharField(max_length=500)
    price = models.CharField(max_length=100, blank=True)
    img_url = models.TextField(blank=True)
    search_url = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    checkin = models.CharField(max_length=50, blank=True)
    checkout = models.CharField(max_length=50, blank=True)
    guests = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} | {self.price} | {self.location}"
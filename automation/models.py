from django.db import models

# Create your models here.

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
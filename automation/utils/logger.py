from automation.models import TestResult


def log_result(testCase: str, url: str, passed: bool, comment: str) -> TestResult:
    """Save a test result to the database and print to console."""
    result = TestResult.objects.create(
        testCase=testCase,
        url=url,
        passed=passed,
        comment=comment,
    )
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} | {testCase} | {comment}")
    return result